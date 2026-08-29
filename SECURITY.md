# Security guidance

## Intended deployment

This project is a trusted, single-user local application. It is not hardened for public internet or hostile multi-tenant deployment.

- The NaviDC worker binds to `127.0.0.1`.
- Streamlit exposure follows `.streamlit/config.toml` and command-line overrides.
- Uploaded files are untrusted input even in local use.

Do not expose ports 8741 or 8742 to an untrusted network without adding authentication, authorization, request limits, TLS termination, and isolation appropriate to that environment.

## Protected data

The application does not require an API credential for the public local model. Do not add tokens or credentials to source files, Markdown examples, logs, or committed environment files.

Uploaded documents may contain sensitive information:

- Process only documents you are authorized to handle.
- Download required artifacts before ending the session.
- Store downloaded bundles according to the document's data classification.
- Clear browser downloads and temporary operator files when required by policy.

## Implemented controls

- Input extension, size, readability, and PDF page count validation
- Rejection of password-protected PDFs
- 100 MB application and worker request limits
- Selected-page processing instead of unconditional full-document transfer
- Request-scoped worker temporary directories
- Escaping of OCR text in generated HTML
- Restrictive Content Security Policy in standalone HTML
- Sanitized user-facing provider errors
- Serialized GPU extraction requests
- No synthetic OCR output when the provider fails

## Out of scope

The current application does not provide:

- User authentication or authorization
- Malware scanning or content disarm and reconstruction
- Audit logging or retention policies
- Encryption-at-rest management for downloaded artifacts
- Rate limiting or quotas
- Process or container isolation between documents
- A supported public network API

## Reporting a vulnerability

Do not include sensitive documents, credentials, or exploit payloads in a public issue. Report the affected file, impact, reproduction conditions, and a redacted proof of concept through the repository owner's private communication channel.
