# INSTALACION.md — STTM v0.4

Tres caminos: **Termux (Android)**, **Linux/macOS** y **Docker**. Elegí uno.
Al final hay una sección común de primeros pasos (crear el primer usuario
admin) y una de validación manual del testigo RFC 3161 (BETA, requiere red).

---

## A. Termux (Android) — el mismo flujo que ya usás para Salem

1. Si no tenés Termux con Python, en una Termux nueva:
   ```
   pkg update && pkg upgrade
   pkg install python git
   ```
2. Descomprimí este paquete donde ya trabajás tus proyectos, por ejemplo:
   ```
   mkdir -p ~/proyectos && cd ~/proyectos
   unzip sttm-v0.4.zip -d sttm
   cd sttm
   ```
3. Instalá la única dependencia real (todo lo demás es stdlib):
   ```
   pip install cryptography
   ```
4. Seguí a la sección **C. Primeros pasos (todos los caminos)** más abajo.
5. Para levantar el servidor accesible desde el resto de tu red local
   (por ejemplo, para probar desde el navegador de una PC en la misma wifi):
   ```
   export STTM_ROOT=$(pwd)
   python scripts/servidor.py --movil
   ```
   ⚠️ **Antes de usar `--movil` en la wifi de la escuela (CEP N° 40) o
   cualquier red compartida**: sin esto, cualquier dispositivo en esa
   red podría llegar a los endpoints de la API. En v0.4 todos los
   endpoints ya exigen login, así que el riesgo bajó mucho respecto a
   v0.3 — pero seguí siendo consciente de que "accesible desde la red"
   y "accesible desde internet" no son lo mismo: `--movil` es para la
   wifi del aula, nunca para exponerlo directo a internet sin el
   Docker+Caddy de la sección B.

---

## B. Linux / macOS (servidor propio o de una empresa)

1. Requisitos: Python 3.10 o más nuevo.
   ```
   python3 --version
   ```
2. Descomprimir y entrar al directorio:
   ```
   unzip sttm-v0.4.zip -d sttm && cd sttm
   ```
3. Entorno virtual (recomendado, para no mezclar con otros proyectos Python):
   ```
   python3 -m venv .venv
   source .venv/bin/activate
   pip install cryptography
   ```
4. Seguí a la sección **C**.
5. Para producción de verdad (no solo probar), usá Docker (sección D) en vez
   de correr `servidor.py` pelado: `http.server` de Python no está pensado
   para manejar tráfico real ni TLS.

### Systemd (opcional, para que el servidor sobreviva reinicios)

```ini
# /etc/systemd/system/sttm.service
[Unit]
Description=STTM — Salem Traceability & Trust Method
After=network.target

[Service]
Type=simple
User=sttm
WorkingDirectory=/opt/sttm
Environment=STTM_ROOT=/opt/sttm
ExecStart=/opt/sttm/.venv/bin/python scripts/servidor.py
Restart=on-failure

[Install]
WantedBy=multi-user.target
```
```
sudo systemctl enable --now sttm
```
Esto tampoco se probó en este entorno (sin systemd disponible en el
sandbox de desarrollo) — es la sintaxis estándar de una unit file simple,
pero confirmalo en tu máquina.

---

## C. Primeros pasos (todos los caminos)

1. **Crear el primer usuario administrador** (te va a pedir la contraseña
   de forma interactiva, nunca la escribas como argumento en la terminal):
   ```
   export STTM_ROOT=$(pwd)
   python scripts/identidad.py crear admin --rol admin --nombre-completo "Tu Nombre"
   ```
2. **Crear el resto del equipo**, con el rol que corresponda:
   ```
   python scripts/identidad.py crear ana --rol auditor --nombre-completo "Ana Pérez"
   python scripts/identidad.py crear bruno --rol lector --nombre-completo "Bruno Gómez"
   ```
3. **Verificar que quedaron bien creados**:
   ```
   python scripts/identidad.py listar
   ```
4. **Levantar el servidor** (modo local, sin `--movil`):
   ```
   python scripts/servidor.py
   ```
5. Abrir `http://localhost:8000` en el navegador. Vas a ver la pantalla de
   login nueva — entrá con el usuario admin que creaste en el paso 1.
6. **Registrar tu primera entrada por CLI** (útil para probar sin la UI,
   o para integrarlo a un script propio):
   ```
   python scripts/registrar.py "Instalación completada" \
     "Primer registro de prueba de STTM v0.4" --actor admin
   ```
