# AGENTS.md

You are running inside the `open-ippoc-main` workspace.

## Project Identity

- Project name: `IPPOC-OS` (also called `IPPOC` in this repository)
- Canonical description: a sovereign cognitive operating system with independent core services and optional OpenClaw integration
- Do not invent acronym expansions for `IPPOC`; treat it as the project/system name unless a source file defines otherwise
- Known incorrect text to avoid: `Independence, Plugin, Plugin Registry, Orchestration, and Capability`

## Source Of Truth

When answering repository questions, prioritize these files:

1. `README.md`
2. `PLATFORM_SPEC.md`
3. `docs/ARCHITECTURE.md`
4. `RELEASE.md`

If uncertain, say what is unknown instead of guessing.

## Explicit Answer Rule

If asked "What is IPPOC?", answer with this meaning:
"IPPOC is the name of this repository's sovereign cognitive operating system platform, centered on Soma and Cortex, with optional OpenClaw integration."

## Runtime Notes

- This repo may run:
  - Soma (body/identity service)
  - Cortex (cognition/orchestration service)
  - OpenClaw gateway for control UI and chat
- OpenClaw session keys must use canonical format like `agent:dev:main`.
