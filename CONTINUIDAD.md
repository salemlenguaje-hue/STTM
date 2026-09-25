# CONTINUIDAD — Proyecto STTM

**Propósito:** Este documento existe para que cualquier persona, colaborador o asistente IA que clone este repositorio sin contexto previo pueda entender qué es STTM, cómo está estructurado, cómo se trabaja y dónde continuar.
**Lectura obligatoria antes de tocar cualquier archivo.**

**Última actualización:** 2026-09-23
**Versión del proyecto:** 0.3.0 (Interfaz ADR-002 implementada)
**Entorno de desarrollo:** Termux (Android) / Linux / macOS
**Tests automatizados:** 70 (GitHub Actions CI)
**Entradas en bitácora:** 40 (v1=9, v2=31; incluye el registro de este cierre)

---

## ÍNDICE
1. Qué es STTM
2. Los Tres Modos de Gobernanza
3. Estructura del proyecto
4. Cómo está programado
5. Estado actual y Límites declarados
6. Incidentes documentados
7. Cómo continuar (Flujo de trabajo)
8. Reglas de oro

---

## 1. QUÉ ES STTM

### 1.1. Visión
STTM (Salem Traceability & Trust Method) es una metodología y una herramienta de código abierto diseñada para generar cadenas de evidencia verificables, locales y a prueba de manipulaciones (tamper-evident) para experimentos, auditorías y reportes técnicos.

No es una blockchain. No es un SaaS en la nube. Es un ledger local (append-only) que permite a investigadores independientes y auditores probar *qué* se hizo, *cuándo* y *bajo qué condiciones*, sin depender de servicios externos.

### 1.2. Filosofía
- **Local-First:** Los datos no salen de la máquina a menos que el usuario los exporte.
- **Evidencia antes que publicidad:** Ninguna capacidad se anuncia si no hay un test, un hash o un reporte que la respalde.
- **Criptografía honesta:** SHA-256 para encadenamiento, HMAC para integridad simétrica, Ed25519 para no-repudio. No prometemos inmutabilidad mágica frente al dueño del hardware; prometemos detección matemática de alteraciones.
- **Neutralidad de estrategia:** STTM no nombra financiadores ni entidades objetivo en documentación pública. Se usan términos neutrales ("entidad evaluadora"). Las notas con nombres propios viven en `data/estrategia/` (excluida por `.gitignore`).

---

## 2. LOS TRES MODOS DE GOBERNANZA

1. **Modo Registro Simple:** Solo bitácora JSONL encadenada.
2. **Modo Continuidad:** Agrega documentos de estado, índices y handoff. (Este proyecto usa este modo como base, y hoy opera en Salem.)
3. **Modo Salem:** Trazabilidad completa con ADRs, GOBs, auditorías y export de evidencia.

**Definición formal:** [ADR-STTM-001](docs/02-arquitectura/ADR-STTM-001-modelo-de-evidencia.md).
**Interfaz por modo:** [ADR-STTM-002](docs/02-arquitectura/ADR-STTM-002-interfaz-tres-niveles.md) (implementado).
**Catálogo y auditorías:** [ADR-STTM-003](docs/02-arquitectura/ADR-STTM-003-proyectos-y-auditorias.md) (implementado).

---

## 3. ESTRUCTURA DEL PROYECTO

