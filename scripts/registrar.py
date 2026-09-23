#!/usr/bin/env python3
"""registrar.py — Registro mínimo para STTM."""
import argparse
import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path

RAIZ = Path(os.environ.get("STTM_ROOT", Path(__file__).resolve().parent.parent))
BITACORA = RAIZ / "BITACORA.jsonl"
HASH_CERO = "0" * 64

def ahora_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

def calcular_hash(entrada: dict) -> str:
    base = {
        "n": entrada["n"], "ts": entrada["ts"], "titulo": entrada["titulo"],
        "detalle": entrada["detalle"], "archivos": entrada["archivos"],
        "commit_ref": entrada["commit_ref"], "firma_tipo": entrada["firma_tipo"],
        "firma": entrada["firma"], "hash_prev": entrada["hash_prev"],
    }
    texto = json.dumps(base, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(texto.encode("utf-8")).hexdigest()

def leer_ultima_entrada() -> dict:
    if not BITACORA.exists(): return {"n": 0, "hash": HASH_CERO}
    ultima = None
    for linea in BITACORA.read_text(encoding="utf-8").splitlines():
        if linea.strip(): ultima = json.loads(linea)
    return ultima if ultima else {"n": 0, "hash": HASH_CERO}

def main() -> None:
    parser = argparse.ArgumentParser(description="Agrega una entrada a la bitácora STTM.")
    parser.add_argument("titulo")
    parser.add_argument("detalle")
    parser.add_argument("--archivos", default="")
    parser.add_argument("--commit", default=None)
    args = parser.parse_args()

    ultima = leer_ultima_entrada()
    archivos = [a.strip() for a in args.archivos.split(",") if a.strip()]

    entrada = {
        "n": ultima["n"] + 1, "ts": ahora_utc(), "titulo": args.titulo,
        "detalle": args.detalle, "archivos": archivos, "commit_ref": args.commit,
        "firma_tipo": "hash", "firma": None, "hash_prev": ultima["hash"],
    }
    entrada["hash"] = calcular_hash(entrada)

    with BITACORA.open("a", encoding="utf-8") as archivo:
        archivo.write(json.dumps(entrada, ensure_ascii=False) + "\n")

    print(f"✅ Registro #{entrada['n']} agregado.")
    print(f"Hash: {entrada['hash'][:16]}...")

if __name__ == "__main__":
    main()
