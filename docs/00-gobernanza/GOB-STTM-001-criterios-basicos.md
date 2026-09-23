# GOB-STTM-001 — Criterios básicos de arranque

**SALEM**  
**STTM — CRITERIOS BÁSICOS DE ARRANQUE**  
Borrador de trabajo interno  

Autor del proyecto  
Martín José Dalberto  
Argentina, 2026  

## 1. Control documental

| Dato | Definición |
|---|---|
| Identificador | SEA-SALEM-STTM-0.1-2026-R1 |
| Estado | Borrador de trabajo interno |
| Alcance | Establece nombre provisional, alineación documental, calidad, registro obligatorio, entorno de trabajo y límites iniciales del proyecto STTM. |
| Autor | Martín José Dalberto, Argentina. |
| Antecedentes | Plantilla de Documento Salem; Sistema de Calidad y Procesos v0.1; Tomo I de Ingeniería Técnica; Tomo II de Ingeniería Técnica; CONTINUIDAD del proyecto Sofía Salem. |

**Declaración de alcance.** Este documento define criterios de arranque del proyecto STTM. No declara certificación ISO, auditoría externa, conformidad formal ni seguridad criptográfica certificada. La interfaz de usuario quedará condicionada al padrón de estilos, marca y lineamientos visuales que entregue el autor.

## 2. Propósito

Este documento existe para dejar explícitas las reglas iniciales del proyecto STTM antes de comenzar el desarrollo de la herramienta, el método público y los documentos de ingeniería.

STTM (Salem Traceability & Trust Method) será un método y una herramienta de trazabilidad orientada a registro, auditoría y evidencia. Debe ser utilizable por público general sin exigir la ingeniería completa del autor, pero debe permitir un modo avanzado para quien desee trazabilidad profunda.

## 3. Nombre provisional

El proyecto utilizará provisionalmente la sigla: **STTM**

Nombre candidato principal: *Salem Traceability & Trust Method*  
Alternativa conservadora: *Salem Traceability Tracking Method*  

La confirmación final del nombre se registrará como decisión documental.

## 4. Alineación documental

El proyecto se alinea documental mente con prácticas internacionales, sin declarar certificación:
- ISO/IEC/IEEE 29148:2018 — Ingeniería de requisitos.
- ISO/IEC/IEEE 42010:2022 — Descripción arquitectónica.
- ISO/IEC 25010:2023 — Modelo de calidad.
- ISO/IEC/IEEE 12207:2026 — Ciclo de vida del software.
- ISO/IEC/IEEE 15288:2023 — Ciclo de vida del sistema.
- ISO/IEC/IEEE 15289:2019 — Contenido documental.
- ISO/IEC 27001:2022 — Seguridad de la información (referencia conceptual).

También se alinea con la Plantilla de Documento Salem, el Sistema de Calidad y Procesos v0.1, y los Tomos I y II de Salem. Cuando exista conflicto entre documentos, prevalecerá el documento más reciente o el que tenga autoridad explícita mayor.

## 5. Calidad y proceso

El proyecto adopta:
- PDCA como hilo conductor.
- Kanban liviano para desarrollo.
- Registro obligatorio de decisiones y cambios.

Se recomienda un límite de trabajo en curso (WIP) de dos tareas en desarrollo para evitar dispersión.

## 6. Entorno de trabajo y Mitigación de Riesgos

El desarrollo se realizará en el filesystem nativo de Termux (`~/sttm`). 
**Decisión de mitigación:** Se descarta el uso de la carpeta compartida de Android (`~/storage/shared/`) para el código y la base de datos principal, mitigando preventivamente los riesgos de permisos, rendimiento de I/O y comportamientos erráticos de Git en entornos móviles. La exportación a Android se realizará solo para paquetes de auditoría o reportes finales.

## 7. Separación de frentes (Soberanía de Datos)

STTM y el proyecto Sofía Salem son frentes independientes. 
- **Sofía Salem:** Laboratorio privado, experimental, datos sensibles.
- **STTM:** Metodología pública, auditable, demostrable.

Queda estrictamente prohibido copiar, enlazar o utilizar datos, bitácoras privadas o claves de Sofía Salem dentro del repositorio o las demostraciones públicas de STTM sin un proceso explícito de sanitización y anonimización documentado.

## 8. Límites iniciales

Quedan expresamente fuera de la promesa inicial:
- Certificación ISO formal.
- Inmutabilidad absoluta frente al propietario del hardware.
- Verificación pública plena sin ceremonia de claves.
- Inclusión de datos privados de otros proyectos del autor.

## 9. Condición de revisión

Este documento se revisará cuando:
- Se confirme el nombre definitivo.
- Se defina la arquitectura de evidencia (ADR-001).
- Se entregue el padrón de estilos UI.
- Se incorporen nuevos requisitos de auditoría o publicación.

## Referencias

[1] Plantilla de Documento Salem.  
[2] Sistema de Calidad y Procesos v0.1, SEA-SALEM-SCP-0.1-2026-R1.  
[3] Salem — Especificación de Ingeniería Técnica, Tomo I, SEI-SALEM-T1-0.1.4-2026-R1.  
[4] Salem — Especificación de Ingeniería Técnica, Tomo II, SEI-SALEM-T2-0.2.0-2026-R1.  
