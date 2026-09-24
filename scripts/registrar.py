#!/usr/bin/env python3
# Creado por Martín José Dalberto, Argentina, 2026.
# SPDX-License-Identifier: MIT
"""registrar.py — Registro STTM con firma canónica (schema v2)."""
import argparse
import json
import os
from datetime import datetime, timezone
from pathlib import Path
import firma

RAIZ = Path(os.environ.get("STTM_ROOT", Path(__file__).resolve().parent.parent))
from rutas import BITACORA  # K-002: fuente única de verdad de rutas
HASH_CERO = "0" * 64
CLAVE_HMAC = os.environ.get("STTM_HMAC_KEY")


def ahora_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def leer_ultima_entrada() -> dict:
    if not BITACORA.exists():
        return {"n": 0, "hash": HASH_CERO}
    ultima = None
    for linea in BITACORA.read_text(encoding="utf-8").splitlines():
        if linea.strip():
            ultima = json.loads(linea)
    if ultima is None:
        return {"n": 0, "hash": HASH_CERO}
    if "n" not in ultima or "hash" not in ultima:
        raise RuntimeError(
            "La última entrada de la bitácora no tiene forma de entrada STTM. "
            "Revisá la bitácora antes de registrar.")
    return ultima


def main() -> None:
    parser = argparse.ArgumentParser(description="Agrega una entrada a la bitácora STTM.")
    parser.add_argument("titulo")
    parser.add_argument("detalle")
    parser.add_argument("--archivos", default="")
    parser.add_argument("--commit", default=None)
    parser.add_argument("--modo-firma", choices=["hash", "hmac", "ed25519"], default="hash")
    args = parser.parse_args()

    ultima = leer_ultima_entrada()
    archivos = [a.strip() for a in args.archivos.split(",") if a.strip()]

    entrada = {
        "n": ultima["n"] + 1, "ts": ahora_utc(), "titulo": args.titulo,
        "detalle": args.detalle, "archivos": archivos, "commit_ref": args.commit,
        "firma_tipo": args.modo_firma, "firma": None,
        "hash_prev": ultima["hash"],
    }

    # 1) Hash de contenido canónico (sin firma).
    entrada["hash"] = firma.hash_contenido(entrada)

    # Guard: las claves de la entrada deben ser exactamente las canónicas.
    # Se verifica DESPUÉS de calcular el hash y ANTES de la firma.
    claves_esperadas = set(firma.CAMPOS_BASE) | {"firma", "hash"}
    claves_reales = set(entrada.keys())
    if claves_reales != claves_esperadas:
        extras = claves_reales - claves_esperadas
        faltan = claves_esperadas - claves_reales
        raise RuntimeError(
            f"Las claves de la entrada no coinciden con las canónicas. "
            f"Extras: {extras}. Faltan: {faltan}. "
            f"Si agregaste un campo nuevo, actualizá CAMPOS_BASE en firma.py.")
    
    # 2) Firma canónica: sobre base + hash, NUNCA sobre sí misma.
    if args.modo_firma == "hmac":
        if not CLAVE_HMAC:
            raise RuntimeError(
                "Modo HMAC requiere STTM_HMAC_KEY. Seteala con: "
                "export STTM_HMAC_KEY='tu_clave_secreta'")
        entrada["firma"] = firma.hmac_firma(entrada, CLAVE_HMAC)
    elif args.modo_firma == "ed25519":
        ruta_priv = RAIZ / "data" / "claves" / "sofia_privada.pem"
        if not ruta_priv.exists():
            print("❌ Clave privada no encontrada. Ejecuta: python scripts/firma.py ceremonia")
            return
        entrada["firma"] = firma.ed25519_firmar(entrada, ruta_priv.read_bytes()).hex()

    with BITACORA.open("a", encoding="utf-8") as archivo:
        archivo.write(json.dumps(entrada, ensure_ascii=False) + "\n")
        archivo.flush()
        os.fsync(archivo.fileno())

    print(f"✅ Registro #{entrada['n']} agregado (modo: {args.modo_firma}).")
    print(f"Hash: {entrada['hash'][:16]}...")
    if entrada["firma"]:
        print(f"Firma: {str(entrada['firma'])[:16]}...")


if __name__ == "__main__":
    main()
