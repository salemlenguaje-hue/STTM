#!/usr/bin/env python3
"""
auditar.py — Motor de auditoría local para STTM (integra ADR-003, v2).

Cambios v2 (incidente 002):
- Tokens: regex con longitud mínima (ghp_ + 36 alfanuméricos). El prefijo
  pelado matcheaba prosa que describe el propio patrón (CONTINUIDAD.md,
  BITACORA.jsonl). La bitácora no se edita: se corrige el patrón.
- Archivos sensibles: clasificación consciente de .gitignore.
  Rojo  = sensible SIN exclusión (riesgo de publicación).
  Ámbar = sensible EN ubicación controlada (excluido por .gitignore).
- manifiesto.json: ahora se escribe de verdad (hashes de artefactos).
  Antes meta.json lo anunciaba sin que existiera (gap de coherencia).
- firmas_validadas cuenta solo esquemas canónicos; legacy = aviso.
"""
import argparse
import hashlib
import json
import os
import re
import sys
from datetime import datetime, timezone
from fnmatch import fnmatch
from pathlib import Path

import verificar as mod_verificar
import auditoria_meta
import proyectos

RAIZ = Path(os.environ.get("STTM_ROOT", Path(__file__).resolve().parent.parent))
AUDITORIAS = RAIZ / "auditorias"

# --- Reglas de privacidad ---
ARCHIVOS_ROJOS = [
    ".key", ".pem", "id_rsa", "id_ed25519",
    ".env", "secret", "token", "password",
    "sofia_salem.key", "experimentos.db"
]

# Subcadenas simples (se mantienen fragmentadas por higiene).
TEXTOS_ROJOS = [
    "pass" + "word=", "api_" + "key=", "secret_" + "key=",
]

# Regex con forma real del secreto. Incidente 002: el prefijo pelado
# matcheaba documentación que describe el patrón.
REGEX_ROJOS = [
    re.compile(r"ghp_[A-Za-z0-9]{36,}", re.I),
    re.compile(r"github_pat_[A-Za-z0-9_]{22,}", re.I),
    re.compile(r"-----begin [a-z ]*private key-----", re.I),
]

EXTENSIONES_TEXTO = {".md", ".txt", ".json", ".jsonl", ".py", ".html", ".css", ".js", ".sh"}
EXCLUIR_CONTENIDO = {"scripts", "tests", ".git", "__pycache__", "node_modules"}
IGNORAR_TOTAL = {"auditorias", ".git", "__pycache__", "node_modules"}


def ahora_utc():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def stamp_carpeta():
    return datetime.now(timezone.utc).strftime("%Y-%m-%d_%H%M%S")


def sha256_archivo(ruta):
    h = hashlib.sha256()
    with ruta.open("rb") as f:
        for bloque in iter(lambda: f.read(65536), b""):
            h.update(bloque)
    return h.hexdigest()


def patrones_gitignore():
    gi = RAIZ / ".gitignore"
    if not gi.exists():
        return []
    pats = []
    for linea in gi.read_text(encoding="utf-8").splitlines():
        linea = linea.strip()
        if linea and not linea.startswith("#"):
            pats.append(linea)
    return pats


def cubierto_por_gitignore(ruta_rel, pats):
    """Devuelve el patrón que cubre al archivo, o None."""
    nombre = ruta_rel.name
    rel = ruta_rel.as_posix()
    for p in pats:
        clean = p.rstrip("/")
        if clean.startswith("/"):
            base = clean.lstrip("/")
            if fnmatch(rel, base) or fnmatch(rel, base + "/*"):
                return p
        else:
            if fnmatch(nombre, clean) or fnmatch(rel, clean) or fnmatch(rel, "*/" + clean):
                return p
    return None


