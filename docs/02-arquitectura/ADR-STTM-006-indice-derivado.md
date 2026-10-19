# ADR-STTM-006 — Índice SQLite derivado (nunca fuente de verdad)

**SALEM**
**STTM — ADR-006: ÍNDICE SQLITE DERIVADO**
Borrador de trabajo interno

Argentina, 2026

## 1. Control documental

| Dato | Definición |
|---|---|
| Identificador | STTM-ADR-006-2026-R1 |
| Estado | Borrador de trabajo interno, pendiente de revisión |
| Alcance | Agrega una capa de índice SQLite+FTS5 para búsqueda rápida, sin cambiar dónde vive la fuente de verdad. |
| Antecedentes | Deuda declarada H6 (v0.3); ADR-STTM-001 (modelo de evidencia). |

## 2. Contexto

`BITACORA.jsonl` como append-only es la garantía central de inmutabilidad de STTM, pero como mecanismo de *consulta* es O(n): buscar una palabra o filtrar por fecha implica leer y parsear el archivo entero, línea por línea, cada vez. Para un ledger de cientos o miles de entradas esto deja de ser instantáneo. La tentación obvia — mover la bitácora a una base de datos relacional — rompería la propiedad que la hace confiable: un archivo de texto plano, append-only, que cualquiera puede leer y verificar sin un motor de base de datos de por medio.

## 3. Decisión

El JSONL sigue siendo la única fuente de verdad, siempre. `indice.py` construye una tabla SQLite (con una tabla virtual FTS5 para texto libre) **derivada** del JSONL, pensada exclusivamente para acelerar consultas — nunca para decidir integridad. Principio de diseño explícito: **el índice se puede borrar en cualquier momento sin perder nada**; `reconstruir()` lo repuebla desde cero.

## 4. Consecuencias

- `/api/buscar` reconstruye el índice en cada consulta antes de buscar (prioriza correctitud/frescura sobre velocidad en esta versión — ver §5 para cuándo esto deja de alcanzar).
- El índice tolera líneas corruptas del JSONL sin romperse (las ignora silenciosamente): juzgar si una línea corrupta es un problema de integridad es responsabilidad exclusiva de `verificar.py`, nunca del índice.
- Se encontró y corrigió, durante la integración de este ADR, un problema real: la sintaxis de consultas de FTS5 trata `-` como operador NOT, así que un texto libre con guiones (por ejemplo, un identificador tipo "Ref-STTM-004") rompía la búsqueda sin avisar por qué. `indice.py` sanitiza la consulta (extrae palabras, ignora puntuación) antes de pasarla a FTS5, para que quien busca no necesite conocer esa sintaxis.

## 5. Límites declarados

- Reconstruir el índice en cada request a `/api/buscar` es correcto pero no escala indefinidamente: para un ledger muy grande (decenas de miles de entradas), esto debería moverse a un job periódico (cron) que reconstruya cada tanto, aceptando una ventana de "casi al día" en vez de "siempre exacto al segundo". Ver INSTALACION.md para el cron sugerido — no implementado en esta versión, declarado como el paso obvio siguiente si el volumen lo justifica.
- El índice no valida firmas ni hashes. Nunca reemplaza a `verificar.py`.
