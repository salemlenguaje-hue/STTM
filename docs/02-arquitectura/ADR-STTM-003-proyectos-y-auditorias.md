# ADR-STTM-003 — Catálogo de proyectos y registro de auditorías

**SALEM**  
**STTM — ADR-003: CATÁLOGO DE PROYECTOS Y REGISTRO DE AUDITORÍAS**  
Borrador de trabajo interno  

Autor del proyecto  
Martín José Dalberto  
Argentina, 2026  

## 1. Control documental

| Dato | Definición |
|---|---|
| Identificador | STTM-ADR-003-2026-R1 |
| Estado | Borrador de trabajo interno, pendiente de revisión |
| Alcance | Define el catálogo de proyectos gestionados por STTM, el registro de auditorías ejecutadas sobre cada uno, y dónde viven ambos. No toca la UI (ADR-002), la bitácora canónica (ADR-001) ni el núcleo criptográfico. |
| Autor | Martín José Dalberto, Argentina. |
| Antecedentes | ADR-STTM-001 (modelo de evidencia); ADR-STTM-002 (interfaz de tres niveles); GOB-STTM-001 (criterios básicos); CONTINUIDAD.md; Tomo I §2 (Opción C) y Tomo II §6 (modelo de amenazas) de Salem. |

Declaración de alcance. Este ADR define estructuras de datos y ubicaciones. No declara certificación ISO ni auditoría externa. Los metadatos de auditoría son declarativos y locales; la firma del solicitante o del ejecutor queda fuera de esta iteración y se declara como decisión pendiente.

## 2. Contexto

Hasta hoy STTM trata el proyecto como si fuera único: una sola bitácora (`BITACORA.jsonl`), un solo `data/proyecto.json` para el modo actual, y reportes de auditoría en `auditorias/<timestamp>/reporte.md`. Esto es insuficiente para tres casos de uso reales:

1. **El autor audita varios proyectos propios** (STTM mismo, un paper, un curso, una herramienta hermana).
2. **El autor audita proyectos de terceros** (por ejemplo, una postulación a una entidad evaluadora que pide evidencia de trazabilidad).
3. **Un tercero audita un proyecto del autor** usando STTM como herramienta.

Los tres casos necesitan:

- Saber **qué proyectos** existen y cómo identificarlos.
- Saber **qué auditorías** se ejecutaron sobre cada uno, quién las pidió, quién las hizo y qué encontraron.
- Mantener la bitácora canónica como fuente de verdad del proyecto, sin que los metadatos de auditoría la contaminen.

Este ADR resuelve esas tres necesidades con dos estructuras nuevas y una regla de separación.

## 3. Decisión

### 3.1 Catálogo de proyectos: `data/proyectos.jsonl`

Archivo append-only en formato JSONL. Cada línea es un proyecto. La primera versión del esquema (v1) tiene estos campos:

```json
{
  "n": 1,
  "ref_interna": "STTM",
  "titulo": "STTM — Salem Traceability & Trust Method",
  "descripcion": "Metodología y herramienta de trazabilidad, auditoría y evidencia para proyectos técnicos.",
  "creado_utc": "2026-09-23T18:00:00Z",
  "nivel_inicial": "continuidad",
  "nivel_actual": "continuidad",
  "primera_auditoria_utc": null,
  "ultima_auditoria_utc": null,
  "activo": true
}
```

| Campo | Tipo | Obligatorio | Mutabilidad |
|---|---|---|---|
| `n` | entero | sí | nunca (autoincremento, identificador primario local) |
| `ref_interna` | texto | no | sí (identificador humano; puede coincidir con el de un grant, cliente, paper, o ser libre) |
| `titulo` | texto | sí | sí |
| `descripcion` | texto | sí | sí |
| `creado_utc` | timestamp UTC | sí | nunca |
| `nivel_inicial` | enum (`simple`, `continuidad`, `salem`) | sí | nunca (se fija al crear) |
| `nivel_actual` | enum (`simple`, `continuidad`, `salem`) | sí | sí (cada cambio se registra en bitácora) |
| `primera_auditoria_utc` | timestamp UTC o null | sí | sí (solo una vez, del null al primer valor) |
| `ultima_auditoria_utc` | timestamp UTC o null | sí | sí |
| `activo` | booleano | sí | sí (desactivar no borra, solo marca) |