```text
~/sttm/
├── CONTINUIDAD.md           <- ESTE DOCUMENTO
├── README.md                <- One-Pager público (Inglés)
├── KANBAN.md                <- Tablero vivo de tareas (reglas y cola)
├── LICENSE / LICENSE-DOCS.md<- MIT (código) / CC-BY 4.0 (docs)
│
├── docs/
│   ├── 00-gobernanza/       <- GOB-STTM-001
│   ├── 01-metodo/           <- One-Pagers EN/ES + nota biográfica del autor (ES)
│   ├── 02-arquitectura/     <- ADR-001, ADR-002 (+addendum 3.6), ADR-003
│   ├── 05-ui/               <- PUNTOS-CRITICOS-UX.md (documento vivo)
│   └── IDENTIDAD-VISUAL-SALEM-STTM.md
│
├── scripts/
│   ├── rutas.py             <- Fuente única de verdad de rutas (K-002)
│   ├── registrar.py         <- Bitácora (hash/HMAC/Ed25519)
│   ├── verificar.py         <- Cadena + schemas v1/v2 + firmas
│   ├── auditar.py           <- Privacidad + integridad + meta.json + manifiesto
│   ├── firma.py             <- Adaptador de firma
│   ├── proyectos.py         <- Catálogo append-only (ADR-003)
│   ├── auditoria_meta.py    <- Metadatos de auditoría (ADR-003)
│   └── servidor.py          <- API local + estáticos (ADR-002)
│
├── tests/                   <- 55 tests (unitarios, integración, endpoints, paridad K-002, selector K-001)
├── web/                     <- Visor/UI (index.html, app.js v3, style.css, assets)
├── auditorias/              <- Una carpeta por auditoría: reporte + meta + manifiesto
└── data/
    ├── proyectos.jsonl      <- Catálogo de proyectos
    ├── proyectos/
    │   └── 1-STTM/
    │       └── BITACORA.jsonl  <- Cadena de evidencia (append-only, 24 entradas)
    ├── backups/             <- Backups con timestamp (no se borran)
    ├── claves/              <- Ed25519 (privada excluida por .gitignore)
    └── estrategia/          <- Notas locales con nombres (excluida)
```

---

## 4. CÓMO ESTÁ PROGRAMADO

- **Lenguaje:** Python 3.11+ (stdlib + `cryptography` para Ed25519).
- **Tests:** `unittest` con sandboxes (`tempfile` + `STTM_ROOT` + puerto libre). Los tests nunca tocan la bitácora real.
- **Servidor:** `http.server` en loopback por defecto; `--movil` abre a la red local (decisión declarada). Lee `web/` del disco en cada request: **los cambios de UI no requieren reinicio; los cambios de `scripts/` sí**.
- **UI (app.js v3):** render con `createElement` + `textContent` para datos externos (innerHTML con datos rompía atributos con comillas). Selectores de listeners siempre con scope, nunca globales (lección UI-001).

### Endpoints del servidor (ADR-002)
Lectura: `/api/bitacora`, `/api/proyecto`, `/api/documentos`, `/api/documento`, `/api/auditorias`, `/api/reporte`, `/api/verificar-paquete`.
Escritura: `/api/registrar`, `/api/modo`, `/api/documento`, `/api/auditar`.
Guards: rutas `.md` solo bajo `docs/` o `CONTINUIDAD.md`, sin `..`; nombres de carpeta de auditoría con regex estricta; subprocess sin shell.

### Capacidades de la UI por modo (regla de honestidad visual)
Lo deshabilitado no se muestra (ni gris ni tachado). El selector de modo siempre visible y con confirmación explícita + registro en bitácora. Export de reportes en 3 niveles: descarga `.md` con BOM UTF-8, Web Share API con archivo, menú mailto/wa.me con resumen (ADR-002 §3.6).

---

## 5. ESTADO ACTUAL Y LÍMITES DECLARADOS

### Qué funciona hoy
✅ Cadena JSONL append-only con schemas v1/v2 y firmas hash/HMAC/Ed25519.
✅ Motor de auditoría con clasificación por `.gitignore` (rojo/ámbar) y manifiestos.
✅ Catálogo de proyectos y metadatos de auditoría (ADR-003).
✅ Interfaz de tres niveles completa: registro, documentos, auditorías, export, Ayuda.
✅ CI con GitHub Actions: 40 tests en 3 versiones de Python.
✅ Gobernanza: GOB-001, ADR-001/002/003, CONTINUIDAD, identidad visual documentada.
✅ Incidentes 001, 002 y UI-001 documentados con fix, tests y lecciones.
✅ Clave pública Ed25519 anclada en el repo (K-005): verificación completa por terceros y en CI.
✅ Multi-proyecto: catálogo y carpetas por proyecto, selector en UI (K-001), bitácoras y auditorías aisladas.
✅ Creación de proyectos desde la UI (K-007): endpoint con validación de ref única y asiento en bitácora.

