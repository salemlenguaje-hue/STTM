#!/usr/bin/env python3
# Creado por Martín José Dalberto, Argentina, 2026.
# SPDX-License-Identifier: MIT
"""
auditoria_meta.py — Metadatos de auditoría STTM (ADR-003 §3.3).

Cada auditoría crea auditorias/<timestamp>/meta.json con:
quién pidió, quién ejecutó, por qué, qué se encontró y estado final.

Reglas ADR-003 que respeta:
- meta.json se escribe UNA sola vez; no se modifica.
- Corregir = auditoría nueva con campo sustituye_a.
- Al completar, actualiza primera/ultima_auditoria_utc del catálogo
  mediante entrada append-only (accion=actualizar).

Uso:
    python scripts/auditoria_meta.py generar \
        --proyecto 1 --motivo "..." --tipo rapida --modo continuidad \
        --solicitante-rol autor --solicitante-nombre "Nombre" \
        --ejecutado-rol autor --ejecutado-nombre "Nombre" \
        --rojos 0 --amarillos 1 --informativos 0 \
        --estado apto_con_observaciones --cadena-integra \
        --entradas-verificadas 15 --entradas-totales 15 --firmas-validadas 15 \
        --reporte reporte.md --manifiesto manifiesto.json \
        --observacion "texto" [--observacion "otro"] [--sustituye-a AUD-...]
"""
import argparse
import json
import os
from datetime import datetime, timezone
from pathlib import Path

import proyectos  # mismo directorio; aporta cargar_estado() y agregar()

RAIZ = Path(os.environ.get("STTM_ROOT", Path(__file__).resolve().parent.parent))
AUDITORIAS = RAIZ / "auditorias"

TIPOS = ("rapida", "estandar", "profunda")
MODOS = ("simple", "continuidad", "salem")
ESTADOS = ("apto", "apto_con_observaciones", "no_apto")
ROLES = ("autor", "colaborador", "auditor_externo", "ia_asistente", "tercero")


def ahora_utc():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def stamp_carpeta():
    return datetime.now(timezone.utc).strftime("%Y-%m-%d_%H%M%S")


def nuevo_id():
    return "AUD-" + datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")


def escribir_meta(carpeta, meta):
    """Escribe meta.json una sola vez. Si existe, se niega (ADR-003)."""
    carpeta.mkdir(parents=True, exist_ok=True)
    ruta = carpeta / "meta.json"
    if ruta.exists():
        raise FileExistsError(
            f"meta.json ya existe en {carpeta}: no se modifica (ADR-003). "
            f"Para corregir, creá una auditoría nueva con --sustituye-a."
        )
    ruta.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    return ruta


def actualizar_catalogo(n, ts):
    """Append-only: primera_auditoria solo si era null; ultima siempre."""
    estado = proyectos.cargar_estado()
    if n not in estado:
        raise KeyError(f"No existe el proyecto #{n}")
    cambios = {"ultima_auditoria_utc": ts}
    if estado[n].get("primera_auditoria_utc") is None:
        cambios["primera_auditoria_utc"] = ts
    proyectos.agregar({
        "accion": "actualizar",
        "n": n,
        "ts": ts,
        "cambios": cambios,
        "motivo": "auditoria completada",
    })
    return cambios


def cmd_generar(args):
    estado = proyectos.cargar_estado()
    if args.proyecto not in estado:
        print(f"❌ No existe el proyecto #{args.proyecto}")
        return 1
    if not estado[args.proyecto].get("activo"):
        print(f"❌ El proyecto #{args.proyecto} está inactivo; no se audita.")
        return 1

    ts = ahora_utc()
    carpeta = AUDITORIAS / stamp_carpeta()

    meta = {
        "auditoria_id": nuevo_id(),
        "proyecto_n": args.proyecto,
        "proyecto_ref": estado[args.proyecto].get("ref_interna"),
        "fecha_utc": ts,
        "motivo": args.motivo,
        "solicitante": {"rol": args.solicitante_rol, "nombre": args.solicitante_nombre},
        "ejecutado_por": {"rol": args.ejecutado_rol, "nombre": args.ejecutado_nombre},
        "tipo": args.tipo,
        "modo_aplicado": args.modo,
        "hallazgos": {
            "rojos": args.rojos,
            "amarillos": args.amarillos,
            "informativos": args.informativos,
        },
        "estado_final": args.estado,
        "cadena_integra": args.cadena_integra,
        "entradas_verificadas": args.entradas_verificadas,
        "entradas_totales": args.entradas_totales,
        "firmas_validadas": args.firmas_validadas,
        "reporte_ruta": args.reporte,
        "manifiesto_ruta": args.manifiesto,
        "observaciones": args.observacion or [],
    }
    if args.sustituye_a:
        meta["sustituye_a"] = args.sustituye_a

    ruta = escribir_meta(carpeta, meta)
    cambios = actualizar_catalogo(args.proyecto, ts)

    rel = ruta.relative_to(RAIZ)
    print(f"✅ Auditoría {meta['auditoria_id']} registrada en {rel}")
    print(f"Catálogo actualizado: {json.dumps(cambios, ensure_ascii=False)}")
    print("Recordá registrar este hito en la bitácora:")
    print(f'  python scripts/registrar.py "Auditoría {meta["auditoria_id"]} completada" '
          f'"Motivo y resultado." --archivos "{rel}" --modo-firma ed25519')
    return 0


def main():
    parser = argparse.ArgumentParser(description="Metadatos de auditoría STTM (ADR-003).")
    sub = parser.add_subparsers(dest="comando")

    g = sub.add_parser("generar", help="Crea auditorias/<ts>/meta.json y actualiza el catálogo.")
    g.add_argument("--proyecto", type=int, required=True)
    g.add_argument("--motivo", required=True)
    g.add_argument("--tipo", choices=TIPOS, default="rapida")
    g.add_argument("--modo", choices=MODOS, default="continuidad")
    g.add_argument("--solicitante-rol", choices=ROLES, default="autor")
    g.add_argument("--solicitante-nombre", default="Martín José Dalberto")
    g.add_argument("--ejecutado-rol", choices=ROLES, default="autor")
    g.add_argument("--ejecutado-nombre", default="Martín José Dalberto")
    g.add_argument("--rojos", type=int, default=0)
    g.add_argument("--amarillos", type=int, default=0)
    g.add_argument("--informativos", type=int, default=0)
    g.add_argument("--estado", choices=ESTADOS, default="apto")
    g.add_argument("--cadena-integra", action="store_true")
    g.add_argument("--entradas-verificadas", type=int, default=0)
    g.add_argument("--entradas-totales", type=int, default=0)
    g.add_argument("--firmas-validadas", type=int, default=0)
    g.add_argument("--reporte", default="reporte.md")
    g.add_argument("--manifiesto", default="manifiesto.json")
    g.add_argument("--observacion", action="append")
    g.add_argument("--sustituye-a", default=None)

    args = parser.parse_args()
    if args.comando == "generar":
        return cmd_generar(args)
    parser.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
