# ADR-STTM-002 — Interfaz de tres niveles y editores de input

**SALEM**  
**STTM — ADR-002: INTERFAZ DE TRES NIVELES Y EDITORES DE INPUT**  
Borrador de trabajo interno  

Autor del proyecto  
Martín José Dalberto  
Argentina, 2026  

## 1. Control documental

| Dato | Definición |
|---|---|
| Identificador | STTM-ADR-002-2026-R1 |
| Estado | Borrador de trabajo interno, pendiente de revisión |
| Alcance | Define los tres modos de interfaz de STTM, qué campos y flujos habilita cada uno, cómo se ve el editor de input en móvil, y cómo persiste la selección de modo. |
| Autor | Martín José Dalberto, Argentina. |
| Antecedentes | ADR-STTM-001 (modelo de evidencia y modos); ADR-STTM-003 (catálogo de proyectos y auditorías); GOB-STTM-001 (criterios básicos); CONTINUIDAD.md de STTM; Tomo I y Tomo II de Salem (principios de evidencia antes que publicidad, local-first, honestidad técnica). |

Declaración de alcance. Este ADR establece decisiones de diseño de interfaz. No implementa todavía editores, no define paleta de colores final (pendiente de actualización del documento de identidad Capa 2), y no toca el núcleo criptográfico.

## 2. Contexto

STTM nació con tres modos conceptuales (ADR-001):

- **Registro Simple** — bitácora + visualización + copiado.
- **Continuidad** — agrega documentos de estado, índice y handoff.
- **Salem** — trazabilidad completa con GOBs, ADRs, tests y auditoría.

Hasta hoy, esos modos existen como texto. La interfaz actual (`web/index.html`) es un visor único que muestra bitácora y documentos por igual, sin distinción por modo. Esto genera tres problemas:

1. **Una entidad evaluadora** ve campos avanzados que no le interesan.
2. **Un investigador independiente** que clona el repo no sabe por dónde empezar.
3. **Un colaborador futuro** no tiene claro qué nivel de ceremonia se le pide según el modo.

Además, la interfaz actual es de **solo lectura**: no hay editor de input para registrar nuevas entradas, crear documentos o ejecutar auditorías desde el navegador. Todo pasa por la terminal.

Este ADR define la interfaz de tres niveles y los editores de input mínimos para cada uno, en coherencia con los principios Salem:

- **Evidencia antes que publicidad** (Tomo I §1): nada se muestra si no está implementado.
- **Inclusión pedagógica** (Tomo II §2): mensajes explican qué ocurrió, dónde y qué sigue.
- **Local-first** (Tomo II §2): toda la UI corre en loopback, sin servicios externos.
- **Personas antes que automatismo** (Tomo II §2): la UI propone, la persona decide.

## 3. Decisión

### 3.1 Los tres niveles de interfaz

La interfaz tendrá un **selector de modo persistente** en la cabecera, con tres opciones:

```text
[ Simple ]  [ Continuidad ]  [ Salem ]
```

El modo seleccionado se guarda en el catálogo de proyectos definido por ADR-STTM-003 (campo `nivel_actual` en `data/proyectos.jsonl`). Mientras el catálogo no esté implementado, la interfaz lee `data/proyecto.json` como fuente provisoria. Por defecto: **Simple**.

Cada modo habilita un subconjunto estricto de capacidades:

| Capacidad | Simple | Continuidad | Salem |
|---|:---:|:---:|:---:|
| Ver bitácora | ✅ | ✅ | ✅ |
| Copiar hash/detalle/JSON | ✅ | ✅ | ✅ |
| Registrar entrada nueva | ✅ | ✅ | ✅ |
| Ver documentos | — | ✅ | ✅ |
| Crear/editar documento | — | ✅ | ✅ |
| Ver documento de continuidad | — | ✅ | ✅ |
| Actualizar continuidad | — | ✅ | ✅ |
| Ver reportes de auditoría | — | — | ✅ |
| Preparar auditoría | — | — | ✅ |
| Ver matriz de trazabilidad | — | — | ✅ |
| Crear GOB / ADR | — | — | ✅ |
| Ejecutar tests | — | — | ✅ |
| Cambiar modo del proyecto | ✅ | ✅ | ✅ |

**Regla de honestidad visual:** si una capacidad está deshabilitada para el modo actual, no se muestra (no se muestra tachada ni gris, porque eso sería prometer algo que no está activo). Es la misma regla del Anillo reservado en Tomo I §2.1 y Tomo II §3.3: lo que no está integrado, no aparece como activo.

### 3.2 Editor de registro (disponible en los 3 modos)

El editor de registro es el único que existe en los tres niveles. Debe ser **touch-friendly** y **responsive**, porque el autor trabaja desde móvil.

Campos del formulario:

| Campo | Obligatorio | Tipo | Ayuda |
|---|---|---|---|
| Título | sí | texto corto | "Ej: Inicio del experimento 001" |
| Detalle | sí | texto extenso | "Descripción de lo que pasó, por qué importa y qué se espera después." |
| Archivos afectados | no | texto, separado por comas | "Ej: docs/GOB-001.md, scripts/registrar.py" |
| Commit relacionado | no | texto corto | "Hash corto de Git, si existe." |
| Modo de firma | sí | selector | "hash · hmac · ed25519" |

Comportamiento:

