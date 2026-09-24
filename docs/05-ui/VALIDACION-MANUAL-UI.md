# Validación manual de la interfaz de usuario

**Estado:** Declaración formal (K-003 cerrada, STTM-0.26).

## Decisión

La interfaz de usuario de STTM (renderizado en navegador) **no tiene tests automatizados**. La validación se realiza manualmente en dispositivo real por el autor tras cada cambio que toque `web/`.

## Motivo

Agregar tests automatizados de render requeriría un headless browser (Playwright, Puppeteer o Selenium), lo que implica:

- **Dependencias pesadas:** ~50-100 MB de binarios, rompiendo el principio de "stdlib únicamente" declarado en CONTINUIDAD.
- **Complejidad en CI:** setup adicional en GitHub Actions, mantenimiento de drivers de navegador.
- **Tests frágiles:** cambios menores de CSS o texto pueden romper tests sin indicar problemas reales.
- **Valor bajo:** la UI de STTM es simple (createElement + textContent, sin framework); el riesgo de bugs de render es bajo y la validación manual es rápida.

El costo de validar manualmente (5 minutos por cambio) es menor que el costo de mantener tests automatizados frágiles.

## Checklist de validación manual

Cada commit que toque `web/` debe validarse en dispositivo real (celular o escritorio) verificando:

1. **Carga:** la página abre sin errores de consola (F12).
2. **Selector de proyecto:** el dropdown muestra todos los proyectos activos; al cambiar, la bitácora se recarga.
3. **Selector de modo:** cambiar modo muestra confirmación y registra en bitácora.
4. **Navegación:** los botones de bitácora/documentos/auditorías/ayuda cambian la vista activa.
5. **Botones de copiar:** cada botón copia el dato correcto y muestra feedback ("¡Copiado!").
6. **Formularios:** registrar entrada, crear documento, auditar y crear proyecto funcionan end-to-end.
7. **Responsive:** en ancho móvil (<720px), la cabecera envuelve sin desborde horizontal (PC-011).
8. **Overlay de copia:** si el navegador no permite clipboard, el overlay muestra el texto seleccionable.

## Frecuencia

- **Cada commit que toque `web/`:** validación completa del checklist.
- **Commits que solo toquen `scripts/` o `tests/`:** smoke rápido (abrir la UI y verificar que carga).

## Evidencia

La validación manual queda documentada en los commits que tocan `web/`. Ejemplos:

- STTM-0.21 (K-001): selector de proyecto validado en dispositivo real, entrada de test creada desde la UI en proyecto #2.
- STTM-0.23 (K-007): botón "+ Proyecto" validado en navegador móvil.
- STTM-0.24 (PC-013): cabeceras de autoría validadas, estáticos sin caché confirmados.

## Revisión de la decisión

Esta decisión se revisará si:
- La UI crece en complejidad (framework, estado global, múltiples vistas anidadas).
- Aparecen bugs recurrentes de render que la validación manual no captura.
- Se integra un segundo desarrollador al proyecto (la validación manual no escala a N personas).

Hasta entonces, la validación manual es el método correcto para STTM.

---
*Documento creado como parte del cierre de K-003 (STTM-0.26).*
