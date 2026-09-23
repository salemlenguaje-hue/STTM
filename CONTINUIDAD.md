# CONTINUIDAD — Proyecto STTM

**Propósito:** Este documento existe para que cualquier persona, colaborador o asistente IA que clone este repositorio sin contexto previo pueda entender qué es STTM, cómo está estructurado, cómo se trabaja y dónde continuar.
**Lectura obligatoria antes de tocar cualquier archivo.**

**Última actualización:** 2026-09-23
**Versión del proyecto:** 0.2.0 (Línea base pública)
**Entorno de desarrollo:** Termux (Android) / Linux / macOS
**Tests automatizados:** 31 (GitHub Actions CI)
**Entradas en bitácora:** 15 (v1=9, v2=6, 1 aviso legacy documentado)

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
- **Criptografía honesta:** Usamos encadenamiento SHA-256 por defecto, HMAC para integridad simétrica, y Ed25519 para no-repudio asimétrico. No prometemos "inmutabilidad mágica" frente al dueño del hardware; prometemos detección matemática de alteraciones.
- **Neutralidad de estrategia:** STTM no nombra financiadores ni entidades objetivo en documentación pública. Se usan términos neutrales ("entidad evaluadora", "financiador potencial"). Las notas de planificación con nombres propios viven en `data/estrategia/` (excluida por `.gitignore`).

---

## 2. LOS TRES MODOS DE GOBERNANZA

STTM se adapta al usuario. No obliga a usar ingeniería pesada en proyectos simples.

1. **Modo Registro Simple:** Solo bitácora JSONL encadenada. Ideal para tracking rápido de experimentos.
2. **Modo Continuidad:** Agrega documentos de estado, índices y handoff. Ideal para proyectos que retoma una IA o un colaborador. (Este proyecto usa este modo).
3. **Modo Salem:** Trazabilidad completa con ADRs, GOBs, matrices de riesgo y preparación formal para auditorías externas.

**Definición formal:** ver [ADR-STTM-001](docs/02-arquitectura/ADR-STTM-001-modelo-de-evidencia.md).

---

## 3. ESTRUCTURA DEL PROYECTO

```text
~/sttm/
├── CONTINUIDAD.md           <- ESTE DOCUMENTO
├── README.md                <- One-Pager público (Inglés)
├── BITACORA.jsonl           <- Cadena de evidencia (Append-only, 15 entradas)
├── LICENSE                  <- MIT (Código)
├── LICENSE-DOCS.md          <- CC-BY 4.0 (Documentación)
│
├── docs/                    <- Documentación y Gobernanza
│   ├── 00-gobernanza/       <- GOBs (Reglas del proyecto)
│   ├── 01-metodo/           <- One-Pagers y definiciones
│   ├── 02-arquitectura/     <- ADRs (Decisiones técnicas)
│   │   ├── ADR-STTM-001-modelo-de-evidencia.md
│   │   ├── ADR-STTM-002-interfaz-tres-niveles.md
│   │   └── ADR-STTM-003-proyectos-y-auditorias.md
│   └── 05-ui/               <- (Pendiente) Padrón de estilos
│
├── scripts/                 <- El núcleo de la herramienta
│   ├── registrar.py         <- Agrega entradas a la bitácora
│   ├── verificar.py         <- Valida la cadena de hashes
│   ├── auditar.py           <- Motor de inspección (privacidad + integridad)
│   ├── firma.py             <- Adaptador de firma (hash/HMAC/Ed25519)
│   ├── proyectos.py         <- Gestor del catálogo de proyectos (ADR-003)
│   └── auditoria_meta.py    <- Metadatos de auditoría (ADR-003)
│
├── tests/                   <- Suite de tests (unittest + tempfile)
├── web/                     <- Visor HTML local (API + Frontend)
├── auditorias/              <- Reportes Markdown + meta.json + manifiesto.json
└── data/
    ├── claves/              <- Claves Ed25519 (privada excluida por .gitignore)
    ├── estrategia/          <- Notas de planificación local (excluida por .gitignore)
    └── proyectos.jsonl      <- Catálogo de proyectos (ADR-003)
```

---

## 4. CÓMO ESTÁ PROGRAMADO

