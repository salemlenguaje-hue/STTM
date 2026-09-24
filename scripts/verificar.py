#!/usr/bin/env python3
# Creado por Martín José Dalberto, Argentina, 2026.
# SPDX-License-Identifier: MIT
"""
verificar.py — Verificador de integridad con schemas versionados.

Expone verificar(ruta) que devuelve un resultado estructurado para que
otros módulos (auditar.py) lo consuman sin parsear texto.
main() conserva exactamente la salida histórica para no romper tests.
"""
import json
import os
import sys
from pathlib import Path
import firma

RAIZ = Path(os.environ.get("STTM_ROOT", Path(__file__).resolve().parent.parent))
from rutas import BITACORA  # K-002: fuente única de verdad de rutas
HASH_CERO = "0" * 64


def verificar(ruta=None):
    """Devuelve un dict estructurado con el estado de la cadena."""
    ruta = Path(ruta) if ruta else BITACORA
    res = {
        "ruta": str(ruta),
        "existe": ruta.exists(),
        "entradas": 0,
        "schemas": {"v1": 0, "v2": 0},
        "por_entrada": [],
        "problemas": [],
        "avisos": [],
        "integra": False,
        "entradas_verificadas": 0,
        "firmas_validadas": 0,
    }
    if not ruta.exists():
        return res

    lineas = [l for l in ruta.read_text(encoding="utf-8").splitlines() if l.strip()]
    res["entradas"] = len(lineas)
    if not lineas:
        res["integra"] = True
        return res

    hash_prev_esperado = HASH_CERO
    for numero_linea, linea in enumerate(lineas, start=1):
        entrada_problemas = []
        entrada_avisos = []
        firma_ok = False
        try:
            entrada = json.loads(linea)
        except json.JSONDecodeError:
            entrada_problemas.append(f"Línea {numero_linea}: no es JSON válido.")
            res["por_entrada"].append({"n": numero_linea, "ok": False,
                                       "problemas": entrada_problemas,
                                       "avisos": [], "firma_ok": False})
            res["problemas"].extend(entrada_problemas)
            continue

        n = entrada.get("n", numero_linea)

        if entrada.get("hash_prev") != hash_prev_esperado:
            entrada_problemas.append(f"Entrada #{n}: cadena rota.")

        h = entrada.get("hash")
        if h == firma.hash_contenido(entrada):
            res["schemas"]["v2"] += 1
        elif h == firma.hash_contenido_v1(entrada):
            res["schemas"]["v1"] += 1
        else:
            entrada_problemas.append(f"Entrada #{n}: contenido alterado.")

        modo = entrada.get("firma_tipo")
        f = entrada.get("firma")
        if modo == "hash":
            if f is not None:
                entrada_problemas.append(f"Entrada #{n}: modo hash no debería tener firma.")
            else:
                firma_ok = True
        elif modo == "hmac":
            clave = os.environ.get("STTM_HMAC_KEY", "clave_secreta_temporal")
            if f == firma.hmac_firma(entrada, clave):
                firma_ok = True
            elif f == firma.hmac_firma_legacy(entrada, clave):
                entrada_avisos.append(f"Entrada #{n}: firma HMAC legacy (incidente 001), contenido íntegro.")
            else:
                entrada_problemas.append(f"Entrada #{n}: firma HMAC inválida.")
        elif modo == "ed25519":
            if not firma.ED25519_DISPONIBLE:
                entrada_avisos.append(f"Entrada #{n}: Ed25519 no disponible, verificación degradada.")
            else:
                ruta_pub = RAIZ / "data" / "claves" / "sofia_publica.pem"
                if not ruta_pub.exists():
                    entrada_avisos.append(f"Entrada #{n}: clave pública ausente, verificación degradada.")
                elif not f or not firma.ed25519_verificar(entrada, f, ruta_pub.read_bytes()):
                    entrada_problemas.append(f"Entrada #{n}: firma Ed25519 inválida.")
                else:
                    firma_ok = True
        else:
            entrada_problemas.append(f"Entrada #{n}: modo de firma desconocido ({modo}).")

        entrada_ok = not entrada_problemas
        res["por_entrada"].append({"n": n, "ok": entrada_ok,
                                   "problemas": entrada_problemas,
                                   "avisos": entrada_avisos, "firma_ok": firma_ok})
        res["problemas"].extend(entrada_problemas)
        res["avisos"].extend(entrada_avisos)
        if entrada_ok:
            res["entradas_verificadas"] += 1
        if firma_ok:
            res["firmas_validadas"] += 1
        hash_prev_esperado = h

    res["integra"] = not res["problemas"]
    return res


def main() -> int:
    ruta = Path(sys.argv[1]) if len(sys.argv) > 1 else None
    res = verificar(ruta)

    if not res["existe"]:
        print(f"❌ No encuentro la bitácora: {res['ruta']}")
        return 1
    if res["entradas"] == 0:
        print("⚠️ Bitácora vacía: nada que verificar.")
        return 0

    print(f"🔍 Verificando: {res['ruta']}")
    print(f"Entradas: {res['entradas']} (schemas: v1={res['schemas']['v1']}, v2={res['schemas']['v2']})")

    if res["avisos"]:
        print(f"⚠️ {len(res['avisos'])} aviso(s):")
        for a in res["avisos"]:
            print(f"   - {a}")
    if res["problemas"]:
        print(f"❌ {len(res['problemas'])} problema(s):")
        for p in res["problemas"]:
            print(f"   - {p}")
        return 1

    print(f"✅ Cadena íntegra: {res['entradas']}/{res['entradas']} entradas verificadas.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
