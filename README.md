# STTM — Salem Traceability & Trust Method

**Local-first, tamper-evident audit trails for AI Safety evaluations.**

> *Note: This English document is the reference for international evaluation and grants. The author's native engineering language is Spanish; internal governance documents (ADRs, GOBs) and the Spanish One-Pager are available in `docs/`.*

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
- **v0.1.0 (Current):** Core methodology, JSONL ledger, hash-chaining, and basic audit scripts.
- **v0.2.0 (Next):** HTML local viewer for the ledger, automated privacy sanitization reports, and Ed25519 integration.
- **v0.3.0 (Future):** Exportable audit packages formatted specifically for AI Safety grant applications.

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
