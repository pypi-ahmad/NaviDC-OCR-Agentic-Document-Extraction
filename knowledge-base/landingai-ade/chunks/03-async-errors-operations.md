---
title: ADE asynchronous jobs, errors, and operations
source_urls: [https://docs.landing.ai/ade/ade-parse-async, https://docs.landing.ai/ade/ade-extract-async, https://github.com/landing-ai/ade-python]
research_date: 2026-08-29
---

# ADE asynchronous jobs, errors, and operations

Jobs support create, get, list, and polling; current SDK v2 adds `wait()`. States: `pending`, `processing`, `completed`, `failed`, `cancelled`. Large results may use a temporary output URL.

SDK retries connection errors and HTTP 408, 409, 429, and 5xx twice by default. Default timeout is eight minutes. Sync 504 cancels the workflow; retry starts new work. Parse can return HTTP 206 with failed pages.

No public webhook contract or first-party human-review queue was found. Use bounded polling, durable job IDs, review assignment, correction history, and explicit acceptance thresholds.
