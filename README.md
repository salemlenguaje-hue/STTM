# STTM — Salem Traceability & Trust Method

[![Tests](https://github.com/salemlenguaje-hue/STTM/actions/workflows/tests.yml/badge.svg)](https://github.com/salemlenguaje-hue/STTM/actions/workflows/tests.yml)

**Local-first, tamper-evident audit trails for AI Safety evaluations.**

> *Note: This English document is the reference for international evaluation and grants. The author's native engineering language is Spanish; internal governance documents (ADRs, GOBs) and the Spanish One-Pager are available in `docs/`.*

## Background & Origin — read this before judging the commit history

STTM did not start yesterday. It consolidates **more than two years** of
methodological work, engineering, and hard lessons from the author's
earlier projects:

- **Sofía Salem** — a cognitive-architecture experiment (80+ signed ledger
  entries, a publicly documented retraction, 700+ automated tests) where
  the traceability method was stress-tested in real practice.
- **Salem language toolchain** — a from-scratch compiler and runtime
  (lexer, parser, semantic analysis, MIR, C/Arduino backends, own
  persistence layer), built solo, which supplied the engineering
  discipline this repository inherits.
- **Alejandra** — a second application of the method, in development.

The dense commit history you see here is **integration and consolidation
work**, not the beginning of development: battle-tested components,
formats and lessons were assembled into this coherent framework. The
method was applied, audited and corrected in real use — including
documented failures — before being packaged as STTM.

**Why "Salem"?** It is the family surname of the author's wife and
daughters. No historical or mystical connotation is intended.

## About the Author

**Martín José Dalberto** — 41 years old, born and based in Misiones,
Argentina. Independent developer. Self-taught by choice and by context:
learned by reading documentation, breaking things and fixing them.
Works from Termux on an Android phone, with mate, in his home province.

He sustains three intertwined projects (Salem, Sofía, STTM) that form a
research ecosystem on verifiable traceability and artificial intelligence.
No team yet — but there is method: a signed ledger, external witnesses,
documented incidents, and the conviction that a well-documented error is
worth more than an unaudited success.

## 1. The Problem
In AI safety and agent evaluation, metrics, logs, and experimental results are often stored in mutable databases, ephemeral notebooks, or plain text files. When the stakes are high—such as publishing safety benchmarks, auditing model behavior, or applying for research grants—the integrity of the evaluation trail is as critical as the model itself. 

Current solutions often rely on:
- Heavy, cloud-dependent enterprise software.
- Manual copy-pasting into PDFs (which breaks reproducibility).
- Git commits alone (which track code changes, but not necessarily the semantic intent, environment state, or experimental context).

## 2. The Solution: STTM
**STTM** is an open-source methodology and lightweight tool designed to generate verifiable, append-only evidence chains for AI experiments and technical reports. 

It is built for independent researchers, auditors, and small teams who need to prove *what* was tested, *when*, and *under what conditions*, without relying on external SaaS platforms.

### Core Principles
- **Local-First:** Operates entirely offline. Your data never leaves your machine unless you explicitly export it.
- **Append-Only Ledger:** Uses a cryptographically chained JSONL ledger (`BITACORA.jsonl`). Past entries cannot be silently altered without breaking the chain.
- **Honest Cryptography:** Uses SHA-256 hash chaining by default. Ed25519 asymmetric signing is available as an optional adapter for public verification, but the tool explicitly declares its cryptographic boundaries (no "magic immutability" claims).
- **Privacy by Design:** Includes built-in audit scripts to detect and sanitize private keys, local paths, and sensitive tokens before exporting evidence to public repositories.

## 3. Three Modes of Governance
STTM adapts to the user's needs without forcing heavy ceremonies on simple projects:
1. **Simple Mode:** Basic event logging and hash-chaining. Ideal for quick experiment tracking.
2. **Continuity Mode:** Adds state tracking, project indices, and handoff documents. Ideal for long-running research or AI-assisted workflows.
3. **Salem Mode:** Full traceability, including Architecture Decision Records (ADRs), risk matrices, and formal audit preparation.

## 4. What STTM is NOT (Declared Limits)
Transparency is a core safety feature. STTM:
- ❌ Is **not** an ISO-certified auditing tool.
- ❌ Does **not** provide absolute immutability against the hardware owner (it detects tampering, but cannot physically prevent a root user from deleting the drive).
- ❌ Is **not** a replacement for formal HSMs (Hardware Security Modules) or enterprise PKI.
- ❌ Does **not** execute or evaluate AI models; it only tracks the *evidence* of the evaluation process.

## 5. Current State & Roadmap

### What works today (v0.3.0)
- **Core ledger:** Append-only JSONL with SHA-256 hash chaining and schema versioning (v1 legacy, v2 current).
- **Cryptographic integrity:** Ed25519 signing with public key anchored in Bitcoin via OpenTimestamps (testigo #2 confirmed).
- **Three governance modes:** Simple, Continuity, and Salem modes with explicit transitions documented in `docs/01-metodo/MODOS-DE-GOBERNANZA.md`.
- **Local web UI:** Three-level interface (ledger, documents, audits) with project selector, mode switcher, and manual validation checklist.
- **Multi-project support:** Catalog with append-only project creation, isolated ledgers per project, and UI-based project management.
- **Privacy audits:** Built-in `auditar.py` script that classifies files by `.gitignore` rules and generates sanitized manifests.
- **External witnesses:** Gmail email timestamp (testigo #1) and OpenTimestamps Bitcoin anchor (testigo #2, confirmed).
- **70 automated tests** covering endpoints, cryptographic integrity, input validation, and governance transitions.
- **34 signed ledger entries** documenting the project's own development with full incident history.

### Known limitations (declared honestly)
- **No automated UI rendering tests:** Validated manually on real devices (see `docs/05-ui/VALIDACION-MANUAL-UI.md`).
- **Append is O(n) per entry:** Acceptable at current scale; declared as technical debt.
- **JSON canonicalization is Python-specific:** External verifiers must replicate exact separators or wait for schema v3.
- **Document registration (GOB-005 style):** Pending implementation.

### Roadmap (no promises, only intentions)
- **K-004:** Document registration workflow with version tracking.
- **K-101:** Public paper on the method with verifiable evidence.
- **K-105:** Exportable audit packages (.zip) for grant applications.
- **Second adopter validation:** Seeking N=2 methodological validation (current: N=1 with Sofía Salem).

## 6. Quick Start
```bash
# Clone the repository
git clone https://github.com/salemlenguaje-hue/STTM.git
cd STTM

# Register a new event in the ledger
python scripts/registrar.py "Experiment A/B started" "Testing prompt injection resilience" --archivos "data/exp_01.json"
```

## 7. License & Authorship
Created by **Martín José Dalberto** (Argentina, 2026).  
Part of the broader [Salem Ecosystem](https://github.com/salemlenguaje-hue).  
**Licenses (real files in this repo):**
- Code (`scripts/`, `tests/`, `web/`): [MIT License](LICENSE) — Copyright (c) 2026 Martín José Dalberto.
- Documentation (`README.md`, `docs/`, report templates): [CC-BY 4.0](LICENSE-DOCS.md).
- Salem isolog / trademark: not licensed; all rights reserved (INPI registration).
