"""HTTP boundary and lifecycle manager for the isolated NaviDC-OCR worker.

This is the only module the Streamlit app uses to reach OCR. It must not
import NaviOCR, Torch, or vLLM (see ADR-001 in docs/adr): those live only in
the worker's separate WSL Python environment, reached over HTTP. Provider
errors from here are always safe, bounded, user-facing strings - never raw
exception text. Open worker.py next to see the other side of this boundary.
"""

from __future__ import annotations

import io
import json
import os
import subprocess
import time
import zipfile
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Protocol

import httpx

DEFAULT_PROVIDER_URL = "http://127.0.0.1:8742"
DEFAULT_RUNTIME_DIR = "/home/ahmad/projects/NaviDC-OCR"
MODEL_NAME = "StarDoc-AI/NaviDC-OCR"


class ProviderError(RuntimeError):
    """A safe, user-facing OCR provider failure."""


@dataclass(frozen=True, slots=True)
class ProviderOutput:
    """Normalized artifacts returned by an OCR provider.

    Attributes:
        markdown: Layout-aware Markdown bytes.
        annotated_pdf: Provider-generated annotated PDF bytes.
        middle_json: Provider layout representation used for HTML overlays.
        images: Extracted image assets keyed by base filename.
        provider: Human-readable provider name.
        model: Provider model identifier.
    """

    markdown: bytes
    annotated_pdf: bytes
    middle_json: dict[str, object]
    images: dict[str, bytes]
    provider: str = "NaviDC-OCR"
    model: str = MODEL_NAME


class OcrProvider(Protocol):
    """Application-facing contract implemented by OCR providers."""

    def health(self) -> dict[str, object]:
        """Return provider health without raising for unavailability."""
        ...

    def extract(
        self,
        pdf_bytes: bytes,
        source_pages: list[int],
        layout_mode: str,
        render_dpi: int = 300,
    ) -> ProviderOutput:
        """Extract selected PDF pages and return normalized artifacts."""
        ...


class NaviDcProvider:
    """HTTP adapter and lifecycle manager for the local NaviDC-OCR worker.

    Args:
        base_url: Optional worker URL. When omitted, the adapter reads
            ``NAVIDC_PROVIDER_URL`` and then uses the local default.
    """

    def __init__(self, base_url: str | None = None) -> None:
        """Initialize the adapter without starting or loading the worker."""
        self.base_url = (base_url or os.getenv("NAVIDC_PROVIDER_URL", DEFAULT_PROVIDER_URL)).rstrip(
            "/"
        )
        self._process: subprocess.Popen[bytes] | None = None

    def health(self) -> dict[str, object]:
        """Return worker health or a normalized unavailable state.

        Returns:
            Provider health JSON, or ``{"status": "unavailable"}`` when the
            request fails or the response is invalid.
        """
        try:
            response = httpx.get(f"{self.base_url}/health", timeout=2)
            response.raise_for_status()
            payload = response.json()
            return payload if isinstance(payload, dict) else {"status": "unavailable"}
        except (httpx.HTTPError, ValueError):
            # Deliberately never raises: callers (ensure_running, the UI) poll
            # this cheaply before the worker exists, so any transport or JSON
            # failure is folded into the same "unavailable" state as a normal
            # not-running worker rather than an exception to handle.
            return {"status": "unavailable"}

    def ensure_running(self, timeout_seconds: float = 45) -> dict[str, object]:
        """Reuse a healthy worker or start one and wait for readiness.

        Args:
            timeout_seconds: Maximum time to wait for the health endpoint.

        Returns:
            Ready worker health metadata.

        Raises:
            ProviderError: If the worker exits or does not become ready.
            OSError: If the configured runtime or WSL executable cannot start.
        """
        health = self.health()
        if health.get("status") == "ready":
            return health
        # Reuse an already-running process handle across calls; only spawn a
        # new worker if this adapter has never started one or the previous
        # one has exited.
        if self._process is None or self._process.poll() is not None:
            self._process = _start_worker()
        deadline = time.monotonic() + timeout_seconds
        while time.monotonic() < deadline:
            if self._process.poll() is not None:
                break
            health = self.health()
            if health.get("status") == "ready":
                return health
            time.sleep(0.5)
        raise ProviderError(
            "NaviDC-OCR could not start. Confirm the WSL runtime is installed, then see README.md."
        )

    def extract(
        self,
        pdf_bytes: bytes,
        source_pages: list[int],
        layout_mode: str,
        render_dpi: int = 300,
    ) -> ProviderOutput:
        """Extract selected PDF pages through the local worker.

        Args:
            pdf_bytes: PDF containing only pages selected by the user.
            source_pages: Original one-based number for each submitted page.
            layout_mode: ``Detection`` or ``Segmentation``.

        Returns:
            Validated and normalized OCR artifacts.

        Raises:
            ProviderError: If startup, transport, extraction, or archive
                validation fails.
        """
        self.ensure_running()
        try:
            with httpx.Client(timeout=httpx.Timeout(1800, connect=10)) as client:
                response = client.post(
                    f"{self.base_url}/extract",
                    files={"document": ("document.pdf", pdf_bytes, "application/pdf")},
                    data={
                        "source_pages": json.dumps(source_pages),
                        "layout_mode": layout_mode,
                        "render_dpi": str(render_dpi),
                    },
                )
            if response.status_code != 200:
                raise ProviderError(_safe_provider_message(response))
            return _read_provider_archive(response.content)
        except httpx.TimeoutException as exc:
            # Network/timeout failures are remapped to safe, generic messages
            # here so the UI never surfaces a raw httpx exception, host, or path.
            raise ProviderError("NaviDC-OCR timed out while processing this document.") from exc
        except httpx.HTTPError as exc:
            raise ProviderError("The local NaviDC-OCR service became unavailable.") from exc


