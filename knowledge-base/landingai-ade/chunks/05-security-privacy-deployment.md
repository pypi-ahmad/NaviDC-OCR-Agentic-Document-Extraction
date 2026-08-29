---
title: ADE security, privacy, retention, and deployment
source_urls: [https://docs.landing.ai/ade/ade-security, https://docs.landing.ai/ade/zdr, https://docs.landing.ai/ade/ade-eu]
research_date: 2026-08-29
---

# ADE security, privacy, retention, and deployment

Vendor docs list GDPR, SOC 2 Type II, and HIPAA-related controls. Enterprise adds SSO and IP allowlists. Verify scope and dates through the Trust Center.

ZDR is Team/Enterprise. LandingAI states documents and intermediates are deleted after processing, results on delivery, and ZDR data is not used for model training or improvement. Unfetched v2 async results remain 24 to 48 hours; fetched results delete on fetch. HIPAA use requires ZDR and a signed BAA.

Hosted regions: AWS Ohio `us-east-2` and Ireland `eu-west-1`. EU keys are region-specific. Enterprise lists VPC/on-prem deployment. Customers own retention and subprocessor controls in their VPC.
