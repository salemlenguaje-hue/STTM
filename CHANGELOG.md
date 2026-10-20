# CHANGELOG — STTM

## v0.4.x — Firma de auditorías (en curso)

- **Firma del ejecutor:** `meta.json` de cada auditoría se firma con la clave Ed25519 del usuario que la ejecuta (`identidad.firmar_como`), sobre el JSON canónico JCS. La firma queda en el campo `firma`.
- **Manifiesto enlazado:** `meta.json` incluye `manifiesto_sha256`, así que la firma cubre también el manifiesto y, por él, los hashes de los artefactos.
- **Verificación:** `/api/verificar-paquete` devuelve `firma_meta` con el estado (`firmada_valida`, `firma_invalida`, `sin_firma`) y el estado del manifiesto (`ok`, `alterado`, `faltante`).
- **Sin usuario, sin firma:** una auditoría sin actor queda con `firma: null` y se declara así.
- **Rol por defecto:** `--rol-actor` pasa de `auditor` a `lector` (menor privilegio).
- **CLI sin autor por defecto:** `auditoria_meta.py generar` exige `--solicitante-nombre` y `--ejecutado-nombre`.

Pendiente, decisión de diseño: la firma del **solicitante**. Requiere un flujo de aprobación entre dos usuarios (ADR-003). Hoy solicitante y ejecutor son la misma persona cuando se audita desde la interfaz.

## v0.4.0 (2026-09) — "Empresarial / N≥2"

Motivada por: llevar STTM de herramienta de un solo autor a algo que un
equipo o una empresa pueda adoptar como método de seguimiento y
trazabilidad confiable.

### Agregado
- **Identidad multiusuario real** (`identidad.py`): usuarios, roles (lector/auditor/admin), clave Ed25519 propia por persona. Reemplaza la clave única de proyecto compartida. Ver ADR-004.
- **Schema v3** de la bitácora: canonicalización JCS (RFC 8785) en vez de `json.dumps` específico de Python, y campo `actor` firmado. Ver ADR-005.
- **Índice SQLite + búsqueda de texto libre** (`indice.py`), reconstruible desde el ledger, nunca fuente de verdad. Ver ADR-006.
- **Crypto-shredding** (`cifrado.py`): borrado seguro de contenido sensible compatible con la inmutabilidad del ledger. Ver ADR-007.
- **Testigo RFC 3161 automático** (`testigo_rfc3161.py`) — **BETA, no validado contra una TSA real**. Ver ADR-008.
- **Servidor HTTP con autenticación y roles reales**: todo endpoint `/api/*` (salvo login) exige token válido; rate-limiting de intentos de login por `(ip, usuario)`.
- **Contenedorización**: `docker/Dockerfile` + `docker/docker-compose.yml` + Caddy para TLS automático — **no probado end-to-end** (sin red en el entorno de desarrollo).
- **Git hook** (`hooks/post-commit`) para registro automático de commits.
- **Mapeo a estándares de cumplimiento** (ISO/IEC 42001, NIST AI RMF, SOC 2) — `docs/07-cumplimiento/MAPEO-ESTANDARES.md`.
- `LICENSE` (MIT) y `LICENSE-DOCS.md` (CC-BY 4.0): existían solo como referencia en la documentación de v0.3, ahora existen como archivos reales.
- `AYUDA.md` e `INSTALACION.md`.

### Corregido (hallazgos de un análisis crítico externo previo)
- `auditar.py` tenía `solicitante`/`ejecutado_por` hardcodeados a un único nombre de autor. Ahora viene del usuario autenticado real (`--actor`).
- Las claves de firma se llamaban `sofia_*` pese a ser de un proyecto distinto (herencia de código reciclado). Ahora cada usuario tiene su propia clave, sin ese nombre heredado.

### Corregido (encontrado durante la integración de esta misma versión)
- FTS5 (el motor de búsqueda del índice) trata `-` como operador NOT: un texto con guiones (ej. "Ref-STTM-004") rompía la búsqueda en silencio. `indice.py` ahora sanitiza la consulta antes de pasarla a SQLite.
- El rate-limiter de login, si fuera solo por IP, bloquearía a toda una red compartida (ej. la wifi de un aula) por el error de una sola persona. Se cambió a `(ip, usuario)`.

### Estado de pruebas
80/80 tests automatizados en verde, corridos realmente (no solo
declarados) en el entorno de desarrollo: canonicalización JCS, identidad
y roles, índice y búsqueda, crypto-shredding, codificador DER + vector de
referencia conocido para el testigo RFC 3161, integración registro→verificación
v3 de punta a punta, e integración del servidor HTTP real (auth, roles,
rate-limit, búsqueda) levantando el proceso y golpeándolo por HTTP.

### Declarado como pendiente, no activo
- Testigo RFC 3161 sin validar contra una TSA real (requiere red).
- Build de Docker sin validar (requiere red).
- Sin 2FA, sin recuperación de contraseña por email.
- Gestión de usuarios solo por CLI, no expuesta por la API web (decisión deliberada, no limitación técnica).
- Auditoría de seguridad externa del código: no realizada. Sigue siendo el paso bloqueante antes de cualquier despliegue serio en una empresa.

## v0.3.0 y anteriores

El historial de commits de versiones anteriores se conserva en este repositorio (rama main).
La bitácora real de STTM (proyecto 1-STTM, 43 entradas) se mantiene íntegra y verifica
con esta versión. La clave pública `data/claves/sofia_publica.pem` se conserva para verificar
las entradas legacy (schemas v1 y v2).