- Al guardar, llama al endpoint `/api/registrar` del servidor local.
- El servidor corre `scripts/registrar.py` con los parámetros correspondientes.
- Devuelve el resultado (número de entrada, hash corto, estado).
- La interfaz actualiza la lista sin recargar toda la página.
- Si falla, muestra **qué ocurrió, por qué y qué sigue** (Tomo II §2).

### 3.3 Editor de documentos (modo Continuidad y Salem)

Disponible solo cuando el modo es Continuidad o Salem.

Funcionalidad mínima:

- Lista de documentos Markdown (misma API `/api/documentos`).
- Botón "Crear documento" que abre un formulario con:
  - Tipo (GOB, ADR, continuidad, readme, otro).
  - Título.
  - Cuerpo (textarea con Markdown crudo, sin render en vivo todavía).
- Botón "Editar" sobre cada documento existente.
- Al guardar, la API escribe el archivo y registra una entrada de bitácora automáticamente (la regla Salem: toda acción relevante queda registrada).

**No se promete render Markdown en vivo** en la primera versión. El visor actual usa `<pre>` para mostrar el texto crudo. Eso es honesto: no anunciamos un editor WYSIWYG si no lo tenemos.

### 3.4 Panel de auditoría (solo modo Salem)

Disponible solo cuando el modo es Salem.

Tres botones alineados con lo ya diseñado:

```text
[ Preparar auditoría ]   [ Generar informe ]   [ Verificar paquete ]
```

Cada botón llama al endpoint correspondiente y muestra:

- Estado de la cadena (íntegra / rota).
- Cantidad de alertas rojas / amarillas.
- Ruta del reporte generado.
- Botón para abrir el reporte.

**No se promete exportación a GitHub** en la primera versión. El botón "Exportar para GitHub" queda fuera de esta iteración y se anota como decisión pendiente.

### 3.5 Cambio de modo

El selector de modo en la cabecera tiene un comportamiento explícito:

- Al cambiar de modo, la interfaz pregunta:  
  "¿Actualizar el proyecto a modo **Continuidad**? Esto habilitará campos adicionales en futuras entradas."
- Si el usuario confirma, se actualiza el nivel en el catálogo (ADR-003) o en `data/proyecto.json` mientras el catálogo no exista, y se registra la entrada de bitácora:  
  "Cambio de modo: Simple → Continuidad."
- La interfaz se recarga mostrando las capacidades del nuevo modo.

Esto evita cambios silenciosos y deja traza de cada decisión.

## 4. Persistencia del modo

Fuente definitiva (ADR-STTM-003): campo `nivel_actual` del catálogo `data/proyectos.jsonl`; cada cambio de nivel se registra además en la bitácora del proyecto.

Fuente provisoria hasta implementar el catálogo: `data/proyecto.json` con esta estructura mínima:

```json
{
  "nombre": "demo-publico",
  "modo": "simple",
  "gob_obligatorio": false,
  "continuidad_obligatoria": false,
  "actualizado_utc": "2026-09-23T18:30:00Z"
}
```

El servidor lo lee al arrancar y lo expone en `/api/proyecto`. La interfaz lo consume para decidir qué mostrar. Cuando el catálogo exista, este archivo se elimina y su contenido migra al catálogo (se registra en bitácora).

## 5. Consecuencias

### Positivas

- Una entidad evaluadora ve una interfaz acorde al nivel que necesita.
- El dogfooding es posible: el proyecto STTM puede usar su propio Modo Salem para desarrollarse.
- Los tres modos quedan consistentes entre documentación, núcleo y UI.
- La regla "nada se anuncia si no está activo" se aplica también a la interfaz.

### Aceptadas

- La primera versión no tiene render Markdown en vivo.
- La primera versión no exporta a GitHub desde la UI.
- El editor de documentos es Markdown crudo, no WYSIWYG.
- La capa visual final queda pendiente del documento de identidad Capa 2 actualizado por el autor.

## 6. Alternativas consideradas

1. **Interfaz única con todos los campos visibles.** Rechazada: abruma al público y contradice el principio de evidencia antes que publicidad.
2. **Tres aplicaciones separadas (una por modo).** Rechazada: triplica mantenimiento y rompe la unidad del método.
3. **Modo único con "perfiles" por usuario.** Rechazada: confunde perfiles personales con niveles de gobernanza del proyecto.
4. **Editor WYSIWYG Markdown desde el inicio.** Rechazada: no existe en stdlib, requeriría dependencia externa, y no es crítico para el método.

## 7. Referencias

- ADR-STTM-001 — Modelo de evidencia, modos y arranque en Termux.
- ADR-STTM-003 — Catálogo de proyectos y registro de auditorías.
- GOB-STTM-001 — Criterios básicos de arranque.
- CONTINUIDAD.md de STTM.
- Salem Tomo I §2.1 — Opción C y Anillo reservado.
- Salem Tomo II §2 — Principios arquitectónicos no negociables.
- Salem Tomo II §3.3 — Estado real del Anillo (no operativo hasta R20-35 a R20-39).
- Plantilla de Documento Salem (SEA-SALEM-[SIGLAS]-[VERSIÓN]-2026-R1).

## 8. Historial

- v0.1, 2026-09-23: versión inicial del ADR, pendiente de revisión.
- v0.2, 2026-09-23: terminología neutral (entidad evaluadora); persistencia de modo apuntada al catálogo de ADR-003.
