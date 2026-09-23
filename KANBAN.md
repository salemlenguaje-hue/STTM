# KANBAN — STTM

**Propósito:** Seguimiento liviano del trabajo pendiente, en curso y hecho del
proyecto. Inspirado en el kanban PDCA de Sofía Salem, adaptado a STTM:
cada tarjeta es un compromiso verificable, no un post-it.

**Reglas del tablero:**
1. No existe tarjeta sin criterio de aceptación verificable.
2. Una tarjeta solo pasa a "Hecho" con evidencia: entrada de bitácora y/o
   commit referenciados en la propia tarjeta.
3. El kanban se actualiza en el mismo commit que el trabajo que mueve la tarjeta.
4. Tarjeta cerrada sin evidencia vuelve a "Pendientes" con nota (honestidad aplicada).
5. IDs estables: K-0## para pendientes comprometidas, K-1## para backlog.

---

## En curso

(Sin tarjetas en este momento.)

---

## Pendientes (próximos pasos comprometidos)

### K-001 — Selector de proyecto en la UI
**Prioridad:** media.
**Dependencia:** al menos un segundo proyecto activo en el catálogo.
**Aceptación:** selector activo en cabecera con 2+ proyectos; al cambiar,
cambian bitácora, documentos y auditorías vistas; 1+ test de endpoint
cubriendo la selección.

### K-002 — Migrar la bitácora a data/proyectos/1-STTM/
**Prioridad:** media-alta. Hacer ANTES que K-001 para no multiplicar rutas.
**Dependencia:** decisión de rutas de lectura en registrar/verificar/auditar/servidor.
**Aceptación:** bitácora única en la nueva ubicación; scripts y servidor la
leen desde ahí; verificación íntegra desde la ruta nueva; migración
registrada en bitácora; sin archivos duplicados.

### K-003 — Tests de render de UI o declaración formal de validación manual
**Prioridad:** baja.
**Aceptación:** tests/test_ui_render.py verde en CI, o entrada de bitácora
que declare la validación manual como decisión aceptada, con motivo y
frecuencia de revisión.

### K-004 — Registro de documentos estilo GOB-005
**Prioridad:** baja.
**Aceptación:** docs/00-gobernanza/REGISTRO-DOCS.md listando cada documento
vivo con ID, versión, estado, responsable y enlace.

### K-005 — Decisión de anclaje público de la clave Ed25519
**Prioridad:** alta (confianza externa).
**Aceptación:** ADR o entrada de bitácora con la decisión (anclar o no) y su
motivo. Si se ancla: clave pública en el repo, CI verificando con ella y
desaparición del aviso "clave pública ausente".

### K-006 — Actualización del documento de identidad Capa 2
**Prioridad:** baja. **Responsable:** autor (Martín).
**Aceptación:** documento actualizado en la carpeta de la empresa + entrada
de bitácora que deje constancia de la nueva versión.

---

## Backlog (ideas sin compromiso)

### K-101 — Paper público del método
Documento con evidencia verificable de STTM para evaluadores externos.

### K-102 — Índice SQLite opcional para catálogo grande
Alternativa 2 del ADR-003; solo si el catálogo supera decenas de proyectos.

### K-103 — Firma de meta.json por solicitante y ejecutor
Decisión pendiente del ADR-003; requiere ceremonia de claves para actores externos.

### K-104 — Render Markdown en el visor
No prometido en ADR-002; solo si aparece necesidad real repetida.

### K-105 — Export de paquete de auditoría (.zip)
Carpeta con reporte + meta + manifiesto + bitácora exportada, para
evaluadores externos.

---

## Hecho (con evidencia)

### K-000 — Crear KANBAN.md y adoptar las reglas del tablero
**Evidencia:** entrada #20 de bitácora y commit STTM-0.15.

---
*Tablero vivo. Se actualiza en el mismo commit que el trabajo que mueve tarjetas.*
