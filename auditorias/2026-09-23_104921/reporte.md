# Reporte de Auditoría STTM
**Fecha UTC:** 2026-09-23_104921
**Proyecto:** STTM (Línea base local)

## 1. Integridad de la Bitácora
**Estado:** ✅ Íntegra
```
🔍 Verificando: /data/data/com.termux/files/home/sttm/BITACORA.jsonl
Entradas: 4
✅ Cadena íntegra: 4/4 entradas verificadas.
```

## 2. Privacidad y Secretos (R14-15 / R20-15)
**Estado:** ❌ Se encontraron 1 alerta(s).

- 🔴 CONTENIDO SENSIBLE: scripts/auditar.py (contiene '-----begin private key')

## 3. Límites de esta auditoría
- Esta auditoría es local y heurística.
- No reemplaza una revisión humana exhaustiva antes de publicar.
- No verifica firmas criptográficas asimétricas (modo hash actual).

---
*Generado por STTM `scripts/auditar.py`*