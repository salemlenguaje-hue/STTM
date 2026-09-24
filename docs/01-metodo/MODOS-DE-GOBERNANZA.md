# Modos de Gobernanza en STTM

**Última actualización:** 2026-09-24
**Estado:** Documentación formal (STTM-0.27)
**Definición canónica:** CONTINUIDAD.md §2 y ADR-STTM-002.

## Los tres modos

1. **Registro Simple:** bitácora JSONL encadenada con SHA-256. Nada más.
2. **Continuidad:** agrega documentos de estado, índices y handoff.
3. **Salem:** agrega ADRs, GOBs, auditorías y export de evidencia.

STTM opera hoy en modo Salem (dogfooding: la herramienta se aplica a sí
misma con el máximo nivel).

## Qué enforce el código y qué es práctica documentada

Esta separación es deliberada: un modo no debe prometer lo que el código
no garantiza.

**Enforceado en código:**
- **Nivel por proyecto:** campo `nivel_actual` en el catálogo
  `data/proyectos.jsonl`. El catálogo es append-only: cada cambio de
  nivel agrega una entrada de actualización, el historial no se reescribe.
- **Cambio de nivel:** `python scripts/proyectos.py nivel --n N --nivel X
  --motivo "..."`, o desde la UI (selector de modo con confirmación
  explícita y asiento en bitácora, ADR-002 §3.5).
- **Honestidad visual (ADR-002):** la UI oculta las capacidades que el
  nivel actual no tiene. En simple no se muestran documentos; fuera de
  salem no se muestran auditorías. Lo deshabilitado no se finge.

**Práctica documentada, NO enforceada por el código:**
- **Modo de firma:** se elige por registro (`--modo-firma
  hash|hmac|ed25519`). El nivel no obliga un modo de firma en código;
  la práctica del proyecto es firmar con Ed25519 en Continuidad y Salem.
- **Auditorías:** `auditar.py` se ejecuta a demanda (CLI o UI). No
  existen auditorías programadas automáticas; la frecuencia es una
  práctica del proyecto, no una garantía del modo.
- **Timestamping externo (OpenTimestamps):** proceso manual documentado
  (testigo #2, con upgrade de Bitcoin pendiente). El código no lo
  enforcea por nivel.

## Transiciones entre modos

**Ascenso (simple → continuidad → salem):**
1. Ejecutar `python scripts/proyectos.py nivel --n N --nivel X --motivo "..."`
   (o usar el selector de modo en la UI, que pide confirmación).
2. El catálogo agrega la entrada de actualización (historial append-only).
3. Se asienta el cambio en la bitácora con su motivo.

**Descenso:** técnicamente posible con el mismo comando. Queda en el
historial del catálogo y en la bitácora. Se desaconseja sin motivo
documentado: bajar el nivel después de haber demostrado integridad
genera dudas sobre la historia posterior.

## Filosofía

- **El nivel adecuado al riesgo:** la trazabilidad tiene costo (tiempo,
  dependencias, ceremonia). No todos los proyectos necesitan Salem.
- **Migración explícita:** cambiar de modo no es silencioso; queda en el
  catálogo y en la bitácora con motivo.
- **Honestidad ante todo:** lo que el código no enforcea se declara como
  práctica documentada, nunca como garantía del modo. Un proyecto en
  modo Simple con bitácora honesta vale más que uno en Salem con
  auditorías rotas o testigos falsos.

## Referencias

- CONTINUIDAD.md §2 (definición de los tres modos)
- ADR-STTM-001 (modelo de evidencia)
- ADR-STTM-002 (interfaz de tres niveles y honestidad visual)
- ADR-STTM-003 (catálogo de proyectos y auditorías)
- GOB-STTM-001 (política de gobernanza)
- docs/05-ui/VALIDACION-MANUAL-UI.md (validación manual declarada)

---
*Documento registrado en la bitácora del proyecto (entrada de STTM-0.27).*