### Lo que STTM NO es / deudas declaradas
❌ **No es un HSM:** no protege contra root con control del disco.
✅ **Validación manual de UI declarada (K-003):** checklist de 8 puntos en docs/05-ui/VALIDACION-MANUAL-UI.md.
❌ **Selector de proyecto en UI:** pendiente (hoy opera el proyecto #1; el catálogo ya soporta N).
❌ **Migración de `BITACORA.jsonl` a `data/proyectos/1-STTM/`:** pendiente (ADR-003 §3.5).
❌ **Timestamping externo con testigos:** no implementado (capa siguiente al anclaje de clave).
❌ **Render Markdown en vivo y WYSIWYG:** no prometidos (ADR-002).
✅ **Registro de documentos estilo GOB-005 (K-004):** docs/00-gobernanza/REGISTRO-DOCS.md.
❌ **Append O(n) por registro (H6):** leer_ultima_entrada recorre toda la bitácora; aceptable a escala actual, deuda declarada.
❌ **Canonicalización v2 específica de Python (H7):** un verificador externo deberá replicar separadores exactos o esperar un schema v3; no tocar sin incidente documentado.

---

## 6. INCIDENTES DOCUMENTADOS

- **Incidente 001** — Cambio de fórmula de hash sin compatibilidad. Verificador tolerante v1/v2 + HMAC legacy como aviso. Entrada #11.
- **Incidente 002** — Patrón de detección sin forma real + clasificación binaria de sensibles. Regex con longitud mínima + clasificación por `.gitignore` + manifiesto real. Entrada #16.
- **Incidente UI-001** — Listeners globales de copiar pisaban "Ver reporte"/"Ver documento". Selectores con scope + guard de copiado.
- **PC-001 a PC-010 y MEJ-001** — Registro vivo de fricciones de UX en [docs/05-ui/PUNTOS-CRITICOS-UX.md](docs/05-ui/PUNTOS-CRITICOS-UX.md), que alimenta el panel de Ayuda de la UI.

---

## 7. CÓMO CONTINUAR (FLUJO DE TRABAJO)

1. **Planificar:** ADR en `docs/02-arquitectura/` si es cambio estructural.
2. **Hacer:** código en `scripts/` o `web/`.
3. **Verificar (tests):** `python -m unittest discover tests 2>&1 | tail -4`.
4. **Verificar (auditoría):** `python scripts/auditar.py --motivo "..."`.
5. **Registrar:** `python scripts/registrar.py "Título" "Detalle" --archivos "..." --modo-firma ed25519`.
6. **Liberar:** `git add ... && git commit && git push`.
7. **UI en vivo:** `python scripts/servidor.py` (o `--movil`); cambios de `web/` se ven recargando; cambios de `scripts/` requieren reinicio.

### Próximos pasos
1. ~~Selector de proyecto en la UI~~ — HECHO (K-001, STTM-0.21).
2. ~~Migración de la bitácora~~ — HECHO (K-002, STTM-0.20): vive en `data/proyectos/1-STTM/`.
3. Tests de render de UI (o declaración formal de que quedan manuales).
4. Registro de documentos estilo GOB-005 (el tablero vivo es KANBAN.md).
5. Testigo externo manual del fingerprint de la clave (fuera de GitHub), por el autor.
6. Actualización del documento de identidad Capa 2 por el autor.

---

## 8. REGLAS DE ORO

1. **Nada se acepta sin test.** Si no está en `tests/`, no existe.
2. **Nada se edita hacia atrás.** La bitácora es sagrada; los errores se corrigen con entradas nuevas.
3. **Cero secretos en el repo.** `.gitignore` + `auditar.py` lo protegen.
4. **Honestidad técnica.** Lo no implementado se dice "pendiente", nunca "activo".
5. **Neutralidad de estrategia.** Sin nombres de entidades en docs públicos.
6. **Un error detectado es un tesoro.** Todo incidente se documenta con fix, test y lección.
7. **Paridad en reescrituras de UI.** Reescribir un archivo de UI completo exige checklist de paridad con la versión anterior (PC-008).

---
*Documento generado y mantenido bajo la metodología STTM.*
