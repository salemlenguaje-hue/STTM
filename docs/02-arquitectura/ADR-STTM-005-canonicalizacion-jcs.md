# ADR-STTM-005 — Canonicalización JCS (RFC 8785)

**SALEM**
**STTM — ADR-005: CANONICALIZACIÓN JCS (RFC 8785)**
Borrador de trabajo interno

Argentina, 2026

## 1. Control documental

| Dato | Definición |
|---|---|
| Identificador | STTM-ADR-005-2026-R1 |
| Estado | Borrador de trabajo interno, pendiente de revisión |
| Alcance | Reemplaza la serialización específica de Python (`json.dumps(sort_keys=True)`) por RFC 8785 (JSON Canonicalization Scheme) para el cálculo de hash y firma del schema v3. |
| Antecedentes | Deuda declarada H7 (v0.3); ADR-STTM-001 (modelo de evidencia). |

## 2. Contexto

STTM v0.3 calculaba el hash de contenido de cada entrada con `json.dumps(datos, sort_keys=True, ensure_ascii=False)`. Esto es determinístico *dentro de Python* — la misma entrada, en la misma versión de Python, siempre produce el mismo texto — pero no es un estándar interoperable. La propuesta central de STTM es "cualquiera puede verificar esta cadena, sin confiar en este código en particular". Un verificador independiente escrito en Go, Rust, o JavaScript no tiene ninguna garantía de replicar byte a byte el comportamiento del serializador de CPython sin, en los hechos, reimplementar las particularidades de esa versión de Python.

## 3. Decisión

Adoptar RFC 8785 (JSON Canonicalization Scheme, JCS) para el schema v3: una única representación textual posible para un valor JSON dado, definida por el IETF e independiente de lenguaje. `canon.py` implementa el subconjunto de JCS que STTM necesita (objetos, arrays, strings, enteros, booleanos, null — sin floats, ver §5).

## 4. Consecuencias

- Las entradas v1/v2 (histórico) siguen verificándose con la fórmula original: este ADR no reescribe el pasado, coexiste con él (`verificar.py` reconoce los tres schemas).
- Cualquier implementación conforme a RFC 8785 en cualquier lenguaje puede recalcular el hash de una entrada v3 y obtener el mismo resultado, sin depender de `canon.py`.
- El campo `actor` (ver ADR-004) entra al cálculo de hash desde v3: si alguien edita a mano el archivo para cambiar quién dice haber hecho algo, el hash cambia y `verificar.py` lo detecta como alteración de contenido.

## 5. Límites declarados

- No se admiten valores `float` en campos firmables: la forma canónica de float en JCS (algoritmo ECMAScript de Number-to-String) es una fuente conocida de bugs de interoperabilidad entre implementaciones, y STTM no tiene necesidad real de floats en estos campos. Se rechaza explícitamente (`TypeError`) en vez de serializar de forma potencialmente no-portable en silencio.
- La implementación cubre el subconjunto de JCS que las entradas de STTM usan; no es un serializador JCS de propósito general y no se ofrece como tal fuera de este proyecto.
