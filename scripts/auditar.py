#!/usr/bin/env python3
"""
auditar.py — Motor de auditoría local para STTM.

Ejecuta chequeos de integridad y privacidad antes de publicar.
Alineado a R14-15 (Tomo I) y R20-15 (Tomo II): la distribución 
pública no debe incluir fuentes privadas ni datos del creador.
"""
import subprocess
import sys
from pathlib import Path
from datetime import datetime, timezone

RAIZ = Path(__file__).resolve().parent.parent
AUDITORIAS = RAIZ / "auditorias"

# --- Reglas de Privacidad ---
# Nombres de archivo que NUNCA deberían estar en un repo público.
ARCHIVOS_ROJOS = [
    ".key", ".pem", "id_rsa", "id_ed25519", 
    ".env", "secret", "token", "password",
    "sofia_salem.key", "experimentos.db" # Protegemos datos de Sofía
]

# Patrones de texto que indican secretos hardcodeados.
TEXTOS_ROJOS = [
    "-----begin private key",
    "-----begin openssh private key",
    "password=", "api_key=", "secret_key=",
    "ghp_" # Tokens clásicos de GitHub
]

EXTENSIONES_TEXTO = {".md", ".txt", ".json", ".jsonl", ".py", ".html", ".css", ".js", ".sh"}

def verificar_bitacora():
    """Ejecuta verificar.py y captura su salida."""
    script_verificar = RAIZ / "scripts" / "verificar.py"
    if not script_verificar.exists():
        return False, "No se encontró scripts/verificar.py"
    
    resultado = subprocess.run(
        [sys.executable, str(script_verificar)],
        capture_output=True, text=True
    )
    return resultado.returncode == 0, resultado.stdout.strip()

def escanear_privacidad():
    """Busca archivos y textos sensibles en el proyecto."""
    hallazgos = []
    ignorar = {".git", "auditorias", "__pycache__", "node_modules"}
    
    for ruta in RAIZ.rglob("*"):
        if any(part in ignorar for part in ruta.parts):
            continue
            
        if ruta.is_file():
            nombre_lower = ruta.name.lower()
            ruta_rel = ruta.relative_to(RAIZ)
            
            # 1. Chequeo de nombre de archivo
            for patron in ARCHIVOS_ROJOS:
                if patron in nombre_lower:
                    hallazgos.append(f"🔴 ARCHIVO SENSIBLE: {ruta_rel} (coincide con '{patron}')")
                    break
            
            # 2. Chequeo de contenido (solo textos)
            if ruta.suffix.lower() in EXTENSIONES_TEXTO:
                try:
                    contenido = ruta.read_text(encoding="utf-8", errors="ignore").lower()
                    for patron in TEXTOS_ROJOS:
                        if patron in contenido:
                            hallazgos.append(f"🔴 CONTENIDO SENSIBLE: {ruta_rel} (contiene '{patron}')")
                            break
                except Exception:
                    pass
                    
    return hallazgos

def generar_reporte(ok_bitacora, msg_bitacora, hallazgos_privacidad):
    """Crea un reporte Markdown con los resultados."""
    AUDITORIAS.mkdir(exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d_%H%M%S")
    carpeta_reporte = AUDITORIAS / timestamp
    carpeta_reporte.mkdir()
    
    archivo_reporte = carpeta_reporte / "reporte.md"
    
    lineas = [
        f"# Reporte de Auditoría STTM",
        f"**Fecha UTC:** {timestamp}",
        f"**Proyecto:** STTM (Línea base local)",
        "",
        "## 1. Integridad de la Bitácora",
        f"**Estado:** {'✅ Íntegra' if ok_bitacora else '❌ Rota'}",
        "```",
        msg_bitacora,
        "```",
        "",
        "## 2. Privacidad y Secretos (R14-15 / R20-15)",
    ]
    
    if hallazgos_privacidad:
        lineas.append(f"**Estado:** ❌ Se encontraron {len(hallazgos_privacidad)} alerta(s).")
        lineas.append("")
        for h in hallazgos_privacidad:
            lineas.append(f"- {h}")
    else:
        lineas.append("**Estado:** ✅ No se detectaron archivos ni textos sensibles obvios.")
        
    lineas.extend([
        "",
        "## 3. Límites de esta auditoría",
        "- Esta auditoría es local y heurística.",
        "- No reemplaza una revisión humana exhaustiva antes de publicar.",
        "- No verifica firmas criptográficas asimétricas (modo hash actual).",
        "",
        "---",
        "*Generado por STTM `scripts/auditar.py`*"
    ])
    
    archivo_reporte.write_text("\n".join(lineas), encoding="utf-8")
    return carpeta_reporte.relative_to(RAIZ)

def main():
    print("🚀 Iniciando Auditoría STTM...")
    print("-" * 30)
    
    print("🔍 Verificando cadena de evidencia...")
    ok_bitacora, msg_bitacora = verificar_bitacora()
    print(msg_bitacora)
    print("-" * 30)
    
    print("🕵️ Escaneando privacidad y secretos...")
    hallazgos = escanear_privacidad()
    if hallazgos:
        print(f"❌ Alertas encontradas: {len(hallazgos)}")
        for h in hallazgos:
            print(f"   {h}")
    else:
        print("✅ Entorno limpio de secretos obvios.")
    print("-" * 30)
    
    print("📄 Generando reporte...")
    ruta_reporte = generar_reporte(ok_bitacora, msg_bitacora, hallazgos)
    print(f"✅ Reporte guardado en: {ruta_reporte}/reporte.md")
    
    sys.exit(0 if (ok_bitacora and not hallazgos) else 1)

if __name__ == "__main__":
    main()
