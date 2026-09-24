# Motivos de la revisión de código y convención de cabeceras

**Fecha:** 2026-09-24
**Estado:** Documentación formal (STTM-0.28, K-009)
**Origen:** Revisión del corazón criptográfico (Capa 1) y convención de cabeceras de autoría.

## Contexto

El 2026-09-24 se realizó una revisión de código por capas de riesgo, empezando por el corazón criptográfico (`firma.py`, `registrar.py`, `verificar.py`). Se identificaron 7 hallazgos (H1-H7), de los cuales 5 se aplicaron como fixes test-first (H1-H5) y 2 se declararon como deuda congelada (H6-H7). Paralelamente, se agregó una convención de cabeceras de autoría en todos los archivos de código.

Este documento registra los motivos detallados de cada hallazgo y de la convención de cabeceras, que habían sido diferidos en el momento de la implementación (entrada #29 de bitácora) para no frenar el avance.

---

## Hallazgos del corazón criptográfico

### H1 — Append no durable en celular (Media-alta)

**Problema:** `registrar.py` escribía con `open("a")` y cerraba sin `flush()` ni `fsync()`. En Termux (Android), un kill del sistema o una batería baja pueden dejar una línea JSON truncada en disco.

**Impacto:** Pérdida del último registro. El verificador aísla el eslabón roto (no arrastra a los siguientes), pero la entrada se pierde y queda ruido permanente en la cadena.

**Fix aplicado:** Agregar `archivo.flush()` y `os.fsync(archivo.fileno())` tras el write.

**Motivo:** En un celular, fsync es la diferencia entre "se guardó" y "creía que se guardó". El costo es una línea de código; el beneficio es durabilidad real ante cortes.

**Test:** `tests/test_h1_fsync.py` verifica que el registro sea durable inmediatamente tras el write.

---

### H2 — Campos nuevos futuros quedan fuera del hash sin avisar (Media)

**Problema:** `CAMPOS_BASE` en `firma.py` congela qué campos cubre el hash. Si alguien agrega un campo nuevo (p.ej. `proyecto_n`, `tags`) y olvida actualizar `CAMPOS_BASE`, ese campo queda **mutable sin detección**: se puede editar sin romper la cadena.

**Impacto:** Silencio peligroso. La cadena sigue verificando, pero el campo nuevo no está protegido.

**Fix aplicado:** Guard en `registrar.py` que verifica que las claves de la entrada sean exactamente `CAMPOS_BASE + {firma, hash}`. Si hay extras o faltantes, falla con estruendo.

**Motivo:** Un campo olvidado en `CAMPOS_BASE` debe romper el registro en el momento de escribir, no en silencio dentro de seis meses cuando alguien edita ese campo y nadie se da cuenta.

**Test:** `tests/test_h2_guard_campos.py` modifica `CAMPOS_BASE` para agregar un campo nuevo y verifica que el registro falle con mensaje claro.

---

### H3 — HMAC con clave por defecto silenciosa (Media)

**Problema:** Si `STTM_HMAC_KEY` no está seteada, `registrar.py` firmaba con `"clave_secreta_temporal"` (escrita en el código) y nadie avisaba. La "firma" no aportaba no-repudio y parecía que sí.

**Impacto:** Falsa sensación de seguridad. Una firma con clave pública no es firma.

**Fix aplicado:** En `registrar.py`, modo `hmac` sin `STTM_HMAC_KEY` falla ruidosamente con mensaje claro. En `verificar.py`, si una entrada HMAC valida con la clave default, se emite aviso: "firma HMAC con clave por defecto: no aporta no-repudio".

**Motivo:** Una firma que no aporta debe declararlo, no fingir. Las entradas viejas con default siguen verificando, pero el aviso deja de mentir sobre su fuerza.

**Test:** `tests/test_h3_hmac_ruidoso.py` verifica que modo `hmac` sin variable de entorno falle con mensaje claro.

**Efecto colateral:** `tests/test_integracion_firma.py` tuvo que actualizarse para setear `STTM_HMAC_KEY` en el entorno del sandbox y firmar la entrada legacy con la misma clave que usa el verificador subprocess. El test viejo codificaba el comportamiento inseguro; se actualizó al contrato nuevo.

---

### H4 — Última entrada sin forma da traceback crudo (Media-baja)

**Problema:** `leer_ultima_entrada()` devolvía la última línea parseada tal cual, y después `ultima["n"]` lanzaba `KeyError` si esa línea era JSON válido pero sin `n` (basura editada a mano).

**Impacto:** Traceback crudo en vez de mensaje humano. El usuario no sabe qué hacer.

**Fix aplicado:** Validar que la última entrada tenga los campos `n` y `hash`. Si no, fallar con mensaje humano: "La última entrada de la bitácora no tiene forma de entrada STTM. Revisá la bitácora antes de registrar."

**Motivo:** Un mensaje humano es más útil que un traceback. El usuario sabe qué hacer: revisar la bitácora.

**Test:** `tests/test_h4_forma_ultima.py` crea una bitácora con última línea JSON válida pero sin campos esperados y verifica que el mensaje sea humano.

---

### H5 — Clave privada con permisos del umask (Baja-media)

**Problema:** `ceremonia_claves()` no fijaba permisos. En Termux el umask da 600 por suerte, no por diseño.

**Impacto:** Dependencia del entorno. En otro sistema, la clave privada podría quedar legible por otros usuarios.

**Fix aplicado:** Agregar `os.chmod(ruta_priv, 0o600)` tras escribir la clave privada.

**Motivo:** Defensa en profundidad. El permiso 600 (solo lectura para el dueño) es el estándar para claves privadas. No depender del umask.

**Test:** `tests/test_h5_chmod_claves.py` verifica que la clave privada tenga permisos 600 tras la ceremonia.

---

### H6 — Append O(n) por registro (Baja, deuda congelada)

**Problema:** `leer_ultima_entrada()` recorre toda la bitácora para encontrar la última entrada. Es O(n) por registro.

**Impacto:** Con 32 entradas es nada. Con 20.000 será notable (~1 segundo por registro).

**Decisión:** Deuda declarada, no se toca. A la escala actual, el costo de optimizar (índice SQLite, caché de última entrada) es mayor que el beneficio. Se revisará si la bitácora supera 10.000 entradas.

**Declaración:** CONTINUIDAD.md §5 (Límites declarados), entrada #30 de bitácora.

---

### H7 — Canonicalización v2 específica de Python (Baja, deuda congelada)

**Problema:** La canonicalización JSON del schema v2 usa `json.dumps` con separadores por defecto de Python (`, ` y `: `). Es reproducible en Python, pero un verificador en otro lenguaje (Rust, Go, JavaScript) tendría que replicar esos separadores exactos.

**Impacto:** Un verificador externo no-Python no puede verificar entradas v2 sin conocer los separadores exactos de Python.

**Decisión:** Deuda declarada, no se toca. Cambiar separadores hoy rompería todos los hashes futuros como un incidente 001 repetido. Si algún día hace falta un verificador externo, se abrirá schema v3 con separadores explícitos, conservando v2 para la historia.

**Declaración:** CONTINUIDAD.md §5 (Límites declarados), entrada #30 de bitácora.

---

## Convención de cabeceras de autoría

**Problema:** Los archivos de código no tenían cabecera con el nombre del autor. Cuando un archivo sale del repo (un reporte, un anexo, un fork), la procedencia se pierde.

**Decisión:** Agregar cabecera con nombre del autor y SPDX-License-Identifier en todos los archivos de código (.py, .js, .css, .html).

**Formato:**
- Python: `# Creado por Martín José Dalberto, Argentina, 2026.` + `# SPDX-License-Identifier: MIT`
- JS/CSS: `/* Creado por Martín José Dalberto, Argentina, 2026. SPDX-License-Identifier: MIT */`
- HTML: `<!-- Creado por Martín José Dalberto, Argentina, 2026. SPDX-License-Identifier: MIT -->`

**Motivo:** La procedencia viaja con el archivo. Cuando un `.py` sale del repo, el ledger no viaja con él, pero la cabecera sí. Es trazabilidad a nivel de archivo, complementaria del ledger a nivel de proyecto.

**Costo:** Bajo. Un solo commit tocando ~25 archivos, solo líneas de comentario. Cero cambio de comportamiento.

**Enforcement:** Test `tests/test_convencion_cabeceras.py` recorre el repo y falla si algún archivo de código nace sin cabecera. La convención no depende de acordarse: la enforced el test.

**Privacidad:** El nombre del autor ya es público en el repo (README, LICENSE, commits, sitio web). La cabecera no expone nada nuevo. La regla de neutralidad de STTM es sobre financiadores y entidades objetivo, no sobre el autor.

**Lección:** La procedencia viaja con el archivo. Un método de trazabilidad debe aplicar su propia lógica a sus propios artefactos.

---

## Lecciones de método

1. **Test-first siempre:** Los 5 fixes se aplicaron con test primero (rojo), fix, verde. Eso garantiza que el fix resuelve el problema real, no uno imaginado.

2. **Efectos colaterales documentados:** El fix de H3 rompió un test viejo que codificaba el comportamiento inseguro. Se actualizó el test al contrato nuevo, no se revirtió el fix.

3. **Deudas declaradas, no escondidas:** H6 y H7 son deudas reales, pero declaradas por escrito en CONTINUIDAD.md y en la bitácora. No son sorpresas futuras.

4. **Compuertas de calidad:** Antes de commitear, la suite completa debe estar verde. Si no, no se toca el repo.

5. **Honestidad técnica:** Un documento de trazabilidad no puede contener inventos. La primera versión del documento de modos de gobernanza tenía afirmaciones no verificadas; se reescribió con solo lo verificable.

---

## Referencias

- Entrada #29 de bitácora: "Cierre de PC-013 y convención de cabeceras de autoría; motivos diferidos a K-009"
- Entrada #30 de bitácora: "Endurecimiento del corazón criptográfico: cinco fixes de la revisión de código (H1-H5)"
- Entrada #31 de bitácora: "K-003 cerrada: validación manual de UI declarada formalmente"
- Tests: `tests/test_h1_fsync.py`, `tests/test_h2_guard_campos.py`, `tests/test_h3_hmac_ruidoso.py`, `tests/test_h4_forma_ultima.py`, `tests/test_h5_chmod_claves.py`, `tests/test_convencion_cabeceras.py`
- CONTINUIDAD.md §5 (Límites declarados)

---
*Documento registrado en la bitácora del proyecto (entrada de STTM-0.28).*
