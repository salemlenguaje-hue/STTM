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



### K-006 — Actualización del documento de identidad Capa 2
**Prioridad:** baja. **Responsable:** autor (Martín).
**Aceptación:** documento actualizado en la carpeta de la empresa + entrada
de bitácora que deje constancia de la nueva versión.

---


---


---

### Panel de Ayuda implementado (2026-09-25)
**Evidencia:** entrada #38 de bitácora y commit STTM-0.33. Documento
`docs/05-ui/AYUDA.md` orientado a usuarios finales con explicación de
modos, instrucciones paso a paso, problemas comunes (PC-001, PC-002,
PC-009, PC-010, PC-011, PC-013) en lenguaje de usuario, exportar/compartir
y preguntas frecuentes. Reemplaza el uso de `PUNTOS-CRITICOS-UX.md`
(técnico) en el panel de ayuda de la UI.

### Revisión del servidor (Capa 2) cerrada (2026-09-25)
**Evidencia:** entrada #39 de bitácora y commit STTM-0.34. Cuatro fixes
de robustez aplicados: H2 (límite JSON 10MB), H3 (límite documento 5MB),
H4 (sanitizar stderr), H5 (timeout subprocess 30s). Suite completa: 74
tests verdes. H1 (CORS/CSRF en --movil) declarado como deuda documentada
(usuario confirmó loopback puro, riesgo teórico).

### Revisión de auditar.py (Capa 3) cerrada (2026-09-25)
**Evidencia:** entrada #40 de bitácora y commit STTM-0.35. Dos fixes
aplicados: A1 (bitácora explícita en main), A2 (gitignore con negación
y **). Suite completa: 76 tests verdes. A3-A5 declarados como deuda
documentada.

### Revisión de proyectos.py (Capa 4) cerrada (2026-09-25)
**Evidencia:** entrada #41 de bitácora y commit STTM-0.36. Cuatro fixes
aplicados: P3 (validación ref CLI), P4 (unicidad ref CLI), P1 (catálogo
tolerante a corrupción), P2 (fsync en agregar). Suite completa: 89 tests
verdes. P5-P7 declarados como deuda documentada.

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


### K-001 — Selector de proyecto en la UI
**Evidencia:** entrada #25 de bitácora y commit STTM-0.21. Selector en
cabecera con 2+ proyectos reales (#1 STTM, #2 DEMO); al cambiar, cambian
bitácora y auditorías (documentos quedan globales: divergencia declarada
con la visión ADR-003). Tests de endpoint: test_k001_selector.py (4) y
salud de input test_salud_input.py (8). Validado en dispositivo real:
entrada creada desde la UI en el proyecto #2 y prueba móvil del PC-011.

### K-002 — Migración de la bitácora a data/proyectos/1-STTM/
**Evidencia:** entrada #24 de bitácora y commit STTM-0.20. Tests de paridad
tests/test_k002_ubicacion.py: 3 rojos antes de migrar, 3 verdes después sin
tocar el archivo de test. Backup pre-migración con SHA-256 en data/backups/.
scripts/rutas.py como fuente única de verdad; 3 scripts y 4 tests parcheados;
git mv preservó el historial. 43 tests verdes; verificación íntegra desde la
ruta nueva.

### K-003 — Tests de render de UI o declaración formal de validación manual
**Evidencia:** entrada #31 de bitácora y commit STTM-0.26. Declaración formal
en docs/05-ui/VALIDACION-MANUAL-UI.md: la UI se valida manualmente en
dispositivo real (no tests automatizados de render). Motivo: headless
browser rompería el principio de stdlib únicamente y agregaría complejidad
sin valor proporcional. Checklist de 8 puntos, frecuencia por commit,
criterios de revisión declarados.

### K-004 — Registro de documentos estilo GOB-005
**Evidencia:** entrada #36 de bitácora y commit STTM-0.31. Documento
docs/00-gobernanza/REGISTRO-DOCS.md que lista cada documento vivo del
proyecto con ID, tipo, título, enlace, estado y responsable. Generado
automáticamente recorriendo el repo; convenciones de ID declaradas.

### K-005 — Anclaje público de la clave Ed25519
**Evidencia:** entrada #21 de bitácora, commit STTM-0.16 y
docs/06-seguridad/ANCLAJE-CLAVE-ED25519.md con fingerprint SHA-256.
CI verifica ed25519 completo desde ese commit.
**Pendiente derivado cerrado:** testigo #1 (email Gmail, 2026-09-23
18:10) asentado en entrada #23; testigo #2 (sello OpenTimestamps, 18:43)
en entrada #22 y en el repo; upgrade de Bitcoin completado el 2026-09-24
(ots upgrade con atestaciones de bob, alice y finney), archivo .ots
completo y verificable.

---
*Tablero vivo. Se actualiza en el mismo commit que el trabajo que mueve tarjetas.*

### K-007 — Crear proyecto desde la UI
**Evidencia:** entrada #28 de bitácora y commit STTM-0.23. Endpoint POST
/api/proyecto/crear con validación de ref única (409 si duplicada, 400 si
inválida o título vacío); UI con botón '+ Proyecto', formulario modal y
confirmación explícita; asiento en bitácora tras creación. Addendum 3.6 al
ADR-003. Tests: test_k007_crear.py (5). Suite completa 60 tests verdes.
PC-012 mitigado: el selector ofrece creación real.

### K-009 — Pase de documentación: motivos de la revisión de código y de las cabeceras
**Evidencia:** entrada #33 de bitácora y commit STTM-0.28. Documento
docs/02-arquitectura/MOTIVOS-REVISION-CODIGO.md con motivos detallados de
los 7 hallazgos de la revisión del corazón criptográfico (H1-H7) y de la
convención de cabeceras de autoría. H1-H5 aplicados con test-first,
H6-H7 declarados como deuda congelada. Lecciones de método documentadas.
