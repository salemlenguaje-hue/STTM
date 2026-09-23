#!/usr/bin/env python3
"""
verificar.py — Verificador de integridad con schemas versionados.

Acepta:
- Hash de contenido v2 (canónico) o v1 (histórico, entradas 1-8).
- HMAC canónico o HMAC legacy (incidente 001, entrada #10).
Distingue ERRORES (rompen la evidencia) de AVISOS (degradaciones documentadas).
Sale 0 si no hay errores, 1 si los hay.
"""
import json
import os
import sys
from pathlib import Path
import firma

RAIZ = Path(os.environ.get("STTM_ROOT", Path(__file__).resolve().parent.parent))
BITACORA = RAIZ / "BITACORA.jsonl"
HASH_CERO = "0" * 64
CLAVE_HMAC = os.environ.get("STTM_HMAC_KEY", "clave_secreta_temporal")


def main() -> int:
    ruta = Path(sys.argv[1]) if len(sys.argv) > 1 else BITACORA
    if not ruta.exists():
        print(f"❌ No encuentro la bitácora: {ruta}")
        return 1

    lineas = [l for l in ruta.read_text(encoding="utf-8").splitlines() if l.strip()]
    if not lineas:
        print("⚠️ Bitácora vacía: nada que verificar.")
        return 0

    errores = []
    avisos = []
    conteo_schemas = {"v1": 0, "v2": 0}
    hash_prev_esperado = HASH_CERO

    for numero_linea, linea in enumerate(lineas, start=1):
        try:
            entrada = json.loads(linea)
        except json.JSONDecodeError:
            errores.append(f"Línea {numero_linea}: no es JSON válido.")
            continue

        n = entrada.get("n", numero_linea)

        # 1) Cadena: hash_prev debe apuntar al hash guardado de la anterior.
        if entrada.get("hash_prev") != hash_prev_esperado:
            errores.append(f"Entrada #{n}: cadena rota.")

        # 2) Contenido: aceptar v2 (canónico) o v1 (histórico).
        h = entrada.get("hash")
        if h == firma.hash_contenido(entrada):
            conteo_schemas["v2"] += 1
        elif h == firma.hash_contenido_v1(entrada):
            conteo_schemas["v1"] += 1
        else:
            errores.append(f"Entrada #{n}: contenido alterado.")

        # 3) Firma según modo declarado.
        modo = entrada.get("firma_tipo")
        f = entrada.get("firma")

        if modo == "hash":
            if f is not None:
                errores.append(f"Entrada #{n}: modo hash no debería tener firma.")

        elif modo == "hmac":
            if f == firma.hmac_firma(entrada, CLAVE_HMAC):
                pass  # firma canónica ok
            elif f == firma.hmac_firma_legacy(entrada, CLAVE_HMAC):
                avisos.append(f"Entrada #{n}: firma HMAC legacy (incidente 001), contenido íntegro.")
            else:
                errores.append(f"Entrada #{n}: firma HMAC inválida.")

        elif modo == "ed25519":
            if not firma.ED25519_DISPONIBLE:
                avisos.append(f"Entrada #{n}: Ed25519 no disponible, verificación degradada.")
            else:
                ruta_pub = RAIZ / "data" / "claves" / "sofia_publica.pem"
                if not ruta_pub.exists():
                    avisos.append(f"Entrada #{n}: clave pública ausente, verificación degradada.")
                elif not f or not firma.ed25519_verificar(entrada, f, ruta_pub.read_bytes()):
                    errores.append(f"Entrada #{n}: firma Ed25519 inválida.")
        else:
            errores.append(f"Entrada #{n}: modo de firma desconocido ({modo}).")

        hash_prev_esperado = h

    print(f"🔍 Verificando: {ruta}")
    print(f"Entradas: {len(lineas)} (schemas: v1={conteo_schemas['v1']}, v2={conteo_schemas['v2']})")

    if avisos:
        print(f"⚠️ {len(avisos)} aviso(s):")
        for a in avisos:
            print(f"   - {a}")

    if errores:
        print(f"❌ {len(errores)} error(es):")
        for e in errores:
            print(f"   - {e}")
        return 1

    print(f"✅ Cadena íntegra: {len(lineas)}/{len(lineas)} entradas verificadas.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
