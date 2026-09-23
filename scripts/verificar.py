#!/usr/bin/env python3
"""verificar.py — Verificador de integridad de la bitácora STTM."""
import hashlib
import json
import os
import sys
from pathlib import Path

RAIZ = Path(os.environ.get("STTM_ROOT", Path(__file__).resolve().parent.parent))
BITACORA = RAIZ / "BITACORA.jsonl"
HASH_CERO = "0" * 64
CAMPOS = ("n", "ts", "titulo", "detalle", "archivos",
          "commit_ref", "firma_tipo", "firma", "hash_prev")

def calcular_hash(entrada: dict) -> str:
    base = {campo: entrada.get(campo) for campo in CAMPOS}
    texto = json.dumps(base, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(texto.encode("utf-8")).hexdigest()

def main() -> int:
    ruta = Path(sys.argv[1]) if len(sys.argv) > 1 else BITACORA
    if not ruta.exists():
        print(f"❌ No encuentro la bitácora: {ruta}")
        return 1

    lineas = [l for l in ruta.read_text(encoding="utf-8").splitlines() if l.strip()]
    if not lineas:
        print("⚠️ Bitácora vacía: nada que verificar.")
        return 0

    problemas = []
    hash_prev_esperado = HASH_CERO

    for numero_linea, linea in enumerate(lineas, start=1):
        try:
            entrada = json.loads(linea)
        except json.JSONDecodeError:
            problemas.append(f"Línea {numero_linea}: no es JSON válido.")
            continue

        n = entrada.get("n", numero_linea)
        if entrada.get("hash_prev") != hash_prev_esperado:
            problemas.append(f"Entrada #{n}: cadena rota.")

        hash_guardado = entrada.get("hash")
        if hash_guardado != calcular_hash(entrada):
            problemas.append(f"Entrada #{n}: contenido alterado.")

        hash_prev_esperado = hash_guardado

    print(f"🔍 Verificando: {ruta}")
    print(f"Entradas: {len(lineas)}")

    if problemas:
        print(f"❌ {len(problemas)} problema(s):")
        for p in problemas: print(f"   - {p}")
        return 1

    print(f"✅ Cadena íntegra: {len(lineas)}/{len(lineas)} entradas verificadas.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
