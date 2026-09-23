# ADR-STTM-001 — Modelo de evidencia, modos y arranque en Termux

**SALEM**  
**STTM — ADR-001: MODELO DE EVIDENCIA, MODOS Y ARRANQUE EN TERMUX**  
Línea base inicial  

Autor del proyecto  
Martín José Dalberto  
Argentina, 2026  

## 1. Control documental

| Dato | Definición |
|---|---|
| Identificador interno | STTM-ADR-001-2026-R1 |
| Estado | Línea base inicial |
| Alcance | Define el modelo de evidencia de STTM, los modos de uso, la carpeta de trabajo, el registro obligatorio y los límites iniciales de firma criptográfica. |
| Autor | Martín José Dalberto, Argentina. |
| Antecedentes | GOB-STTM-001; Plantilla de Documento Salem; Sistema de Calidad y Procesos v0.1; Tomo I de Ingeniería Técnica; Tomo II de Ingeniería Técnica; CONTINUIDAD del proyecto Sofía Salem. |

Declaración de alcance. Este ADR establece decisiones técnicas iniciales para STTM. No declara certificación ISO, auditoría externa, inmutabilidad absoluta ni seguridad criptográfica certificada.

## 2. Contexto

STTM será una metodología y una herramienta pública de trazabilidad. Debe poder ser usada por personas que no desean adoptar la ingeniería completa del autor, pero también debe permitir un modo avanzado con trazabilidad profunda.

El proyecto se desarrolla en Termux, pero se quiere evitar el riesgo de trabajar directamente sobre almacenamiento compartido de Android. Además, STTM no debe incluir datos privados del proyecto Sofía Salem.

## 3. Evidencia

Se consideran antecedentes directos:

- La bitácora JSONL encadenada usada en Sofía Salem.
- La regla de no editar entradas anteriores; las correcciones se agregan como entradas nuevas.
- La necesidad de no presentar capacidades criptográficas no integradas.
- La necesidad de no incluir fuentes privadas ni datos del creador en distribuciones públicas.
- El principio de evidencia antes que publicidad.
- El uso de PDCA y Kanban liviano como rutina de calidad.

## 4. Decisión

Se decide:

1. STTM se desarrolla en la carpeta nativa de Termux `~/sttm`.
2. La exportación hacia Android se hará solo cuando sea necesaria, mediante copia explícita.
3. STTM tendrá tres modos de uso:
   - Modo Registro Simple.
   - Modo Continuidad.
   - Modo Salem.
4. La evidencia canónica inicial será una bitácora append-only llamada `BITACORA.jsonl`.
5. Cada entrada de bitácora incluirá, como mínimo:
   - número secuencial;
   - fecha UTC;
   - título;
   - detalle;
   - archivos afectados;
   - referencia opcional a commit;
   - hash de la entrada anterior;
   - hash de la entrada actual;
   - tipo de firma;
   - firma opcional.
6. SQL podrá usarse más adelante como índice opcional, pero no será la única fuente de verdad.
7. Los commits Git se usarán internamente para el desarrollo de STTM, pero no serán obligatorios para usuarios públicos de la herramienta.
8. La marca de agua se aplicará únicamente a salidas oficiales: reportes, exportaciones, paquetes de auditoría y copias marcadas.
9. Ed25519 quedará disponible como capacidad opcional mediante adaptador. Si no está disponible, el sistema degradará a hash local o HMAC local, declarándolo explícitamente.
10. No se utilizará contenido privado de Sofía Salem en STTM. Las demostraciones usarán ejemplos sintéticos o datos sanitizados.
11. La interfaz visual quedará en espera del padrón de estilos, marca y lineamientos gráficos entregados por el autor.

## 5. Consecuencias

Positivas:

- STTM arranca en un entorno estable.
- Se reduce el riesgo de permisos y filesystem de Android.
- La evidencia inicial es simple, legible y verificable.
- Los usuarios públicos no serán obligados a usar ingeniería pesada.
- Se preserva la separación entre STTM y Sofía Salem.

Negativas o aceptadas:

- Por ahora la bitácora no usa firma HMAC ni Ed25519.
- La inmutabilidad no es absoluta; se limita a detección de cambios por cadena de hashes y anclas posteriores.
- Git será necesario para el desarrollo interno, aunque no se impondrá a todos los usuarios públicos.

## 6. Alternativas consideradas

1. Trabajar directamente en `~/storage/shared/Documents/STTM`.  
   Rechazada temporalmente por riesgos de permisos, rendimiento y Git.

2. Usar SQLite como única base de evidencia.  
   Rechazada como fuente única porque una base binaria es menos transparente para auditoría pública.

3. Exigir GOB, continuidad y commits a todos los usuarios.  
   Rechazada porque STTM debe ser usable en modo simple.

4. Implementar Ed25519 desde el inicio como obligación.  
   Rechazada porque todavía no hay backend criptográfico integrado ni ceremonia de claves.

## 7. Referencias

- GOB-STTM-001 — Criterios básicos de arranque.
- Sistema de Calidad y Procesos v0.1, SEA-SALEM-SCP-0.1-2026-R1.
- Salem — Especificación de Ingeniería Técnica, Tomo I, SEI-SALEM-T1-0.1.4-2026-R1.
- Salem — Especificación de Ingeniería Técnica, Tomo II, SEI-SALEM-T2-0.2.0-2026-R1.
- CONTINUIDAD del proyecto Sofía Salem.

## 8. Historial

- v0.1, 2026-09-23: versión inicial del ADR.
