#!/usr/bin/env python3
"""
registrar.py — Registro mínimo para STTM.

Este script agrega una entrada nueva a BITACORA.jsonl.
Cada entrada incluye el hash de la entrada anterior.

Por ahora no usa HMAC ni Ed25519.
Usa solo SHA-256 y deja declarado que el tipo de firma es "hash".

Uso simple:

    python scripts/registrar.py "Título" "Detalle" --archivos "a.md,b.md" --commit abc1234
"""

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

# Ruta raíz del proyecto STTM.
# Este archivo vive en scripts/, por eso subimos un nivel.
RAIZ = Path(__file__).resolve().parent.parent

# Archivo canónico de bitácora.
BITACORA = RAIZ / "BITACORA.jsonl"

# Cadena de ceros para la primera entrada.
HASH_CERO = "0" * 64


def ahora_utc() -> str:
    """
    Devuelve la fecha actual en formato UTC simple y estable.
    """
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def calcular_hash(entrada: dict) -> str:
    """
    Calcula un hash SHA-256 de los campos canónicos de la entrada.
    Se usa sort_keys para que el orden no cambie el hash.
    """
    base = {
        "n": entrada["n"],
        "ts": entrada["ts"],
        "titulo": entrada["titulo"],
        "detalle": entrada["detalle"],
        "archivos": entrada["archivos"],
        "commit_ref": entrada["commit_ref"],
        "firma_tipo": entrada["firma_tipo"],
        "firma": entrada["firma"],
        "hash_prev": entrada["hash_prev"],
    }

    texto = json.dumps(base, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(texto.encode("utf-8")).hexdigest()


def leer_ultima_entrada() -> dict:
    """
    Lee la última entrada de la bitácora.
    Si la bitácora no existe o está vacía, devuelve una entrada cero.
    """
    if not BITACORA.exists():
        return {"n": 0, "hash": HASH_CERO}

    ultima = None

    for linea in BITACORA.read_text(encoding="utf-8").splitlines():
        linea = linea.strip()
        if linea:
            ultima = json.loads(linea)

    if ultima is None:
        return {"n": 0, "hash": HASH_CERO}

    return ultima


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Agrega una entrada nueva a la bitácora STTM."
    )

    parser.add_argument(
        "titulo",
        help="Título breve del hito o decisión."
    )

    parser.add_argument(
        "detalle",
        help="Descripción clara del hito o decisión."
    )

    parser.add_argument(
        "--archivos",
        default="",
        help="Lista de archivos afectados, separados por comas."
    )

    parser.add_argument(
        "--commit",
        default=None,
        help="Hash corto del commit Git relacionado, si existe."
    )

    args = parser.parse_args()

    ultima = leer_ultima_entrada()

    archivos = [
        archivo.strip()
        for archivo in args.archivos.split(",")
        if archivo.strip()
    ]

    entrada = {
        "n": ultima["n"] + 1,
        "ts": ahora_utc(),
        "titulo": args.titulo,
        "detalle": args.detalle,
        "archivos": archivos,
        "commit_ref": args.commit,
        "firma_tipo": "hash",
        "firma": None,
        "hash_prev": ultima["hash"],
    }

    entrada["hash"] = calcular_hash(entrada)

    # Agregamos la entrada al final. Nunca editamos entradas anteriores.
    with BITACORA.open("a", encoding="utf-8") as archivo:
        archivo.write(json.dumps(entrada, ensure_ascii=False) + "\n")

    print(f"✅ Registro #{entrada['n']} agregado.")
    print(f"Hash: {entrada['hash'][:16]}...")
    print(f"Hash previo: {entrada['hash_prev'][:16]}...")


if __name__ == "__main__":
    main()