- **Lenguaje:** Python 3.11+ (Biblioteca estándar + `cryptography` para Ed25519).
- **Tests:** `unittest` con aislamiento de entornos temporales (`tempfile`). Los tests nunca tocan la bitácora real del usuario. 31 tests en CI.
- **Servidor Web:** `http.server` (stdlib) sirviendo en loopback (`127.0.0.1`) por seguridad, con flag `--movil` para desarrollo en red local.
- **Criptografía:** 
  - SHA-256 para encadenamiento de hashes (schema v2).
  - HMAC-SHA256 para integridad simétrica.
  - Ed25519 para no-repudio asimétrico (usando `cryptography` precompilado de Termux).

### Convenciones
- Los scripts leen la variable de entorno `STTM_ROOT` para saber dónde está la raíz del proyecto. Si no está, asumen que están en `scripts/` y suben un nivel.
- Las correcciones a la bitácora **nunca** se hacen editando líneas pasadas. Se agrega una entrada nueva de "Fe de erratas".
- El verificador acepta schemas v1 (histórico) y v2 (canónico), y reconoce HMAC legacy como aviso documentado.

---

## 5. ESTADO ACTUAL Y LÍMITES DECLARADOS

### Qué funciona hoy
✅ Cadena JSONL append-only con SHA-256 (schema v2).
✅ Firma asimétrica Ed25519 con ceremonia de claves local.
✅ Verificador de integridad tolerante (detecta alteraciones, acepta schemas v1/v2).
✅ Motor de auditoría con clasificación por `.gitignore` (incidente 002).
✅ Visor web local con capa visual clara (isologo original + ilustración derivada).
✅ CI/CD con GitHub Actions (31 tests corren en cada push).
✅ Gobernanza completa: GOB-001, ADR-001, ADR-002, ADR-003.
✅ Catálogo de proyectos y metadatos de auditoría (ADR-003 implementado).
✅ Política de neutralidad de estrategia.

### Lo que STTM NO es (Límites honestos)
❌ **No es un HSM:** No protege contra un usuario root que quiera borrar el disco.
❌ **No es una base de datos:** No reemplaza a SQLite o Postgres para consultas complejas; es un ledger de auditoría.
❌ **No tiene interfaz de 3 niveles implementada:** ADR-002 define el diseño, pero el visor actual no tiene selector de modo (próximo paso).
❌ **No firma metadatos de auditoría:** La firma del solicitante y ejecutor queda como decisión pendiente (ADR-003).

---

## 6. INCIDENTES DOCUMENTADOS

### Incidente 001 — Cambio de fórmula de hash sin compatibilidad

**Detección:** Entrada #10 de la bitácora, firmada con HMAC usando la fórmula vieja (incluía `firma=None` en el hash).

**Diagnóstico:** Al reescribir `registrar.py` para el adaptador de firma, se cambió la fórmula del hash (sacó el campo `firma` de la base). Las entradas 1-8 fueron firmadas con la fórmula vieja (v1), el verificador nuevo solo conocía la nueva (v2), y entonces toda la historia pareció alterada.

**Fix:** Verificador tolerante que acepta schemas v1 (histórico) y v2 (canónico), y reconoce HMAC legacy como aviso documentado. La bitácora no se edita hacia atrás.

**Lección:** Los schemas de hash se versionan desde el día uno. Cambiar una fórmula sin migración convierte tu historia en "alterada".

**Entrada:** #11 en bitácora.

---

### Incidente 002 — Patrón de detección sin forma real + clasificación binaria

**Detección:** Primera ejecución de `auditar.py` integrado con catálogo. El escáner reportó 3 rojos:
1. `CONTINUIDAD.md` "contiene 'ghp_'"
2. `BITACORA.jsonl` "contiene 'ghp_'"
3. `data/claves/sofia_privada.pem` es archivo sensible

**Diagnóstico:**
1 y 2. **Falso positivo.** El patrón era el prefijo pelado `ghp_`. Pero un token real de GitHub es `ghp_` seguido de 36 caracteres alfanuméricos. Lo que encontró el escáner fue nuestra propia prosa describiendo el patrón (CONTINUIDAD.md dice "tokens `ghp_`", la bitácora dice "detección de token ghp_"). El escáner se volvió a auto-detectar, esta vez a través de la documentación que lo describe. Y la bitácora no se puede editar para "limpiarla" (rompería la cadena), así que la corrección correcta era arreglar el patrón, no el texto.

