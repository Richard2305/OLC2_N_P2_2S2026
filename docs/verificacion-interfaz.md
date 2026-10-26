# Verificación de la interfaz

Comprobaciones realizadas sobre Django local y Chrome mediante agent-browser. No se sustituyó la API ni la ejecución de QEMU con mocks durante los recorridos del navegador.

| Recorrido | Resultado observado |
| --- | --- |
| Abrir el editor | Carga fuente de ejemplo, CSS y JavaScript locales; se obtiene cookie CSRF |
| Ejecutar inicio.ox | Salida real con Fibonacci de 8 igual a 21, arreglo invertido y slice |
| Compilar sin ejecutar | Muestra ARM64 y reportes; la consola aclara que no se ejecutó |
| Ctrl+Enter | Ejecuta el código actual |
| Abrir archivo local | Se cargó el archivo oficial 8_errores.ox mediante selector de archivos |
| Recuperación de errores | Se mostraron once diagnósticos y todos los mensajes de control |
| Navegar desde un diagnóstico | La selección del primer error enfocó línea 25, columna 17 |
| Guardar fuente | La copia descargada coincidió byte a byte con inicio.ox |
| Exportar AST | La descarga produjo un SVG válido y cargado como imagen en el panel |
| Exportar símbolos | Se descargó un HTML independiente con la tabla |
| Editar después de ejecutar | Los reportes se marcaron como pertenecientes a la versión anterior |
| Nuevo con cambios pendientes | El diálogo permitió conservar la edición sin perder el código |
| Recargar con borrador | Se recuperó el código editado desde almacenamiento local |
| Desconexión de red | Se mostró un mensaje de conexión, sin presentar una ejecución exitosa |
| Recuperar conexión | La siguiente ejecución volvió a producir salida real |
| Pestañas | Errores, símbolos y AST alternan sus paneles; el gráfico admite zoom |
| Pantallas pequeñas | A 320, 375, 414 y 768 px no hubo overflow horizontal de la página y todos los botones de acciones quedaron dentro del ancho visible |

Se corrigió un recorte de acciones a 320 px al ocultar el recordatorio visual del atajo y compactar los botones; el atajo continúa funcionando.

## Repetir la verificación

```sh
python manage.py runserver 127.0.0.1:8000
```

En otra terminal, con agent-browser disponible:

```sh
npx agent-browser --session oxigen-check open http://127.0.0.1:8000/
npx agent-browser --session oxigen-check snapshot -i
```

Usa los controles del editor para repetir los recorridos. En automatización, desplaza al área visible un elemento antes de pulsarlo y utiliza rutas absolutas al cargar archivos. Para cambiar el tamaño de pantalla:

```sh
npx agent-browser --session oxigen-check set viewport 320 820
```

Las pruebas Python verifican además el escape de HTML/DOT, los reportes con errores de ejecución, el funcionamiento sin Graphviz, el límite de nodos y una solicitud real con CSRF. La verificación visual y funcional del navegador complementa esas pruebas; no mide todas las combinaciones posibles de entradas ni sustituye una auditoría completa de accesibilidad.
