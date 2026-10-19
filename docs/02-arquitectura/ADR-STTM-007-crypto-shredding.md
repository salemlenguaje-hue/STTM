# ADR-STTM-007 — Crypto-shredding (borrado seguro compatible con inmutabilidad)

**SALEM**
**STTM — ADR-007: CRYPTO-SHREDDING**
Borrador de trabajo interno

Argentina, 2026

## 1. Control documental

| Dato | Definición |
|---|---|
| Identificador | STTM-ADR-007-2026-R1 |
| Estado | Borrador de trabajo interno, pendiente de revisión |
| Alcance | Define cómo STTM puede cumplir con un pedido de borrado de datos personales (tipo GDPR / Ley 25.326 de Argentina) sin violar la inmutabilidad de la bitácora. |
| Antecedentes | Discusión sobre requisitos empresariales; ADR-STTM-001 (modelo de evidencia: "la bitácora es sagrada"). |

## 2. Contexto

STTM promete un ledger append-only e inmutable. Una empresa con obligaciones de protección de datos en algún momento va a necesitar poder decir, de forma real y verificable, "borramos el dato personal de esta persona". Estos dos requisitos son, en apariencia, incompatibles: un ledger genuinamente inmutable no puede borrar nada.

## 3. Decisión

Adoptar **crypto-shredding** (o "crypto-erasure"), un patrón estándar en sistemas de ledger con este requisito:

1. El campo `detalle` de una entrada marcada como sensible no se guarda en texto plano: se cifra (Fernet/AES-128) con una clave simétrica generada una única vez para esa entrada (`cifrado.py`).
2. Esa clave se guarda aparte, un archivo chico por entrada (`data/claves/entradas/<n>.key`, permisos 0o600) — nunca dentro del ledger.
3. El ledger guarda el ciphertext y el hash SHA-256 del contenido en claro: la cadena de integridad sigue intacta y verificable sin necesidad de poder leer el contenido.
4. **"Triturar" una entrada = borrar solo su archivo `.key`.** El ciphertext que queda en el ledger es, desde ese momento, ruido computacionalmente irrecuperable. El evento (que existió, cuándo, con qué hash) permanece para siempre en la cadena, como cualquier evento de un ledger inmutable — pero su *contenido* deja de ser accesible.

## 4. Consecuencias

- Un DPO o auditor de privacidad puede pedir "mostrame que el dato de esta persona ya no es recuperable" y STTM puede responder: la clave no existe, el intento de descifrado falla por diseño, y hay una constancia local (fuera del ledger) de cuándo y por qué se trituró (`_triturados.jsonl` en la carpeta de claves).
- Este manifiesto de trituración vive **fuera** del ledger deliberadamente: no es un evento de negocio del proyecto auditado, es una acción de administración de datos personales, y mezclar ambos contaminaría la bitácora canónica.

## 5. Límites declarados (no es asesoría legal)

- No borra el campo `titulo`: se asume no-personal por convención. Si un título contiene datos personales, es un error de uso que `cifrado.py` no puede detectar por sí solo.
- Esto cumple con "no se puede volver a acceder al dato personal", no con "el evento nunca existió". Para la mayoría de los marcos de protección de datos esta es la distinción que aceptan, pero confirmarlo para un caso concreto es trabajo de un equipo de compliance/legal real, no de este documento.
- Si alguien hizo un backup manual del directorio de claves antes de triturar, ese backup queda fuera del control de STTM — la herramienta no puede proteger contra decisiones de infraestructura tomadas por fuera de ella.