**Reglas:**

- `n` es estable y nunca se reutiliza. Si se borra un proyecto, `n` queda consumido.
- El archivo es append-only: correcciones se hacen con una entrada nueva (`"accion": "actualizar", "n": 3, ...`).
- El archivo actual se reconstruye leyendo todas las entradas en orden y aplicando las acciones.
- El proyecto "STTM mismo" es la entrada #1 del catálogo (dogfooding).

### 3.2 Ubicación de la bitácora por proyecto

Hoy la bitácora vive en `BITACORA.jsonl` (raíz). Con catálogo multi-proyecto, cada proyecto tiene su propia bitácora:

```text
data/
  proyectos.jsonl                ← catálogo (único para toda la instancia)
  proyectos/
    1-STTM/
      BITACORA.jsonl             ← bitácora del proyecto 1
      documentos/                ← documentos del proyecto
    2-PAPER-SEGURIDAD-IA/
      BITACORA.jsonl
      documentos/
```

El directorio se llama `<n>-<slug>` donde `<slug>` es una versión simplificada del título (ASCII, sin espacios). El slug es solo para legibilidad del filesystem; el identificador estable es `n`.

### 3.3 Registro de auditorías: `auditorias/<timestamp>/meta.json`

Cada auditoría ejecutada crea una carpeta `auditorias/<timestamp>/` con:

```text
auditorias/
  2026-09-23_180000/
    meta.json                    ← metadatos de la auditoría
    reporte.md                   ← resultado (humano)
    manifiesto.json              ← hashes de los artefactos (máquina)
    evidencia/                   ← bitácora exportada, documentos, etc.
```

El archivo `meta.json` tiene estos campos (schema v1):

```json
{
  "auditoria_id": "AUD-20260923-180000",
  "proyecto_n": 1,
  "proyecto_ref": "STTM",
  "fecha_utc": "2026-09-23T18:00:00Z",
  "motivo": "Línea base pública previa a postulación a entidad evaluadora.",
  "solicitante": {
    "rol": "autor",
    "nombre": "Martín José Dalberto"
  },
  "ejecutado_por": {
    "rol": "autor",
    "nombre": "Martín José Dalberto"
  },
  "tipo": "rapida",
  "modo_aplicado": "continuidad",
  "hallazgos": {
    "rojos": 0,
    "amarillos": 1,
    "informativos": 3
  },
  "estado_final": "apto_con_observaciones",
  "cadena_integra": true,
  "entradas_verificadas": 12,
  "entradas_totales": 12,
  "firmas_validadas": 12,
  "reporte_ruta": "reporte.md",
  "manifiesto_ruta": "manifiesto.json",
  "observaciones": [
    "Una ruta absoluta personal detectada; normalizar antes de publicar."
  ]
}
```

| Campo | Tipo | Obligatorio |
|---|---|---|
| `auditoria_id` | texto | sí (formato `AUD-YYYYMMDD-HHMMSS`) |
| `proyecto_n` | entero | sí (referencia al catálogo) |
| `proyecto_ref` | texto | sí (denormalizado, para legibilidad) |
| `fecha_utc` | timestamp UTC | sí |
| `motivo` | texto | sí (libre; una frase explicando por qué se audita) |
| `solicitante` | objeto `{rol, nombre}` | sí |
| `ejecutado_por` | objeto `{rol, nombre}` | sí |
| `tipo` | enum (`rapida`, `estandar`, `profunda`) | sí |
| `modo_aplicado` | enum (`simple`, `continuidad`, `salem`) | sí |
| `hallazgos` | objeto `{rojos, amarillos, informativos}` | sí |
| `estado_final` | enum (`apto`, `apto_con_observaciones`, `no_apto`) | sí |
| `cadena_integra` | booleano | sí |
| `entradas_verificadas` | entero | sí |
| `entradas_totales` | entero | sí |
| `firmas_validadas` | entero | sí |
| `reporte_ruta` | texto | sí (relativa a la carpeta de la auditoría) |
| `manifiesto_ruta` | texto | sí |
| `observaciones` | lista de textos | no |

**Reglas:**

