# Ayuda rápida (interfaz web)

Esta es la versión corta pensada para leerse dentro de la app. La guía
completa (comandos de CLI, referencia de API, checklist antes de llevar
esto a producción) está en `AYUDA.md`, en la raíz del proyecto.

## Roles

- **lector**: puede ver todo, no puede modificar nada.
- **auditor**: además de ver, puede registrar entradas, editar documentos y ejecutar auditorías.
- **admin**: además de todo lo anterior, administra usuarios (por CLI, no desde acá) y proyectos.

## Atajos

- **Buscar**: usá el campo de búsqueda de texto libre — funciona con palabras sueltas, y también con identificadores que tengan guiones (ej. "Ref-STTM-004").
- **Ver un documento**: hacé clic en cualquier archivo `.md` listado para abrirlo en el visor.
- **Auditar el proyecto actual**: botón "Auditar", elegí el tipo (rápida/estándar/profunda) y el motivo.
- **Cerrar sesión**: botón al pie de la página. El token se borra al instante, tanto acá como en el servidor.

## Si algo no te deja hacer una acción

Lo más probable es que tu rol no alcance (ver tabla arriba). Un mensaje
"permisos insuficientes" es normal, no un error del sistema — pedile a
un admin que te suba de rol si tu trabajo lo necesita de verdad.

Para cualquier otra duda, `AYUDA.md` en la raíz tiene la guía completa.
