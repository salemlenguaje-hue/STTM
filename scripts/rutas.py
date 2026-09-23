#!/usr/bin/env python3
"""
rutas.py — Fuente única de verdad de rutas STTM (K-002).

Antes de K-002 cada script calculaba su propia ruta de bitácora en la
raíz. Ahora la bitácora vive en data/proyectos/<n>-<slug>/ (ADR-003 §3.2)
y todos los scripts la importan de acá.

K-001 (selector de proyecto en UI) reemplazará las constantes
PROYECTO_N / PROYECTO_SLUG por resolución desde el catálogo o el selector.
"""
import os
from pathlib import Path

RAIZ = Path(os.environ.get("STTM_ROOT", Path(__file__).resolve().parent.parent))
CATALOGO = RAIZ / "data" / "proyectos.jsonl"

# Proyecto activo por defecto (primera entrada del catálogo, ADR-003).
# Carpeta nombrada <n>-<slug>; el slug es para humanos, el n es el ID estable.
PROYECTO_N = 1
PROYECTO_SLUG = "STTM"
CARPETA_PROYECTO = RAIZ / "data" / "proyectos" / f"{PROYECTO_N}-{PROYECTO_SLUG}"
BITACORA = CARPETA_PROYECTO / "BITACORA.jsonl"

# Asegura que la carpeta exista (idempotente; no toca la bitácora).
CARPETA_PROYECTO.mkdir(parents=True, exist_ok=True)
