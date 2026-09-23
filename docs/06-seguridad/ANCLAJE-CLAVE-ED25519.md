# ANCLAJE DE CLAVE Ed25519 — STTM (K-005)

**Estado:** anclada en el repo desde 2026-09-23 (commit STTM-0.16).
**Testigos externos:** 2 activos (email Gmail 18:10 y sello OpenTimestamps 18:43 del 2026-09-23; ver §3.1).

## 1. Decisión

Anclar la clave pública Ed25519 en el repositorio público para que
cualquier tercero verifique las firmas de la bitácora sin pedirle nada
al autor.

Declaración explícita de alcance: STTM no es ni pretende ser un HSM.
La clave privada vive en la máquina del autor; el anclaje protege la
clave de verificación, no la de firma. El modelo de amenazas sigue
siendo detección verificable de alteración, no prevención contra un
atacante con control de la máquina.

## 2. La clave

- Archivo público: data/claves/sofia_publica.pem (commiteado).
- Archivo privado: data/claves/sofia_privada.pem (jamás commiteado).
- Nombre: histórico, heredado de la ceremonia inicial (2026-09-23);
  el identificador verdadero es el fingerprint.
- Fingerprint SHA-256 del archivo público: 72afe372c4e48292f74b72b07fc61d5820e9e3989d30b39fe6bfa44f849a0541
- Uso: verificar entradas con firma_tipo ed25519 de BITACORA.jsonl.

## 3. Qué habilita este anclaje

- Terceros: clonar, verificar y confirmar que las firmas corresponden
  a la clave anclada, sin confiar en la palabra del autor.
- CI: verificación completa de entradas ed25519 (desaparece el aviso
  "clave pública ausente, verificación degradada").
- Testigos futuros: este fingerprint puede publicarse en medios
  externos (email propio, gist firmado, red social). Cada testigo que
  se agregue se registra en la bitácora con fecha y medio.

### 3.1 Testigos registrados

| # | Medio | Fecha | Detalle |
|---|---|---|---|
| 1 | Email Gmail | 2026-09-23 18:10 | Asunto: "STTM fingerprint K-005". Remitente: dalbertomartinjose3@gmail.com. Destinatarios: alejandrasalem2@gmail.com y salemlenguaje@gmail.com. Contenido: PEM completo de la clave pública y estado de cadena 21/21. Timestamp fijado por el proveedor de correo. Asentado en bitácora con retraso (entrada #23) por un bloque de trabajo no ejecutado; ver la propia entrada para el relato del salto. |
| 2 | OpenTimestamps (Bitcoin) | 2026-09-23 18:43 | Sello .ots sobre el PDF exportado del email del testigo #1, creado vía web en opentimestamps.org sin registro. Archivo en repo: docs/06-seguridad/testigos/testigo-01-gmail-k005.pdf.ots. SHA-256 del PDF original anclado en la entrada #22 de bitácora. El PDF no se commitea (contiene direcciones de correo): se conserva local y se provee a pedido. Estado: sellado por calendarios; attestation de Bitcoin pendiente de upgrade con el cliente ots. |

Ciclo de vida de los sellos: un archivo .ots se actualiza con
ots upgrade cuando Bitcoin confirma. Eso no edita el testigo: agrega
la attestation al mismo sello. Cada upgrade se anota debajo de esta
tabla con fecha y bloque, sin tocar las filas existentes. El archivo
upgraded se commitea; el anterior queda en el historial de git.

## 4. Qué NO habilita (límites honestos)

- No protege la clave privada: con ella robada, un atacante re-firma
  la bitácora y las firmas serían válidas contra esta clave anclada.
  La defensa contra ese caso es timestamping externo con testigos
  (capa siguiente, no implementada, declarada en CONTINUIDAD).
- Lo que sí detecta: reemplazo del par de claves. Quien re-firme con
  otra clave no puede coincidir con este fingerprint anclado.
- No convierte al repo en fuente de tiempo: los timestamps de la
  bitácora son declarativos del reloj del autor.

## 5. Rotación

Si la clave se rota o se compromete: entrada nueva de bitácora,
versión nueva de este documento con el fingerprint nuevo, y soporte
en verificar.py para claves por época (deuda declarada: hoy lee una
sola clave pública). Las entradas antiguas siguen verificando con la
clave de su época mientras se conserve el historial de anclajes.

## 6. Verificación para terceros

1. sha256sum data/claves/sofia_publica.pem debe coincidir con el
   fingerprint de la sección 2.
2. python scripts/verificar.py debe reportar cadena íntegra y las
   firmas ed25519 válidas contra esa clave.

## Historial

- v1, 2026-09-23: anclaje inicial (K-005), commit STTM-0.16,
  entrada #21 de bitácora.