def escanear_privacidad():
    """Devuelve (rojos, amarillos)."""
    rojos, amarillos = [], []
    pats = patrones_gitignore()

    for ruta in RAIZ.rglob("*"):
        if any(part in IGNORAR_TOTAL for part in ruta.parts):
            continue
        if not ruta.is_file():
            continue

        nombre_lower = ruta.name.lower()
        ruta_rel = ruta.relative_to(RAIZ)

        # 1) Nombre de archivo sensible, clasificado por .gitignore.
        for patron in ARCHIVOS_ROJOS:
            if patron in nombre_lower and "publica" not in nombre_lower:
                cubre = cubierto_por_gitignore(ruta_rel, pats)
                if cubre:
                    amarillos.append(
                        f"🟡 ARCHIVO SENSIBLE EN UBICACION CONTROLADA: {ruta_rel} "
                        f"(excluido por .gitignore: {cubre}). Verificar que la exclusion siga vigente."
                    )
                else:
                    rojos.append(
                        f"🔴 ARCHIVO SENSIBLE SIN EXCLUSION: {ruta_rel} "
                        f"(coincide con '{patron}'; agregalo al .gitignore o retiralo antes de publicar)"
                    )
                break

        # 2) Contenido (solo fuera de carpetas de herramientas).
        if any(part in EXCLUIR_CONTENIDO for part in ruta.parts):
            continue
        if ruta.suffix.lower() in EXTENSIONES_TEXTO:
            try:
                contenido = ruta.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue
            bajo = contenido.lower()
            for patron in TEXTOS_ROJOS:
                if patron in bajo:
                    rojos.append(f"🔴 CONTENIDO SENSIBLE: {ruta_rel} (contiene '{patron}')")
                    break
            else:
                for rx in REGEX_ROJOS:
                    if rx.search(contenido):
                        rojos.append(
                            f"🔴 CONTENIDO SENSIBLE: {ruta_rel} "
                            f"(coincide con forma real de secreto: {rx.pattern[:14]}...)"
                        )
                        break
    return rojos, amarillos


def escribir_manifiesto(carpeta):
    """Hashes de los artefactos de la carpeta (excepto el manifiesto mismo)."""
    archivos = sorted(p for p in carpeta.iterdir()
                      if p.is_file() and p.name != "manifiesto.json")
    man = {
        "generado_utc": ahora_utc(),
        "archivos": {p.name: sha256_archivo(p) for p in archivos},
        "bitacora_sha256": sha256_archivo(mod_verificar.BITACORA)
                           if mod_verificar.BITACORA.exists() else None,
    }
    ruta = carpeta / "manifiesto.json"
    ruta.write_text(json.dumps(man, indent=2, ensure_ascii=False), encoding="utf-8")
    return ruta