- `solicitante` y `ejecutado_por` son **distintos por diseño**: en una auditoría interna pueden coincidir, pero en una auditoría para terceros son personas (o roles) diferentes.
- `rol` puede ser: `autor`, `colaborador`, `auditor_externo`, `ia_asistente`, `tercero`.
- El archivo `meta.json` se escribe **una sola vez** al final de la auditoría. No se modifica; si hay que corregir algo, se crea una nueva auditoría con `"sustituye_a": "AUD-..."`.
- Al completar una auditoría, el script actualiza `primera_auditoria_utc` (si estaba en null) y `ultima_auditoria_utc` del proyecto en el catálogo.

### 3.4 Separación de responsabilidades

La evidencia vive en capas que no se confunden:

| Capa | Archivo | Qué prueba |
|---|---|---|
| **Historia del proyecto** | `data/proyectos/<n>-<slug>/BITACORA.jsonl` | Qué pasó en el proyecto, en orden, firmado. |
| **Ejecución de una auditoría** | `auditorias/<timestamp>/meta.json` | Quién pidió, quién hizo, por qué y qué se encontró. |
| **Resultado de una auditoría** | `auditorias/<timestamp>/reporte.md` | Lectura humana del estado. |
| **Verificación automática** | `auditorias/<timestamp>/manifiesto.json` | Hashes de artefactos, verificables por terceros. |

La bitácora del proyecto **no menciona auditorías** salvo como hito: "se ejecutó la auditoría AUD-..., ver meta.json". El detalle vive en la carpeta de la auditoría.

### 3.5 Migración del proyecto actual

El proyecto que hoy vive en la raíz (STTM mismo) se convierte en la entrada #1 del catálogo y se mueve a `data/proyectos/1-STTM/`. Se registra en bitácora como evento de migración. La bitácora vieja se conserva completa; no se reescribe.

## 4. Consecuencias

### Positivas

- STTM puede auditar **varios proyectos** sin mezclarse.
- Cada auditoría tiene **metadatos de procedencia** (quién pidió, quién hizo), que es lo que cualquier entidad evaluadora o auditor externo espera.
- El catálogo es append-only como la bitácora: coherente con ADR-001.
- El "modo actual" del proyecto ya no vive en un archivo suelto; vive en el catálogo, que es la fuente única.
- Un tercero puede auditar un proyecto del autor usando STTM sin tocar la bitácora del proyecto.

### Aceptadas

- La primera versión no firma `meta.json`. La firma del solicitante y del ejecutor queda como decisión pendiente.
- El catálogo no tiene búsqueda avanzada: para pocos proyectos (decenas) alcanza con leer el JSONL.
- La UI (ADR-002) mostrará un selector de proyecto en la cabecera cuando se implemente.

## 5. Alternativas consideradas

1. **Un proyecto único, múltiples "espacios de trabajo" por auditoría.** Rechazada: confunde proyecto (cosa auditada) con auditoría (acto de auditar).
2. **Base SQLite para el catálogo.** Rechazada como fuente canónica: el JSONL append-only es verificable sin tooling; SQLite queda como índice opcional si el catálogo crece.
3. **Metadatos de auditoría dentro de la bitácora del proyecto.** Rechazada: mezcla la historia del proyecto con el acto de auditarlo, y hace que un tercero no pueda auditar sin contaminar la bitácora.
4. **Firma del solicitante y del ejecutor desde el inicio.** Rechazada: agrega ceremonia de claves que todavía no está definida; se anota como decisión futura cuando STTM tenga usuarios reales además del autor.

## 6. Referencias

- ADR-STTM-001 — Modelo de evidencia, modos y arranque en Termux.
- ADR-STTM-002 — Interfaz de tres niveles y editores de input.
- GOB-STTM-001 — Criterios básicos de arranque.
- Salem Tomo I §2.1 — Opción C y Anillo reservado.
- Salem Tomo II §6 — Modelo de amenazas mínimo (separación de activos).
- ISO/IEC/IEEE 29148:2018 — Requisitos verificables.

## 7. Historial

- v0.1, 2026-09-23: versión inicial del ADR, pendiente de revisión por el autor.
- v0.2, 2026-09-23: terminología neutral (entidad evaluadora); slug de ejemplo sin referencias a entidades reales.