3. **Verdadero positivo mal clasificado.** Ahí hay una clave privada real, sí. Pero vive en su ubicación declarada (ADR-001 y fe de erratas) y está cubierta por `.gitignore` (`*.pem`). No es un leak accidental: es el cofre declarado. Un escáner útil no debería tratar igual "clave tirada en el repo" que "clave en su cofre ignorado por git".

**Deudas detectadas:**
- `meta.json` declaraba `manifiesto_ruta: "manifiesto.json"` pero `auditar.py` nunca escribió ese archivo. Anunciar artefactos fantasma es exactamente lo que STTM prohíbe.
- `firmas_validadas: 14` en lugar de 15 porque la entrada #10 (HMAC legacy) se reconoce con aviso pero no suma como firma validada. Conservador = mejor para una herramienta de confianza.

**Fix:**
- Regex con forma real del secreto: `ghp_[A-Za-z0-9]{36,}` en lugar de prefijo pelado.
- Clasificación consciente de `.gitignore`: rojo si el archivo sensible NO está excluido (riesgo de publicación), ámbar si está excluido (ubicación controlada, con recordatorio de verificar que la exclusión siga vigente).
- `manifiesto.json` ahora se escribe de verdad (hashes de `reporte.md` y de la bitácora).
- Auditoría retroactiva de la carpeta 165225 para cubrir el gap de coherencia.

**Tests de regresión:** 5 tests nuevos en `tests/test_privacidad.py` que cubren las tres clases de bug detectadas.

**Lecciones:**
1. Un patrón de detección debe modelar la forma real del secreto, no su prefijo.
2. La bitácora no se edita para "limpiarla": se corrige el patrón.
3. Un archivo sensible en su cofre declarado no es un leak: es una ubicación controlada.
4. Lo que se anuncia debe existir. Anunciar artefactos fantasma es humo.

**Entrada:** #16 en bitácora.

---

## 7. CÓMO CONTINUAR (FLUJO DE TRABAJO)

Si vas a agregar una feature o arreglar un bug, este es el ciclo PDCA obligatorio:

1. **Planificar:** Crear un ADR en `docs/02-arquitectura/` si es un cambio estructural.
2. **Hacer:** Escribir el código en `scripts/` o `web/`.
3. **Verificar (Tests):** Agregar un test en `tests/`. Correr `python -m unittest discover tests -v`.
4. **Verificar (Auditoría):** Correr `python scripts/auditar.py` para asegurar que no filtraste secretos.
5. **Registrar:** 
```bash
   python scripts/registrar.py "Título del hito" "Detalle" --archivos "script.py" --modo-firma ed25519
```
6. **Liberar:** `git add . && git commit && git push`.

### Próximos pasos (pendientes)
1. **Implementar ADR-002:** Interfaz de 3 niveles con selector de modo.
2. **Actualizar documento de identidad Capa 2:** El autor revisará el padrón de estilos para alinear la capa visual clara con la identidad formal.

---

## 8. REGLAS DE ORO

1. **Nada se acepta sin test.** Si no está en `tests/`, no existe.
2. **Nada se edita hacia atrás.** La bitácora es sagrada. Los errores se corrigen con entradas nuevas.
3. **Cero secretos en el repo.** El `.gitignore` y `auditar.py` protegen esto. Nunca commitees un `.env`, una `.key` privada, o notas de `data/estrategia/`.
4. **Honestidad técnica.** Si una capacidad no está implementada, la documentación debe decir "pendiente" o "reservada", nunca "activa". (Alineado a Tomo II de Salem, R20-33).
5. **Neutralidad de estrategia.** STTM no nombra financiadores en documentación pública. Las notas con nombres propios viven en `data/estrategia/` (local, nunca se commitea).
6. **Un error detectado es un tesoro.** Cada incidente documentado refuerza el método.

---
*Documento generado y mantenido bajo la metodología STTM.*
