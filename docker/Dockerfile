# STTM v0.4 — Dockerfile
#
# ⚠️ NO PROBADO end-to-end en este entorno: el sandbox donde se escribió
# esta imagen no tiene salida de red (no puede hacer `docker build` ni
# bajar la imagen base `python:3.12-slim`). La sintaxis sigue el patrón
# estándar de Docker y no debería tener sorpresas, pero corré
# `docker build` vos y confirmalo antes de considerar esto "activo"
# (regla de oro del proyecto: lo no probado se declara pendiente).
#
# Este Dockerfile NO incluye TLS: STTM habla HTTP plano puerto 8000.
# Para HTTPS real, poné un reverse proxy delante (ver docker-compose.yml,
# que agrega Caddy con TLS automático). No reinventamos TLS en Python
# puro — es exactamente el tipo de cosa que un motor probado como
# Caddy/Traefik/nginx hace mejor y con menos superficie de error.

FROM python:3.12-slim

LABEL org.opencontainers.image.title="STTM" \
      org.opencontainers.image.description="Salem Traceability & Trust Method" \
      org.opencontainers.image.licenses="MIT"

# Usuario no-root: STTM guarda claves privadas (0o600) y contraseñas
# hasheadas; correr como root en el contenedor sería exponer más de lo
# necesario si algún día aparece una vulnerabilidad en una dependencia.
RUN groupadd -r sttm && useradd -r -g sttm -m -d /home/sttm sttm

WORKDIR /app

# Solo 'cryptography' es una dependencia real de STTM (Ed25519, Fernet).
# Todo lo demás es stdlib — es una decisión de diseño, no un descuido:
# menos dependencias externas = menos superficie de cadena de suministro
# para una herramienta que existe justamente para dar confianza.
RUN pip install --no-cache-dir cryptography

COPY --chown=sttm:sttm . /app

# data/ y auditorias/ deben persistir entre reinicios del contenedor:
# se montan como volúmenes (ver docker-compose.yml). Acá solo nos
# aseguramos de que existan con los permisos correctos si el volumen
# viene vacío (primer arranque).
RUN mkdir -p /app/data/claves/usuarios /app/data/claves/entradas /app/auditorias \
    && chown -R sttm:sttm /app/data /app/auditorias

USER sttm

EXPOSE 8000

# Sin --movil: dentro del contenedor "loopback" ya es 0.0.0.0 desde la
# perspectiva de Docker (el aislamiento de red lo da el propio
# contenedor, no bindear a loopback). El mapeo de puertos en
# docker-compose.yml es lo que controla qué es accesible desde afuera.
ENV STTM_ROOT=/app
CMD ["python", "scripts/servidor.py", "--movil"]
