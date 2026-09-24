# Ayuda de STTM

STTM (Salem Traceability & Trust Method) es una herramienta para crear cadenas de evidencia verificables de tus proyectos. Todo lo que registrás queda encadenado criptográficamente: si alguien modifica una entrada del pasado, la cadena se rompe y se detecta.

## Modos de operación

STTM tiene tres modos que se adaptan a tus necesidades:

### Modo Simple
Registro básico de eventos con hashes SHA-256. Ideal para prototipos y experimentos rápidos.

**Qué tenés:**
- Bitácora de entradas encadenadas
- Hashes SHA-256 para verificar integridad
- Sin firma digital

**Cuándo usarlo:** Cuando la velocidad importa más que la trazabilidad formal.

### Modo Continuidad
Agrega documentos de estado, índices y handoff. Ideal para proyectos en producción con usuarios reales.

**Qué tenés (además de Simple):**
- Firma Ed25519 obligatoria
- Documentos de estado y continuidad
- Auditorías programadas (semanal/mensual)

**Cuándo usarlo:** Cuando la integridad importa pero no es crítica.

### Modo Salem
Máxima trazabilidad con validación automática y testigos externos. Ideal para proyectos públicos donde la confianza verificable es esencial.

**Qué tenés (además de Continuidad):**
- Timestamping externo (OpenTimestamps) obligatorio
- Auditorías programadas (diaria/semanal)
- Testigos externos (GitHub Actions, email)
- Export de reportes para terceros

**Cuándo usarlo:** Cuando necesitás demostrar integridad a terceros.

## Cómo usar STTM

### Registrar una entrada
1. Hacé click en **"+ Nueva entrada"** en la vista de Bitácora
2. Completá el formulario:
   - **Título:** nombre corto del evento (obligatorio)
   - **Detalle:** descripción de qué pasó, por qué importa y qué se espera después (obligatorio)
   - **Archivos afectados:** lista de archivos modificados, separados por comas (opcional)
   - **Commit relacionado:** hash corto de Git si aplica (opcional)
   - **Modo de firma:** hash (básico), hmac (simétrico) o ed25519 (asimétrico)
3. Click en **"Guardar entrada"**

La entrada se agrega a la bitácora con un hash que la encadena a la anterior. Si alguien modifica esta entrada en el futuro, el hash cambiará y la cadena se romperá.

### Cambiar de modo
1. Usá el selector **"Modo"** en la cabecera
2. Confirmá el cambio en el diálogo que aparece
3. La UI se actualiza mostrando solo las capacidades del modo seleccionado

El cambio queda registrado en la bitácora con tu motivo.

### Crear un proyecto nuevo
1. Click en **"+ Proyecto"** en la cabecera
2. Completá el formulario:
   - **Referencia interna:** identificador único (ej: sttm, sofia, alejandra)
   - **Título:** nombre del proyecto
   - **Descripción:** propósito del proyecto
   - **Nivel inicial:** simple, continuidad o salem
3. Click en **"Crear proyecto"**

El proyecto se agrega al catálogo y queda disponible en el selector de proyecto.

## Problemas comunes

### "La interfaz no cambió" después de actualizar
Si actualizaste STTM pero la interfaz sigue mostrando la versión vieja, es porque el navegador está usando una versión en caché.

**Solución:**
1. Abrí una pestaña de incógnito (Ctrl+Shift+N en Chrome, Ctrl+Shift+P en Firefox)
2. Entrá a STTM en la pestaña de incógnito
3. Deberías ver la versión actualizada

**Por qué pasa:** STTM es una herramienta local de un solo usuario, así que el servidor envía `Cache-Control: no-store` para evitar caché. Pero si tenías la página abierta antes de la actualización, el navegador puede seguir usando la versión vieja.

### El botón "Copiar" dice "Copiado (compat.)"
Algunos botones de copiado pueden mostrar "Copiado (compat.)" en lugar de solo "Copiado".

**Qué significa:**
- **"Copiado"**: se usó la API moderna `navigator.clipboard` (método preferido)
- **"Copiado (compat.)"**: se usó `document.execCommand('copy')` (método alternativo)
- **Overlay de copiado manual**: si los dos métodos anteriores fallan, aparece un cuadro de texto con el contenido para que lo copies manualmente

**Por qué pasa:** La API `navigator.clipboard` solo funciona en contextos seguros (HTTPS o localhost). Si estás accediendo a STTM desde una IP de red en HTTP, el navegador bloquea la API moderna y STTM usa métodos alternativos.

