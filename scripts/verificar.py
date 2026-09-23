#!/usr/bin/env python3
"""
verificar.py — Verificador de integridad de la bitácora STTM.

Recalcula el hash SHA-256 de cada entrada y comprueba:
  1. Que el hash guardado coincida con el contenido (detecta edición).
  2. Que hash_prev apunte al hash real de la entrada anterior
     (detecta inserciones, borrados o reordenamientos).

Uso:
    python scripts/verificar.py                  # verifica BITACORA.jsonl
    python scripts/verificar.py otra.jsonl       # verifica una copia o export

Sale con código 0 si todo está íntegro, 1 si hay problemas.
"""
import hashlib
import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
BITACORA = RAIZ / "BITACORA.jsonl"

# Cadena de ceros: el "hash previo" de la primera entrada.
HASH_CERO = "0" * 64

# Mismos campos canónicos que usa registrar.py al firmar.
# Si esto cambia acá, debe cambiar allá también.
CAMPOS = ("n", "ts", "titulo", "detalle", "archivos",
          "commit_ref", "firma_tipo", "firma", "hash_prev")


def calcular_hash(entrada: dict) -> str:
    """Recalcula el hash de una entrada usando sus campos canónicos."""
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

        # Comprobación 1: cadena.
        if entrada.get("hash_prev") != hash_prev_esperado:
            problemas.append(
                f"Entrada #{n}: cadena rota (hash_prev no coincide con la entrada anterior)."
            )

        # Comprobación 2: contenido.
        hash_guardado = entrada.get("hash")
        hash_calculado = calcular_hash(entrada)
        if hash_guardado != hash_calculado:
            problemas.append(
                f"Entrada #{n}: contenido alterado (hash guardado ≠ hash recalculado)."
            )

        # La próxima entrada deberá apuntar al hash guardado de esta.
        hash_prev_esperado = hash_guardado

    print(f"🔍 Verificando: {ruta}")
    print(f"Entradas: {len(lineas)}")

    if problemas:
        print(f"❌ {len(problemas)} problema(s) detectado(s):")
        for p in problemas:
            print(f"   - {p}")
        return 1

    print(f"✅ Cadena íntegra: {len(lineas)}/{len(lineas)} entradas verificadas.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
