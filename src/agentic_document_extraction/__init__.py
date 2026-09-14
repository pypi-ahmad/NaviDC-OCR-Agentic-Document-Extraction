"""Local agentic document extraction application.

This package boundary is intentionally empty: it must not import NaviOCR,
Torch, or vLLM, so the lightweight Streamlit environment never depends on
the isolated GPU worker's libraries (see provider.py and worker.py). Start
reading at documents.py.
"""