7. **Verificar la cadena**:
   ```
   python scripts/verificar.py data/proyectos/1-STTM/BITACORA.jsonl
   ```

### Git hook de registro automático (opcional)

```
git config sttm.actor admin   # tu usuario STTM, no tu usuario de git
cp hooks/post-commit .git/hooks/post-commit
chmod +x .git/hooks/post-commit
```
Desde el próximo commit en ese repo, cada uno queda registrado solo. Si
`sttm.actor` no está configurado, el hook avisa y no hace nada — nunca
bloquea un commit por esto.

### Cron sugerido para el índice de búsqueda (si el ledger crece mucho)

`/api/buscar` reconstruye el índice en cada consulta (ver ADR-006), lo
cual es correcto pero deja de ser instantáneo con ledgers muy grandes.
Si eso pasa, movelo a un cron y dejá de reconstruir en cada request
(requiere un cambio chico en `servidor.py`, no incluido en esta versión):
```
# crontab -e
*/15 * * * * cd /opt/sttm && STTM_ROOT=/opt/sttm python3 scripts/indice.py --proyecto 1
```

---

## D. Docker (recomendado para un despliegue real de empresa)

⚠️ **No se pudo correr `docker build` ni `docker compose up` en el entorno
donde se escribió esto (sin salida de red)**. La sintaxis sigue el patrón
estándar de Docker Compose v2 y no debería dar sorpresas, pero validalo
vos con `docker compose config` antes de confiar en que anda.

1. Sin dominio propio todavía (para probar en tu red local, SIN TLS):
   - Editá `docker/docker-compose.yml`: comentá el servicio `caddy` entero
     y descomentá la línea `ports: ["8000:8000"]` bajo `sttm`.
   - ```
     docker compose -f docker/docker-compose.yml up -d --build
     ```
   - Abrí `http://localhost:8000`.

2. Con dominio propio (producción, con TLS automático vía Caddy):
   - Editá `docker/Caddyfile` si hace falta.
   - ```
     export STTM_DOMINIO=sttm.tuempresa.com
     docker compose -f docker/docker-compose.yml up -d --build
     ```
   - Esperá un minuto a que Caddy obtenga el certificado de Let's Encrypt
     (necesita que el DNS de ese dominio ya apunte a este servidor y que
     los puertos 80/443 estén abiertos).

3. Crear el primer usuario admin **dentro** del contenedor:
   ```
   docker compose -f docker/docker-compose.yml exec sttm \
     python scripts/identidad.py crear admin --rol admin
   ```

4. Los datos (`data/`, `auditorias/`) viven en volúmenes con nombre
   (`sttm_datos`, `sttm_auditorias`): sobreviven a `docker compose down`,
   se pierden solo con `docker compose down -v`. Hacé backup de esos
   volúmenes con la herramienta de backup que ya uses para Docker en tu
   organización.

---

## E. Validación manual del testigo RFC 3161 (BETA — requiere red real)

Este módulo no se pudo probar contra una TSA real durante el desarrollo
(ver ADR-008). Una vez que tengas red de verdad (Termux con datos
móviles, tu Linux con internet, etc.):

```
export STTM_ROOT=$(pwd)
python scripts/testigo_rfc3161.py probar README.md
```

Si ves `✅ Sello de tiempo CONCEDIDO`, andá a
`docs/02-arquitectura/ADR-STTM-008-testigo-rfc3161.md` y actualizá el
estado de "BETA" a "activo", con la fecha y la TSA usada como evidencia
— y dejalo registrado en la bitácora:
```
python scripts/registrar.py \
  "Validación end-to-end del testigo RFC 3161" \
  "Confirmado contra freetsa.org el <fecha>. Ver ADR-008." \
  --actor admin
```

---

## F. Qué hacer si algo de esto no funciona

Todo lo marcado ⚠️ en este documento es honesto: no se probó de punta a
punta en el entorno donde se escribió (sin red de salida). Si algo falla,
lo más probable es un detalle de tu entorno específico (versión de
Python, permisos de Docker, DNS), no un error conceptual de diseño. Downgrade
seguro si algo no anda: corré `python scripts/servidor.py` sin Docker ni
`--movil` — ese camino sí se probó exhaustivamente (80 tests automatizados,
incluyendo levantar el servidor real y pegarle por HTTP).
