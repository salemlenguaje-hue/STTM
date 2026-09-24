# Registro de documentos vivos

**Fecha de generación:** 2026-09-25
**Estado:** Registro formal (STTM-0.31, K-004)
**Método de generación:** Script que recorre el repo y extrae metadata de cada .md.

## Propósito

Este documento lista todos los documentos vivos del proyecto STTM con su ID, versión, estado, responsable y enlace. Es el índice maestro de la documentación del proyecto.

## Convenciones de ID

- **ADR-STTM-xxx**: Architecture Decision Records (decisiones de arquitectura).
- **GOB-STTM-xxx**: Documentos de gobernanza (políticas, reglas).
- **DOC-xxx**: Documentos sin ID formal (guías, notas, registros).

Los IDs son estables: una vez asignados, no cambian.

## Registro

| ID | Tipo | Título | Enlace | Estado | Responsable |
|---|---|---|---|---|---|
| DOC-001 | DOC | STTM — Salem Traceability & Trust Method | `README.md` | Activo | Autor |
| DOC-002 | DOC | CONTINUIDAD — Proyecto STTM | `CONTINUIDAD.md` | Activo | Autor |
| DOC-003 | DOC | KANBAN — STTM | `KANBAN.md` | Activo | Autor |
| DOC-004 | DOC | LICENSE | `LICENSE` | Activo | Autor |
| DOC-005 | DOC | Documentation License — CC-BY 4.0 | `LICENSE-DOCS.md` | Activo | Autor |
| GOB-STTM-001 | GOB | GOB-STTM-001 — Criterios básicos de arranque | `docs/00-gobernanza/GOB-STTM-001-criterios-basicos.md` | Activo | Autor |
| DOC-006 | DOC | Modos de Gobernanza en STTM | `docs/01-metodo/MODOS-DE-GOBERNANZA.md` | Activo | Autor |
| DOC-007 | DOC | Nota biográfica del autor (versión en español) | `docs/01-metodo/NOTA-BIOGRAFICA-AUTOR.md` | Activo | Autor |
| DOC-008 | DOC | STTM — Método Salem de Trazabilidad y Confianza | `docs/01-metodo/ONE-PAGER_es.md` | Activo | Autor |
| ADR-STTM-001 | ADR | ADR-STTM-001 — Modelo de evidencia, modos y arranque en Termux | `docs/02-arquitectura/ADR-STTM-001-modelo-de-evidencia.md` | Activo | Autor |
| ADR-STTM-002 | ADR | ADR-STTM-002 — Interfaz de tres niveles y editores de input | `docs/02-arquitectura/ADR-STTM-002-interfaz-tres-niveles.md` | Activo | Autor |
| ADR-STTM-003 | ADR | ADR-STTM-003 — Catálogo de proyectos y registro de auditorías | `docs/02-arquitectura/ADR-STTM-003-proyectos-y-auditorias.md` | Activo | Autor |
| DOC-009 | DOC | Motivos de la revisión de código y convención de cabeceras | `docs/02-arquitectura/MOTIVOS-REVISION-CODIGO.md` | Activo | Autor |
| DOC-010 | DOC | PUNTOS CRÍTICOS DE UX — Visor STTM | `docs/05-ui/PUNTOS-CRITICOS-UX.md` | Activo | Autor |
| DOC-011 | DOC | Validación manual de la interfaz de usuario | `docs/05-ui/VALIDACION-MANUAL-UI.md` | Activo | Autor |
| DOC-012 | DOC | ANCLAJE DE CLAVE Ed25519 — STTM (K-005) | `docs/06-seguridad/ANCLAJE-CLAVE-ED25519.md` | Activo | Autor |
| DOC-013 | DOC | IDENTIDAD VISUAL — Salem / STTM | `docs/IDENTIDAD-VISUAL-SALEM-STTM.md` | Activo | Autor |


## Notas

- **Versiones:** No se registran versiones explícitas en este documento. Cada documento se versiona mediante commits en git; el historial de cambios está disponible en el repo.
- **Estado "Activo":** Todos los documentos listados están en uso. Si un documento se depreca, se agrega una fila con estado "Deprecado" y se indica el documento que lo reemplaza.
- **Responsable:** Por defecto es el autor del proyecto (Martín José Dalberto). Los ADRs y GOBs pueden tener responsables específicos si se declaran en el documento.

## Mantenimiento

Este registro se actualiza manualmente cuando:
- Se agrega un documento nuevo al repo.
- Se depreca un documento existente.
- Cambia el responsable de un documento.

La próxima actualización está prevista para el próximo commit que agregue o modifique documentos de gobernanza.

---
*Documento registrado en la bitácora del proyecto (entrada de STTM-0.31).*
