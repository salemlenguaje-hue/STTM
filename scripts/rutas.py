#!/usr/bin/env python3
"""
rutas.py — Fuente única de verdad de rutas STTM (K-002, v2 para K-001).

Regla de carpetas (ADR-003 §3.2): cada proyecto vive en
data/proyectos/<n>-<ref_interna>/ y su bitácora en
data/proyectos/<n>-<ref_interna>/BITACORA.jsonl.

Resolución:
- El proyecto activo por defecto viene de STTM_PROYECTO (default 1).
  El servidor pasa esta variable por request a sus subprocess; la CLI
  humana la usa directamente. Ningún script guarda estado global.
- El slug de la carpeta es la ref_interna del catálogo, que se fija al
  crear el proyecto y no cambia (si cambiara, la carpeta se migra con
  asiento en bitácora, como toda mudanza).
- Si el catálogo no existe (sandboxes mínimos de tests), el proyecto 1
  cae al slug histórico "STTM"; cualquier otro número sin catálogo es
  un error explícito, no un silencio.
"""
import json
import os
from pathlib import Path

RAIZ = Path(os.environ.get("STTM_ROOT", Path(__file__).resolve().parent.parent))
CATALOGO = RAIZ / "data" / "proyectos.jsonl"

PROYECTO_N = int(os.environ.get("STTM_PROYECTO", "1"))


def _refs_del_catalogo():
    """Mapa n -> ref_interna, leyendo solo entradas de creación."""
    if not CATALOGO.exists():
        return {}
    refs = {}
    for linea in CATALOGO.read_text(encoding="utf-8").splitlines():
        linea = linea.strip()
        if not linea:
            continue
        try:
            entrada = json.loads(linea)
        except json.JSONDecodeError:
            continue
        if entrada.get("accion") == "actualizar":
            continue
        n = entrada.get("n")
        if n is not None:
            refs[n] = entrada.get("ref_interna")
    return refs


def carpeta_de(n):
    refs = _refs_del_catalogo()
    if n in refs and refs[n]:
        slug = refs[n]
    elif n == 1:
        slug = "STTM"  # default histórico para sandboxes sin catálogo
    else:
        raise RuntimeError(
            f"No puedo resolver la carpeta del proyecto #{n}: "
            f"no figura en el catalogo {CATALOGO}")
    return RAIZ / "data" / "proyectos" / f"{n}-{slug}"


def bitacora_de(n):
    return carpeta_de(n) / "BITACORA.jsonl"


# Rutas del proyecto activo por defecto (compatibilidad con K-002).
# Si el proyecto no existe, salida limpia en vez de traceback crudo:
# el mensaje debe alcanzarle a una persona, no solo a un programador.
try:
    CARPETA_PROYECTO = carpeta_de(PROYECTO_N)
    BITACORA = bitacora_de(PROYECTO_N)
except RuntimeError as e:
    raise SystemExit(f"❌ {e}") from None

CARPETA_PROYECTO.mkdir(parents=True, exist_ok=True)
