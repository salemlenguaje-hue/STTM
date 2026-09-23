#!/usr/bin/env python3
"""
servidor.py — Servidor local para el Visor STTM.
Sirve la interfaz web y expone la bitácora y documentos como API.
Alineado a R14-06 (Tomo I): Loopback por defecto, con modo móvil para desarrollo.
"""
import http.server
import socketserver
import json
import os
import sys
import socket
from pathlib import Path
from urllib.parse import urlparse, parse_qs

RAIZ = Path(__file__).resolve().parent.parent
WEB = RAIZ / "web"
BITACORA = RAIZ / "BITACORA.jsonl"
DOCS = RAIZ / "docs"

PORT = 8000

class STTMHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        # Servimos los archivos estáticos desde la carpeta web/
        super().__init__(*args, directory=str(WEB), **kwargs)

    def do_GET(self):
        parsed = urlparse(self.path)
        
        # API: Leer bitácora completa
        if parsed.path == "/api/bitacora":
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            entradas = []
            if BITACORA.exists():
                for linea in BITACORA.read_text(encoding="utf-8").splitlines():
                    if linea.strip():
                        entradas.append(json.loads(linea))
            # Invertir para mostrar lo más reciente primero
            self.wfile.write(json.dumps(entradas[::-1], ensure_ascii=False).encode("utf-8"))
            return
        
        # API: Listar documentos Markdown
        elif parsed.path == "/api/documentos":
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            docs = []
            for p in DOCS.rglob("*.md"):
                docs.append(str(p.relative_to(RAIZ)))
            self.wfile.write(json.dumps(docs, ensure_ascii=False).encode("utf-8"))
            return

        # API: Leer un documento específico
        elif parsed.path == "/api/documento":
            qs = parse_qs(parsed.query)
            ruta = qs.get("ruta", [""])[0]
            # Seguridad: evitar salir de la carpeta del proyecto
            ruta_limpia = os.path.normpath(ruta)
            if ruta_limpia.startswith("..") or not ruta_limpia.startswith("docs"):
                self.send_error(403, "Ruta no autorizada")
                return
            
            archivo = RAIZ / ruta_limpia
            if archivo.exists() and archivo.suffix == ".md":
                self.send_response(200)
                self.send_header("Content-type", "text/plain; charset=utf-8")
                self.end_headers()
                self.wfile.write(archivo.read_text(encoding="utf-8").encode("utf-8"))
            else:
                self.send_error(404, "Documento no encontrado")
            return

        # Si no es API, servir archivos estáticos (HTML/CSS/JS)
        super().do_GET()

def main():
    movil = "--movil" in sys.argv
    host = "0.0.0.0" if movil else "127.0.0.1"
    
    with socketserver.TCPServer((host, PORT), STTMHandler) as httpd:
        print(f"✅ Servidor STTM corriendo.")
        print(f"🌐 Interfaz local: http://127.0.0.1:{PORT}")
        if movil:
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                s.connect(("8.8.8.8", 80))
                ip_local = s.getsockname()[0]
                s.close()
                print(f"📱 Desde tu celular (misma WiFi): http://{ip_local}:{PORT}")
            except Exception:
                pass
        print("Presiona Ctrl+C para detener.")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n🛑 Servidor detenido.")

if __name__ == "__main__":
    main()
