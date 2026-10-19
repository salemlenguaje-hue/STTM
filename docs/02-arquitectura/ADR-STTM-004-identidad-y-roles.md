# ADR-STTM-004 — Identidad, roles y claves por persona

**SALEM**
**STTM — ADR-004: IDENTIDAD, ROLES Y CLAVES POR PERSONA**
Borrador de trabajo interno

Argentina, 2026

## 1. Control documental

| Dato | Definición |
|---|---|
| Identificador | STTM-ADR-004-2026-R1 |
| Estado | Borrador de trabajo interno, pendiente de revisión |
| Alcance | Define usuarios, roles y el reemplazo de la clave única de proyecto por una clave Ed25519 propia por persona. |
| Antecedentes | ADR-STTM-001 (modelo de evidencia); análisis crítico externo previo (hallazgo: `solicitante`/`ejecutado_por` hardcodeados a un único autor en `auditar.py`). |

## 2. Contexto

STTM v0.3 no tenía identidad real: `auditar.py` escribía siempre el mismo nombre como `solicitante` y `ejecutado_por`, y las entradas se firmaban con una única clave de proyecto (`sofia_privada.pem`, nombre heredado de otro proyecto del ecosistema) compartida por quien fuera que operara el sistema. Esto es inaceptable para una herramienta cuya propuesta de valor central es "quién hizo qué, verificablemente": sin identidad por persona, esa pregunta no tiene respuesta.

Además, una clave compartida entre todo un equipo tiene un problema estructural: si se filtra (como ocurrió, de hecho, con una exportación manual del proyecto durante este mismo trabajo), hay que rotarla para *todos* a la vez, y no hay forma de saber, mirando solo la firma, cuál de las personas con acceso realmente generó una entrada dada.

## 3. Decisión

- Cada persona que usa STTM es un **usuario** (`identidad.py`): nombre único, rol, contraseña (PBKDF2-HMAC-SHA256, 600.000 iteraciones — ver §5 para la limitación de no usar Argon2id), y **su propio par de claves Ed25519**, generado al crearse la cuenta.
- Tres roles, jerárquicos: **lector** (solo lectura) ⊂ **auditor** (+ registrar entradas, ejecutar auditorías, editar documentos) ⊂ **admin** (+ crear proyectos, cambiar de modo, gestionar usuarios).
- Toda entrada nueva de la bitácora (schema v3, ver ADR-005) se firma con la clave **del usuario autenticado que la generó**, nunca con una clave de proyecto compartida. La clave de proyecto (`firma.py ceremonia`) queda para casos que necesiten una firma a nivel proyecto (ej. un manifiesto de auditoría completo), no para atribuir autoría de entradas individuales.
- Las sesiones son tokens opacos con expiración (12 horas por defecto), no JWT: no hay necesidad de que el token sea autocontenido/verificable sin consultar al servidor, y un token opaco es más simple de revocar (`/api/logout` lo borra del lado del servidor de inmediato).

## 4. Consecuencias

- El servidor HTTP (`servidor.py`) pasa de no tener autenticación a exigirla en **todos** los endpoints `/api/`, con el rol mínimo correspondiente por endpoint.
- La gestión de usuarios (alta, baja) queda **solo por CLI** (`identidad.py crear/listar/desactivar`) en esta versión, deliberadamente: exponer alta de usuarios por API amplía la superficie de ataque sin un beneficio claro en el caso de uso típico (un admin con acceso a la máquina/servidor da de alta a su equipo).
- Un usuario desactivado no puede iniciar sesión, pero sus entradas pasadas siguen siendo verificables (la clave pública no se borra, solo la cuenta se marca inactiva).

## 5. Límites declarados

- PBKDF2-HMAC-SHA256 en vez de Argon2id: este entorno de desarrollo no tuvo acceso de red para instalar `argon2-cffi`. PBKDF2 con 600k iteraciones es defendible (recomendación OWASP 2023), pero Argon2id es preferible si el entorno de despliegue lo permite — ver INSTALACION.md.
- Sin 2FA, sin recuperación de contraseña por email. Declarado pendiente, no activo.
- El bloqueo de intentos fallidos de login es por `(ip, usuario)` en memoria del proceso: reinicia el servidor y se resetea; con más de un proceso servidor (balanceador de carga) necesitaría un store compartido. Suficiente para un servidor único self-hosted, no para un despliegue multi-instancia.
