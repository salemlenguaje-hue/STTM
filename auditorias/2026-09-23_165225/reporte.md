# Reporte de Auditoría STTM
**Fecha UTC:** 2026-09-23T16:52:25Z
**Proyecto:** #1 (STTM)

## 1. Integridad de la Bitácora
**Estado:** ✅ Íntegra
**Entradas:** 15 (verificadas: 15, firmas válidas: 14)
**Schemas:** v1=9, v2=6
**Avisos:**
- Entrada #10: firma HMAC legacy (incidente 001), contenido íntegro.

## 2. Privacidad y Secretos (R14-15 / R20-15)
**Estado:** ❌ 3 alerta(s).
- 🔴 CONTENIDO SENSIBLE: CONTINUIDAD.md (contiene 'ghp_')
- 🔴 CONTENIDO SENSIBLE: BITACORA.jsonl (contiene 'ghp_')
- 🔴 ARCHIVO SENSIBLE: data/claves/sofia_privada.pem (coincide con '.pem')

## 3. Resumen de hallazgos
- Rojos: 3
- Amarillos: 1
- Estado final: **no_apto**

## 4. Límites de esta auditoría
- Esta auditoría es local y heurística.
- No reemplaza una revisión humana exhaustiva antes de publicar.
- La carpeta `scripts/` se excluye del escaneo de contenido (son herramientas).

---
*Generado por STTM `scripts/auditar.py`*