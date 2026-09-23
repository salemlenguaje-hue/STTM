# Reporte de Auditoría STTM
**Fecha UTC:** 2026-09-23T17:15:33Z
**Proyecto:** #1 (STTM)

## 1. Integridad de la Bitácora
**Estado:** ✅ Íntegra
**Entradas:** 15 (verificadas: 15, firmas canónicas válidas: 14)
**Schemas:** v1=9, v2=6
**Avisos:**
- Entrada #10: firma HMAC legacy (incidente 001), contenido íntegro.

## 2. Privacidad y Secretos (R14-15 / R20-15)
**Ámbar:** ⚠️ 1
- 🟡 ARCHIVO SENSIBLE EN UBICACION CONTROLADA: data/claves/sofia_privada.pem (excluido por .gitignore: *.pem). Verificar que la exclusion siga vigente.

## 3. Resumen de hallazgos
- Rojos: 0
- Amarillos: 2
- Estado final: **apto_con_observaciones**

## 4. Semántica de conteo
- `firmas_validadas` cuenta solo verificaciones positivas del esquema canónico.
- Las firmas HMAC legacy (incidente 001) se reconocen con aviso y no suman.

## 5. Límites de esta auditoría
- Esta auditoría es local y heurística.
- No reemplaza una revisión humana exhaustiva antes de publicar.
- La carpeta `scripts/` se excluye del escaneo de contenido (son herramientas).

---
*Generado por STTM `scripts/auditar.py` v2*