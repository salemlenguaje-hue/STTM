#!/usr/bin/env python3
"""
servidor.py — API local + estáticos del visor STTM (ADR-002, v2).

Lectura:
  GET  /api/bitacora                    entradas (más reciente primero)
  GET  /api/proyecto?n=                 estado del proyecto desde el catálogo
  GET  /api/documentos                  lista de .md (docs/ + CONTINUIDAD.md)
  GET  /api/documento?ruta=             contenido de un .md (texto plano)
  GET  /api/auditorias                  carpetas con resumen de meta.json
  GET  /api/reporte?carpeta=            reporte.md de una auditoría
  GET  /api/verificar-paquete?carpeta=  cadena + integridad del manifiesto

Escritura:
  POST /api/registrar                   nueva entrada de bitácora
  POST /api/modo                        cambio de nivel del proyecto
  POST /api/documento                   crear o actualizar documento .md
  POST /api/auditar                     ejecutar auditoría

Seguridad v2:
- Sin shell: todos los subprocess con lista de argumentos.
- Rutas validadas: sin '..', sufijo .md, dentro de docs/ o CONTINUIDAD.md.
- Nombres de carpeta de auditoría validados con regex estricta.
- Loopback por defecto; --movil abre a la red local (decisión declarada).
"""
import argparse
import hashlib
import http.server
import json
import os
import re
import socket
import socketserver
import subprocess
import sys
from pathlib import Path
from urllib.parse import urlparse, parse_qs

RAIZ = Path(os.environ.get("STTM_ROOT", Path(__file__).resolve().parent.parent))
WEB = RAIZ / "web"
SCRIPTS = RAIZ / "scripts"
BITACORA = RAIZ / "BITACORA.jsonl"
DOCS = RAIZ / "docs"
AUDITORIAS = RAIZ / "auditorias"

sys.path.insert(0, str(SCRIPTS))
import verificar as mod_verificar  # verificación estructurada, sin parsear texto

RE_CARPETA = re.compile(r"^\d{4}-\d{2}-\d{2}_\d{6}$")
MODOS = ("simple", "continuidad", "salem")
MODOS_FIRMA = ("hash", "hmac", "ed25519")


def correr_script(nombre, *args):
    env = os.environ.copy()
    env["STTM_ROOT"] = str(RAIZ)
    return subprocess.run(
        [sys.executable, str(SCRIPTS / nombre), *args],
        capture_output=True, text=True, env=env,
    )


def sha256_archivo(ruta):
    h = hashlib.sha256()
    with ruta.open("rb") as f:
        for bloque in iter(lambda: f.read(65536), b""):
            h.update(bloque)
    return h.hexdigest()


def ruta_documento_valida(ruta_rel):
    """Devuelve Path segura o None. Solo .md bajo docs/ o CONTINUIDAD.md."""
    if not ruta_rel or ".." in ruta_rel.split("/"):
        return None
    candidata = (RAIZ / ruta_rel).resolve()
    try:
        candidata.relative_to(RAIZ.resolve())
    except ValueError:
        return None
    if candidata.suffix.lower() != ".md":
        return None
    bajo_docs = False
    try:
        candidata.relative_to((RAIZ / "docs").resolve())
        bajo_docs = True
    except ValueError:
        pass
    es_continuidad = candidata == (RAIZ / "CONTINUIDAD.md").resolve()
    return candidata if (bajo_docs or es_continuidad) else None


def siguiente_numero(carpeta, prefijo):
    nums = [0]
    for p in carpeta.glob(prefijo + "-*"):
        m = re.match(re.escape(prefijo) + r"-STTM-(\d+)", p.name)
        if m:
            nums.append(int(m.group(1)))
    return max(nums) + 1


def slug(texto):
    s = re.sub(r"[^a-z0-9]+", "-", texto.lower()).strip("-")
    return s or "sin-titulo"


class STTMHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(WEB), **kwargs)

    def log_message(self, fmt, *a):
        pass  # silencio el log por defecto

    def send_json(self, obj, code=200):
        body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-type", "application/json; charset=utf-8")
        self.send_header("Content-length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def send_texto(self, texto, code=200):
        body = texto.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-type", "text/plain; charset=utf-8")
        self.send_header("Content-length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def leer_json(self):
        largo = int(self.headers.get("Content-Length", 0))
        crudo = self.rfile.read(largo) if largo else b"{}"
        try:
            return json.loads(crudo.decode("utf-8"))
        except Exception:
            return None

    # ---------------- lectura ----------------
    def do_GET(self):
        parsed = urlparse(self.path)
        q = parse_qs(parsed.query)

        if parsed.path == "/api/bitacora":
            entradas = []
            if BITACORA.exists():
                for linea in BITACORA.read_text(encoding="utf-8").splitlines():
                    if linea.strip():
                        entradas.append(json.loads(linea))
            return self.send_json(entradas[::-1])

        if parsed.path == "/api/proyecto":
            r = correr_script("proyectos.py", "listar", "--json")
            if r.returncode != 0:
                return self.send_json({"error": r.stderr.strip()}, 500)
            lista = json.loads(r.stdout)
            activos = [p for p in lista if p.get("activo")]
            if not activos:
                return self.send_json({"error": "no hay proyectos activos"}, 404)
            n = q.get("n", [str(activos[0]["n"])])[0]
            elegido = next((p for p in lista if str(p.get("n")) == n), None)
            if elegido is None:
                return self.send_json({"error": f"proyecto {n} no existe"}, 404)
            return self.send_json({"proyecto": elegido, "activos": activos})

        if parsed.path == "/api/documentos":
            docs = [str(p.relative_to(RAIZ)) for p in DOCS.rglob("*.md")]
            if (RAIZ / "CONTINUIDAD.md").exists():
                docs.append("CONTINUIDAD.md")
            return self.send_json(sorted(docs))

        if parsed.path == "/api/documento":
            ruta = ruta_documento_valida(q.get("ruta", [""])[0])
            if ruta is None or not ruta.exists():
                return self.send_json({"error": "ruta no autorizada o inexistente"}, 404)
            return self.send_texto(ruta.read_text(encoding="utf-8"))

        if parsed.path == "/api/auditorias":
            salida = []
            if AUDITORIAS.exists():
                for carpeta in sorted(AUDITORIAS.iterdir(), reverse=True):
                    if not carpeta.is_dir() or not RE_CARPETA.match(carpeta.name):
                        continue
                    item = {"carpeta": carpeta.name}
                    meta = carpeta / "meta.json"
                    if meta.exists():
                        try:
                            m = json.loads(meta.read_text(encoding="utf-8"))
                            item.update({
                                "auditoria_id": m.get("auditoria_id"),
                                "fecha": m.get("fecha_utc"),
                                "motivo": m.get("motivo"),
                                "estado": m.get("estado_final"),
                                "hallazgos": m.get("hallazgos"),
                            })
                        except Exception:
                            item["error_meta"] = True
                    else:
                        # Auditorias previas a ADR-003 no tienen meta.json:
                        # se declaran como sin metadatos; no se inventan datos.
                        item["sin_meta"] = True
                    salida.append(item)
            return self.send_json(salida)

        if parsed.path == "/api/reporte":
            nombre = q.get("carpeta", [""])[0]
            if not RE_CARPETA.match(nombre):
                return self.send_json({"error": "carpeta inválida"}, 400)
            reporte = AUDITORIAS / nombre / "reporte.md"
            if not reporte.exists():
                return self.send_json({"error": "reporte inexistente"}, 404)
            return self.send_json({"carpeta": nombre,
                                   "contenido": reporte.read_text(encoding="utf-8")})

        if parsed.path == "/api/verificar-paquete":
            nombre = q.get("carpeta", [""])[0]
            if not RE_CARPETA.match(nombre):
                return self.send_json({"error": "carpeta inválida"}, 400)
            carpeta = AUDITORIAS / nombre
            res = mod_verificar.verificar()
            cadena = {
                "integra": res["integra"],
                "entradas": res["entradas"],
                "verificadas": res["entradas_verificadas"],
                "avisos": res["avisos"],
                "problemas": res["problemas"],
            }
            manifiesto = None
            ruta_man = carpeta / "manifiesto.json"
            if ruta_man.exists():
                m = json.loads(ruta_man.read_text(encoding="utf-8"))
                detalles, ok = [], True
                for nombre_arch, hash_guardado in (m.get("archivos") or {}).items():
                    p = carpeta / nombre_arch
                    if not p.exists():
                        detalles.append(f"{nombre_arch}: falta archivo")
                        ok = False
                    elif sha256_archivo(p) != hash_guardado:
                        detalles.append(f"{nombre_arch}: hash distinto")
                        ok = False
                nota_bit = None
                bit_guardado = m.get("bitacora_sha256")
                bit_actual = sha256_archivo(BITACORA) if BITACORA.exists() else None
                if bit_guardado and bit_actual != bit_guardado:
                    nota_bit = ("la bitácora cambió después de esta auditoría "
                                "(esperado si hubo registros posteriores)")
                manifiesto = {"ok": ok, "detalles": detalles, "nota_bitacora": nota_bit}
            return self.send_json({"carpeta": nombre, "cadena": cadena,
                                   "manifiesto": manifiesto})

        return super().do_GET()

    # ---------------- escritura ----------------
    def do_POST(self):
        parsed = urlparse(self.path)
        datos = self.leer_json()
        if datos is None:
            return self.send_json({"error": "JSON inválido"}, 400)

        if parsed.path == "/api/registrar":
            titulo = (datos.get("titulo") or "").strip()
            detalle = (datos.get("detalle") or "").strip()
            modo = datos.get("modo_firma", "hash")
            if not titulo or not detalle:
                return self.send_json({"error": "titulo y detalle son obligatorios"}, 400)
            if modo not in MODOS_FIRMA:
                return self.send_json({"error": f"modo de firma inválido: {modo}"}, 400)
            args = [titulo, detalle, "--modo-firma", modo]
            archivos = (datos.get("archivos") or "").strip()
            if archivos:
                args += ["--archivos", archivos]
            commit = (datos.get("commit") or "").strip()
            if commit:
                args += ["--commit", commit]
            r = correr_script("registrar.py", *args)
            return self.send_json({"ok": r.returncode == 0, "rc": r.returncode,
                                   "stdout": r.stdout.strip(),
                                   "stderr": r.stderr.strip()})

        if parsed.path == "/api/modo":
            nivel = datos.get("nivel")
            if nivel not in MODOS:
                return self.send_json({"error": f"nivel inválido: {nivel}"}, 400)
            n = str(datos.get("n", 1))
            motivo = (datos.get("motivo") or "cambio desde la interfaz").strip()
            r = correr_script("proyectos.py", "nivel", "--n", n,
                              "--nivel", nivel, "--motivo", motivo)
            if r.returncode != 0:
                return self.send_json({"ok": False, "error": r.stdout.strip()}, 400)
            r2 = correr_script("registrar.py",
                               f"Cambio de modo del proyecto #{n} a {nivel}",
                               f"Solicitado desde la interfaz. Motivo: {motivo}",
                               "--archivos", "data/proyectos.jsonl",
                               "--modo-firma", "hash")
            return self.send_json({"ok": True, "stdout": r.stdout.strip(),
                                   "registro": r2.stdout.strip()})

        if parsed.path == "/api/documento":
            cuerpo = datos.get("cuerpo") or ""
            ruta_rel = (datos.get("ruta") or "").strip()
            if ruta_rel:
                ruta = ruta_documento_valida(ruta_rel)
                if ruta is None:
                    return self.send_json({"error": "ruta no autorizada"}, 400)
                creada = not ruta.exists()
            else:
                tipo = datos.get("tipo", "otro")
                titulo = (datos.get("titulo") or "").strip()
                if not titulo:
                    return self.send_json({"error": "titulo obligatorio para crear"}, 400)
                if tipo == "gob":
                    carpeta, pref = DOCS / "00-gobernanza", "GOB"
                    nombre = f"{pref}-STTM-{siguiente_numero(carpeta, pref):03d}-{slug(titulo)}.md"
                elif tipo == "adr":
                    carpeta, pref = DOCS / "02-arquitectura", "ADR"
                    nombre = f"{pref}-STTM-{siguiente_numero(carpeta, pref):03d}-{slug(titulo)}.md"
                elif tipo == "metodo":
                    carpeta = DOCS / "01-metodo"
                    nombre = f"{slug(titulo)}.md"
                else:
                    carpeta = DOCS
                    nombre = f"{slug(titulo)}.md"
                carpeta.mkdir(parents=True, exist_ok=True)
                ruta = carpeta / nombre
                creada = not ruta.exists()
            ruta.parent.mkdir(parents=True, exist_ok=True)
            ruta.write_text(cuerpo, encoding="utf-8")
            rel = str(ruta.relative_to(RAIZ))
            r2 = correr_script("registrar.py",
                               f"Documento {'creado' if creada else 'actualizado'}: {rel}",
                               "Guardado desde el editor de la interfaz (ADR-002).",
                               "--archivos", rel, "--modo-firma", "hash")
            return self.send_json({"ok": True, "creada": creada, "ruta": rel,
                                   "registro": r2.stdout.strip()})

        if parsed.path == "/api/auditar":
            motivo = (datos.get("motivo") or "Auditoría desde la interfaz").strip()
            tipo = datos.get("tipo", "rapida")
            if tipo not in ("rapida", "estandar", "profunda"):
                return self.send_json({"error": "tipo inválido"}, 400)
            r = correr_script("auditar.py", "--proyecto", "1",
                              "--motivo", motivo, "--tipo", tipo)
            carpeta = None
            if AUDITORIAS.exists():
                dirs = [d.name for d in sorted(AUDITORIAS.iterdir(), reverse=True)
                        if d.is_dir() and RE_CARPETA.match(d.name)]
                carpeta = dirs[0] if dirs else None
            return self.send_json({"ok": r.returncode == 0, "rc": r.returncode,
                                   "stdout": r.stdout.strip(), "carpeta": carpeta})

        return self.send_json({"error": "endpoint desconocido"}, 404)


def main():
    parser = argparse.ArgumentParser(description="Servidor local del visor STTM.")
    parser.add_argument("--movil", action="store_true",
                        help="escucha en 0.0.0.0 (red local). Por defecto: loopback.")
    args = parser.parse_args()
    host = "0.0.0.0" if args.movil else "127.0.0.1"
    port = int(os.environ.get("STTM_PORT", "8000"))
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer((host, port), STTMHandler) as httpd:
        print(f"✅ Servidor STTM corriendo en http://{host}:{port}")
        if args.movil:
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                s.connect(("8.8.8.8", 80))
                print(f"📱 Desde tu celular (misma WiFi): http://{s.getsockname()[0]}:{port}")
                s.close()
            except Exception:
                pass
        print("Ctrl+C para detener.")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n🛑 Servidor detenido.")


if __name__ == "__main__":
    main()
