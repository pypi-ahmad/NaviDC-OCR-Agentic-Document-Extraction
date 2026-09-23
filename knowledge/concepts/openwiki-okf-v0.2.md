---
type: Reference
title: OpenWiki and OKF v0.2
description: Summarizes the normative OKF v0.2 bundle conventions, OpenWiki's documented OKF support, and version differences in the supplied introductory references.
tags: [okf, openwiki, documentation, provenance]
status: draft
generated:
  by: okf-skill/0.2
  at: 2026-09-23T15:08:10+00:00
sources:
  - id: okf-v02-spec
    resource: https://github.com/GoogleCloudPlatform/open-knowledge-format/blob/main/SPEC.md
    title: Open Knowledge Format v0.2 specification
  - id: openwiki-okf-support
    resource: https://www.langchain.com/blog/openwiki-0-2-adds-okf-support
    title: OpenWiki 0.2 OKF support announcement
  - id: google-cloud-introduction
    resource: https://cloud.google.com/blog/products/data-analytics/how-the-open-knowledge-format-can-improve-data-sharing/
    title: Google Cloud introduction to OKF
  - id: okf-homepage
    resource: https://okf.md/
    title: OKF homepage
  - id: supplied-catalog-spec-copy
    resource: https://github.com/GoogleCloudPlatform/knowledge-catalog/blob/main/okf/SPEC.md
    title: Supplied knowledge-catalog copy of the OKF specification
  - id: repository-openwiki-index
    resource: ../../openwiki/index.md
    title: This repository's generated OpenWiki index
---

# OpenWiki and OKF v0.2

Open Knowledge Format (OKF) is a portable convention for knowledge bundles built from Markdown files with YAML frontmatter. OKF v0.2 keeps the format minimal while adding standard fields for provenance, trust, lifecycle, and attested computations. It does not prescribe a fixed taxonomy or require a runtime or SDK.[^okf-v02-spec]

## Bundle structure

An OKF bundle is a directory tree of UTF-8 Markdown files. Each non-reserved Markdown file is a concept with YAML frontmatter and a free-form body. The `type` field is required; other fields and type names are producer-defined. Directory hierarchy organizes concepts, while ordinary Markdown links express relationships between them.[^okf-v02-spec]

`index.md` is a reserved directory listing and `log.md` is a reserved update history. The bundle-root index may declare `okf_version: "0.2"`. A consumer should use the current specification for these names and rules.[^okf-v02-spec]

## Provenance and trust

`sources` records the materials a concept derives from. A source `id` can be used as a stable footnote key. `generated` records who or what produced the current content and when; `verified` records a separate confirmation event. `status` can be `draft`, `stable`, or `deprecated`, and `stale_after` can record a freshness boundary. Trust tiers derived from `verified` are advisory signals, not access control or cryptographic proof.[^okf-v02-spec]

This bundle's concept is marked `draft` and has no `verified` field. Its sources and generation time describe provenance; they do not certify that a person reviewed it.[^okf-v02-spec]

## OpenWiki support

LangChain's OpenWiki 0.2 announcement describes generated and updated codebase wikis using OKF-style frontmatter, directory indexes, and update logs. It presents that structure as a way to make large wikis easier to browse and search across compatible tools.[^openwiki-okf-support]

The article calls the update file `logs.md` in one section, while the normative OKF v0.2 specification reserves singular `log.md`. Follow the specification for bundle conformance rather than treating an implementation article as the standard.[^openwiki-okf-support][^okf-v02-spec]

This repository's generated wiki is under [`openwiki/`](../../openwiki/index.md); its root index declares `okf_version: "0.2"`. The separate `knowledge/` directory is this repository's portable OKF bundle. The two collections serve different roles: OpenWiki documents the current codebase, while this bundle stores reusable governed knowledge about OKF and its integration.[^repository-openwiki-index]

## Version notes for the supplied references

The Google Cloud introduction describes the initial OKF v0.1 format. The `okf.md` homepage also identifies itself as v0.1, so both are useful for background but are not the normative source for v0.2 details.[^google-cloud-introduction][^okf-homepage]

The current v0.2 specification supersedes the legacy `timestamp` field with `generated.at` and moves provenance citations from a body `# Citations` list into frontmatter `sources`. Use the dedicated `open-knowledge-format` specification for current requirements. The supplied `knowledge-catalog/okf/SPEC.md` URL is retained here as a reference copy, not as the version authority.[^okf-v02-spec][^supplied-catalog-spec-copy]

## Sources

[^okf-v02-spec]: [Open Knowledge Format v0.2 specification](https://github.com/GoogleCloudPlatform/open-knowledge-format/blob/main/SPEC.md).
[^openwiki-okf-support]: [OpenWiki 0.2 adds OKF support](https://www.langchain.com/blog/openwiki-0-2-adds-okf-support), LangChain, 2026-07-16.
[^google-cloud-introduction]: [Introducing the Open Knowledge Format](https://cloud.google.com/blog/products/data-analytics/how-the-open-knowledge-format-can-improve-data-sharing/), Google Cloud, 2026-06-12.
[^okf-homepage]: [OKF homepage](https://okf.md/), which labels itself OKF v0.1.
[^supplied-catalog-spec-copy]: [Supplied specification copy in `knowledge-catalog/okf`](https://github.com/GoogleCloudPlatform/knowledge-catalog/blob/main/okf/SPEC.md).
[^repository-openwiki-index]: [Generated OpenWiki index](../../openwiki/index.md).