**Qué hacer:** Nada, el contenido se copió igual. Si aparece el overlay manual, seleccioná todo el texto (Ctrl+A) y copialo (Ctrl+C).

### Los selectores se ven cortados en el celular
En pantallas angostas (menos de 720px de ancho), los selectores de proyecto y modo pueden verse cortados o desbordar.

**Solución:** Esto ya está mitigado. Los selectores se envuelven automáticamente en pantallas angostas. Si todavía ves problemas, probá rotar la pantalla a modo horizontal.

**Por qué pasa:** La cabecera tiene muchos elementos (logo, selectores, navegación) que no entran en una sola línea en pantallas chicas. STTM usa media queries para envolver los elementos automáticamente.

### "Auditoría previa al schema de metadatos"
En la lista de auditorías, algunas entradas pueden mostrar 📜 con la leyenda "auditoría previa al schema de metadatos".

**Qué significa:** Esa auditoría se ejecutó antes de que STTM tuviera el sistema actual de metadatos. No tiene `meta.json` ni hallazgos clasificados por severidad.

**Qué hacer:** Nada, es información histórica. Las auditorías nuevas sí tienen metadatos completos.

### Caracteres rotos al abrir el reporte descargado
Si descargaste un reporte de auditoría como `.md` y al abrirlo ves caracteres como "AuditorÃ­a" o "âœ…", es un problema de codificación del visor.

**Qué significa:** El archivo está correcto (UTF-8), pero el visor que usaste asume otra codificación (Latin-1 o Windows-1252).

**Solución:**
1. Abrí el archivo con un editor de texto que soporte UTF-8 (Notepad++, VS Code, Sublime Text)
2. O subilo a un visor online que soporte UTF-8
3. O abrilo directamente en STTM (la UI siempre muestra UTF-8 correctamente)

**Por qué pasa:** STTM agrega un BOM UTF-8 al inicio del archivo para ayudar a los visores a detectar la codificación, pero algunos visores viejos no lo reconocen.

## Exportar y compartir reportes

### Descargar reporte
1. Ejecutá una auditoría
2. Click en **"Descargar reporte"** para guardar un `.md` con el contenido completo
3. El archivo se descarga a tu carpeta de descargas

### Compartir por email o WhatsApp
En móviles, podés usar **"Compartir reporte"** para enviar el reporte directamente a email o WhatsApp.

**Qué se comparte:**
- **En móviles:** el archivo `.md` completo (si el mensajero lo soporta) o solo el resumen de texto
- **En desktop:** un menú con opciones de email (mailto:) y WhatsApp (wa.me) con el resumen como cuerpo del mensaje

**Importante:** El servidor de STTM nunca sube evidencia a terceros. El archivo se comparte directamente desde tu navegador.

**Por qué solo el resumen a veces:** Algunos mensajeros (WhatsApp, email) tienen límites de tamaño o no soportan archivos adjuntos desde la web. En esos casos, STTM comparte solo el resumen de texto y vos adjuntás el `.md` descargado manualmente.

## Preguntas frecuentes

### ¿Puedo modificar una entrada de la bitácora?
No. La bitácora es append-only: solo se pueden agregar entradas nuevas, nunca modificar o borrar las existentes. Si necesitás corregir algo, agregá una entrada nueva explicando la corrección.

### ¿Qué pasa si se rompe la cadena de hashes?
Si alguien modifica una entrada del pasado, el hash de esa entrada cambiará y no coincidirá con el `hash_prev` de la siguiente entrada. El verificador de integridad detectará la ruptura y te avisará.

### ¿Puedo bajar de modo Salem a Simple?
Técnicamente sí, pero no es recomendable. Una vez que demostraste integridad con Salem, bajar el nivel puede generar dudas sobre la historia posterior.

### ¿Los modos afectan el rendimiento?
Mínimamente. El modo Salem agrega ~2 segundos por entrada (timestamping + testigos), pero es asíncrono y no bloquea el registro.

### ¿Puedo tener diferentes modos para diferentes archivos del mismo proyecto?
No. El modo aplica al proyecto completo. Si necesitás diferentes niveles de rigor, creá proyectos separados.

## Soporte

STTM es una herramienta de código abierto desarrollada por Martín José Dalberto (Argentina, 2026). Para reportar bugs o solicitar funcionalidades, abr un issue en el repositorio de GitHub.

---

*Esta ayuda se actualiza automáticamente desde `docs/05-ui/AYUDA.md`. Última actualización: 2026-09-25.*