def _start_worker() -> subprocess.Popen[bytes]:
    runtime = os.getenv("NAVIDC_RUNTIME_DIR", DEFAULT_RUNTIME_DIR)
    source_dir = str(Path(__file__).resolve().parents[1])
    port = os.getenv("NAVIDC_PROVIDER_PORT", "8742")
    environment = os.environ.copy()
    if os.name == "nt":
        # Workaround: uvicorn runs inside WSL Ubuntu, but this repository is
        # checked out on the Windows filesystem. PYTHONPATH must be a path WSL
        # can resolve, so the Windows source_dir is translated with wslpath
        # before being used, not passed through as-is.
        windows_source = source_dir.replace("\\", "/")
        wsl_source = subprocess.run(
            ["wsl.exe", "-d", "Ubuntu-24.04", "--", "wslpath", "-a", windows_source],
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
        command = (
            f"cd {runtime!s} && PYTHONUNBUFFERED=1 PYTHONPATH={wsl_source!s} "
            ".venv/bin/python -m uvicorn "
            f"agentic_document_extraction.worker:app --host 127.0.0.1 --port {port}"
        )
        return subprocess.Popen(
            ["wsl.exe", "-d", "Ubuntu-24.04", "--", "bash", "-lc", command],
        )
    environment["PYTHONPATH"] = os.pathsep.join(
        filter(None, [source_dir, environment.get("PYTHONPATH")])
    )
    environment["PYTHONUNBUFFERED"] = "1"
    return subprocess.Popen(
        [
            f"{runtime}/.venv/bin/python",
            "-m",
            "uvicorn",
            "agentic_document_extraction.worker:app",
            "--host",
            "127.0.0.1",
            "--port",
            port,
        ],
        cwd=runtime,
        env=environment,
    )


def _safe_provider_message(response: httpx.Response) -> str:
    # The worker's error detail is untrusted-ish (it can echo NaviDC internals);
    # only a short string is passed through, and anything longer or malformed
    # falls back to a fixed generic message instead of being shown as-is.
    try:
        detail = response.json().get("detail")
        if isinstance(detail, str) and len(detail) <= 300:
            return detail
    except (ValueError, AttributeError):
        pass
    return "NaviDC-OCR could not extract this document. Try fewer pages or a clearer scan."


def _read_provider_archive(data: bytes) -> ProviderOutput:
    # Archive layout is the on-wire contract with worker._run_extraction:
    # result.md, annotated.pdf, middle.json, and an optional images/ folder.
    try:
        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            names = set(archive.namelist())
            required = {"result.md", "annotated.pdf", "middle.json"}
            if not required <= names:
                raise ProviderError("NaviDC-OCR returned an incomplete result.")
            images = {
                PurePosixPath(name).name: archive.read(name)
                for name in names
                if name.startswith("images/") and not name.endswith("/")
            }
            return ProviderOutput(
                markdown=archive.read("result.md"),
                annotated_pdf=archive.read("annotated.pdf"),
                middle_json=json.loads(archive.read("middle.json")),
                images=images,
            )
    except (zipfile.BadZipFile, json.JSONDecodeError, KeyError) as exc:
        raise ProviderError("NaviDC-OCR returned an unreadable result.") from exc