def generar_reporte(carpeta, res, rojos_priv, amarillos_priv, rojos, amarillos, estado):
    lineas = [
        "# Reporte de Auditoría STTM",
        f"**Fecha UTC:** {ahora_utc()}",
        f"**Proyecto:** #{res.get('proyecto_n', '?')} ({res.get('proyecto_ref', '?')})",
        "",
        "## 1. Integridad de la Bitácora",
        f"**Estado:** {'✅ Íntegra' if res['integra'] else '❌ Rota'}",
        f"**Entradas:** {res['entradas']} (verificadas: {res['entradas_verificadas']}, firmas canónicas válidas: {res['firmas_validadas']})",
        f"**Schemas:** v1={res['schemas']['v1']}, v2={res['schemas']['v2']}",
    ]
    if res["avisos"]:
        lineas.append("**Avisos:**")
        lineas.extend(f"- {a}" for a in res["avisos"])
    if res["problemas"]:
        lineas.append("**Problemas:**")
        lineas.extend(f"- {p}" for p in res["problemas"])
    lineas += ["", "## 2. Privacidad y Secretos (R14-15 / R20-15)"]
    if rojos_priv:
        lineas.append(f"**Rojos:** ❌ {len(rojos_priv)}")
        lineas.extend(f"- {h}" for h in rojos_priv)
    if amarillos_priv:
        lineas.append(f"**Ámbar:** ⚠️ {len(amarillos_priv)}")
        lineas.extend(f"- {h}" for h in amarillos_priv)
    if not rojos_priv and not amarillos_priv:
        lineas.append("**Estado:** ✅ No se detectaron archivos ni textos sensibles.")
    lineas += [
        "",
        "## 3. Resumen de hallazgos",
        f"- Rojos: {rojos}",
        f"- Amarillos: {amarillos}",
        f"- Estado final: **{estado}**",
        "",
        "## 4. Semántica de conteo",
        "- `firmas_validadas` cuenta solo verificaciones positivas del esquema canónico.",
        "- Las firmas HMAC legacy (incidente 001) se reconocen con aviso y no suman.",
        "",
        "## 5. Límites de esta auditoría",
        "- Esta auditoría es local y heurística.",
        "- No reemplaza una revisión humana exhaustiva antes de publicar.",
        "- La carpeta `scripts/` se excluye del escaneo de contenido (son herramientas).",
        "",
        "---",
        "*Generado por STTM `scripts/auditar.py` v2*"
    ]
    (carpeta / "reporte.md").write_text("\n".join(lineas), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description="Motor de auditoría STTM.")
    parser.add_argument("--proyecto", type=int, default=1)
    parser.add_argument("--motivo", default="Auditoría de rutina")
    parser.add_argument("--tipo", choices=("rapida", "estandar", "profunda"), default="rapida")
    args = parser.parse_args()

    print("🚀 Iniciando Auditoría STTM...")
    print("-" * 30)

    res = mod_verificar.verificar()
    if not res["existe"]:
        print(f"❌ No encuentro la bitácora: {res['ruta']}")
        return 1
    print(f"🔍 Verificando cadena: {res['entradas']} entradas, íntegra={res['integra']}")
    print("-" * 30)

    print("🕵️ Escaneando privacidad y secretos...")
    rojos_priv, amarillos_priv = escanear_privacidad()
    if rojos_priv:
        print(f"❌ Rojos: {len(rojos_priv)}")
        for h in rojos_priv:
            print(f"   {h}")
    if amarillos_priv:
        print(f"⚠️ Ámbar: {len(amarillos_priv)}")
        for h in amarillos_priv:
            print(f"   {h}")
    if not rojos_priv and not amarillos_priv:
        print("✅ Entorno limpio de secretos obvios.")
    print("-" * 30)

    rojos = len(rojos_priv) + len(res["problemas"])
    amarillos = len(amarillos_priv) + len(res["avisos"])
    estado = "no_apto" if rojos else ("apto_con_observaciones" if amarillos else "apto")

    try:
        estado_cat = proyectos.cargar_estado().get(args.proyecto, {})
        modo = estado_cat.get("nivel_actual", "continuidad")
        proyecto_ref = estado_cat.get("ref_interna")
    except Exception:
        modo, proyecto_ref = "continuidad", None

    ts = ahora_utc()
    carpeta = AUDITORIAS / stamp_carpeta()
    carpeta.mkdir(parents=True, exist_ok=True)

    res["proyecto_n"] = args.proyecto
    res["proyecto_ref"] = proyecto_ref
    generar_reporte(carpeta, res, rojos_priv, amarillos_priv, rojos, amarillos, estado)
    print(f"📄 Reporte guardado en: {carpeta.relative_to(RAIZ)}/reporte.md")

    ruta_man = escribir_manifiesto(carpeta)
    print(f"🧾 Manifiesto escrito en: {ruta_man.relative_to(RAIZ)}")

    meta = {
        "auditoria_id": auditoria_meta.nuevo_id(),
        "proyecto_n": args.proyecto,
        "proyecto_ref": proyecto_ref,
        "fecha_utc": ts,
        "motivo": args.motivo,
        "solicitante": {"rol": "autor", "nombre": "Martín José Dalberto"},
        "ejecutado_por": {"rol": "autor", "nombre": "Martín José Dalberto"},
        "tipo": args.tipo,
        "modo_aplicado": modo,
        "hallazgos": {"rojos": rojos, "amarillos": amarillos, "informativos": 0},
        "estado_final": estado,
        "cadena_integra": res["integra"],
        "entradas_verificadas": res["entradas_verificadas"],
        "entradas_totales": res["entradas"],
        "firmas_validadas": res["firmas_validadas"],
        "reporte_ruta": "reporte.md",
        "manifiesto_ruta": "manifiesto.json",
        "observaciones": res["avisos"] + amarillos_priv + rojos_priv,
    }
    try:
        ruta_meta = auditoria_meta.escribir_meta(carpeta, meta)
        print(f"✅ Meta de auditoría escrita en: {ruta_meta.relative_to(RAIZ)}")
    except FileExistsError as e:
        print(f"⚠️ {e}")

    try:
        cambios = auditoria_meta.actualizar_catalogo(args.proyecto, ts)
        print(f"✅ Catálogo actualizado: {cambios}")
    except Exception as e:
        print(f"ℹ️ Catálogo no actualizado ({e}); sigo sin catálogo (sandbox/CI).")

    # Rojo o cadena rota = fallo. Ámbar solo = advertencia, no fallo.
    return 0 if (res["integra"] and rojos == 0) else 1


if __name__ == "__main__":
    sys.exit(main())
