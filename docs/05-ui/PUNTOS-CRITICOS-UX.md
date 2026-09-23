# PUNTOS CRÍTICOS DE UX — Visor STTM

**Propósito:** Registro vivo de fricciones, confusiones y riesgos de usabilidad
detectados durante la implementación de ADR-002. Este documento es la fuente
de contenido del panel de Ayuda que se integrará antes de finalizar el proyecto.

**Regla:** cada punto crítico observado se anota acá en el momento, con su
estado (abierto / mitigado / resuelto) y su mitigación si la tiene.

---

## PC-001 — Copiado en contextos no seguros
**Estado:** Resuelto (técnica), pendiente de explicación en Ayuda.
**Observación:** `navigator.clipboard` no existe fuera de https/localhost.
Desde la IP de red en http, los botones de copiado fallaban en silencio.
**Mitigación:** copiado en 3 capas (API moderna → execCommand → overlay manual).
El botón informa qué método usó ("¡Copiado!" vs "Copiado (compat.)").
**Para la Ayuda:** explicar por qué a veces dice "compat." y qué hacer si
aparece el overlay de copiado manual.

## PC-002 — Cache del navegador muestra UI vieja
**Estado:** Mitigado (manual), pendiente de explicación en Ayuda.
**Observación:** tras actualizar style.css/app.js, Chrome seguía mostrando
la versión anterior. Hubo que usar pestaña de incógnito varias veces.
**Mitigación provisoria:** incógnito o recarga forzada.
**Para la Ayuda:** avisar que si la interfaz "no cambió", probar incógnito.

## PC-003 — Cambios de modo no deben ser silenciosos
**Estado:** Abierto (se implementa en Fase 2).
**Observación:** cambiar el nivel del proyecto habilita o deshabilita
capacidades. Un clic accidental no debe reconfigurar el proyecto.
**Mitigación prevista (ADR-002 §3.5):** diálogo de confirmación explícito
antes de aplicar el cambio, con registro en bitácora.

## PC-004 — Formularios en pantalla táctil chica
**Estado:** Abierto (observar en Fase 4).
**Observación prevista:** el teclado táctil puede tapar el botón de guardar;
los campos largos (detalle, cuerpo de documento) necesitan altura mínima
y scroll interno.
**Mitigación prevista:** botones fijos arriba del formulario, textareas con
altura mínima, probar en celular real en Fase 4.

## PC-005 — Regla de honestidad visual vs. descubribilidad
**Estado:** Abierto (decisión de diseño en Fase 2).
**Observación:** ADR-002 prohíbe mostrar capacidades deshabilitadas (nada de
botones grises). Riesgo: el usuario de modo Simple no sabe que existen
modos superiores.
**Mitigación prevista:** el selector de modo SIEMPRE visible (es una
capacidad de todos los modos), y la Ayuda explica qué agrega cada nivel.

---

## Historial
- 2026-09-23: creación del documento con PC-001 a PC-005 iniciales.

## PC-006 — Reporte de auditoría no se muestra
**Estado:** Resuelto (bug de parseo de JSON).
**Observación:** El botón "Ver reporte" en la vista de auditorías no mostraba nada. El endpoint `/api/reporte` devolvía JSON válido, pero el JavaScript no lo parseaba correctamente.
**Diagnóstico:** El código usaba `fetchJSON()` que ya parsea el JSON, pero luego intentaba acceder a `reporte.contenido` como si fuera texto plano. El endpoint devuelve `{"carpeta": "...", "contenido": "..."}`, así que `reporte.contenido` es correcto, pero había un bug en cómo se renderizaba el HTML.
**Mitigación:** Corregir el renderizado del reporte y la verificación de paquete en el visor de auditoría.
**Para la Ayuda:** si un reporte no se muestra, recargar la página (puede ser cache del navegador).

## PC-007 — Imagen del equipo no aparece en el hero
**Estado:** Resuelto.
**Observación:** El visor no mostraba la ilustración del equipo de auditoría (sttm-equipo.png) en el hero.
**Diagnóstico:** El HTML v2 generado en la Fase 2 no incluía el elemento `<section class="hero">` con la imagen.
**Mitigación:** Agregar el hero con la imagen después del header en index.html.
**Para la Ayuda:** la imagen del equipo es puramente decorativa; si no carga, el visor sigue funcionando.

---

## Historial actualizado
- 2026-09-23: PC-006 (reporte de auditoría) y PC-007 (imagen del equipo) detectados y resueltos en Fase 2.

## PC-009 — Auditorías previas a ADR-003 rompían la lista (undefined 'rojos')
**Estado:** Resuelto.
**Observación:** Al entrar en modo Salem, mensaje rojo: "Error al cargar
auditorías: Cannot read properties of undefined (reading 'rojos')".
**Diagnóstico:** las tres auditorías anteriores a ADR-003 no tienen
meta.json; el endpoint las devolvía sin campo hallazgos y el render leía
aud.hallazgos.rojos sin guard. Un solo elemento sin datos tumbaba toda la
lista (patrón PC-006 hermano: datos ausentes no manejados).
**Mitigación:** el endpoint declara sin_meta=true (no inventa datos) y el
render muestra 📜 con la leyenda "auditoría previa al schema de metadatos".
Guard equivalente para manifiesto=null en el visor de paquete.
**Lección:** en listas heterogéneas (historial largo), cada campo opcional
necesita un estado visual propio; lo ausente se declara, no se colapsa.

---

## Historial actualizado
- 2026-09-23: PC-009 documentado y resuelto.

## MEJ-001 — Exportar reporte y/o enviar por email o WhatsApp
**Estado:** Implementado (3 niveles de degradación honesta).
**Solicitud:** durante la prueba de UI del 2026-09-23, el autor pidió
poder exportar el reporte de auditoría y/o enviarlo por email o WhatsApp.
**Diseño:** ver ADR-002 §3.6 (addendum v0.3). Descarga .md siempre;
Web Share con archivo en móviles; menú mailto/wa.me con resumen como
último nivel. El servidor nunca sube evidencia a terceros.
**Para la Ayuda:** explicar que por límites de los mensajeros solo viaja
el resumen; el reporte completo se descarga y se adjunta manualmente.

## PC-010 — Mojibake al abrir el reporte descargado en visores de Android
**Estado:** Resuelto (BOM UTF-8).
**Observación:** el .md descargado se abía con caracteres rotos
("AuditorÃ­a", "âœ…") en visores que asumen Latin-1/Windows-1252.
**Diagnóstico:** los bytes siempre fueron UTF-8 válidos; el visor no
tenía pista de codificación. WhatsApp, email y la UI no se afectaban
porque ahí el texto viaja como string, no como archivo.
**Mitigación:** BOM UTF-8 al inicio del Blob descargado y del File
compartido. Es la pista estándar que esos visores necesitan.
**Lección:** un archivo correcto puede parecer roto si le falta la
etiqueta de codificación que su consumidor espera.

---

## Historial actualizado
- 2026-09-23: PC-010 documentado y resuelto. Cierre del ciclo ADR-002.
