# El método STTM, en cuatro ideas

Este documento explica el método en sí, separado de la implementación
(el "cómo" vive en los ADRs de `docs/02-arquitectura/`).

## 1. Registro append-only

Cada evento relevante de un proyecto —una decisión, un incidente, un
cambio— se agrega como una línea nueva a un archivo de texto plano
(`BITACORA.jsonl`). Nunca se edita ni se borra una línea ya escrita.
Si algo estaba mal, se agrega una entrada nueva que lo corrige o lo
aclara — el error queda, con su corrección al lado, en vez de
desaparecer.

## 2. Encadenamiento por hash

Cada entrada incluye el hash de la entrada anterior (`hash_prev`). Esto
convierte la bitácora en una cadena: modificar una entrada vieja (aunque
sea un espacio) cambia su hash, lo cual rompe el `hash_prev` de la
entrada siguiente, y así en cascada hasta el final. `verificar.py`
detecta esto recorriendo la cadena entera.

## 3. Firma por identidad real

Desde v0.4 (schema v3, ver ADR-004 y ADR-005), cada entrada se firma con
la clave Ed25519 propia de la persona autenticada que la generó — no con
una clave compartida por todo un equipo. Esto responde la pregunta que
un ledger sin identidad no puede responder: no solo "esto no cambió",
sino "esto lo hizo, verificablemente, esta persona".

## 4. Verificación independiente del código propio

Todo lo anterior usa estándares públicos (RFC 8785 para la
canonicalización, RFC 8032 para las firmas Ed25519) en vez de formatos
propios. La idea no es "confiá en `verificar.py`" — es "cualquiera puede
escribir su propio verificador desde estos RFCs y llegar al mismo
resultado". Un método que solo se puede auditar con el código de quien
lo escribió no es, en un sentido importante, un método auditable.

## Lo que este método no resuelve por sí solo

Un ledger íntegro y bien firmado no dice si el contenido de una entrada
es verdadero, solo que no cambió después de escrita. La honestidad del
contenido sigue siendo responsabilidad de quien lo escribe — el método
solo garantiza que, sea lo que sea que haya escrito, quede fijado y
atribuido para siempre.
