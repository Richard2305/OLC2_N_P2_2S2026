# OxigenNative

Compilador académico: Python + PLY → AST propio → análisis semántico → ARM64 → QEMU, servido mediante Django.

## Instalación e inicio

Requiere Linux, Python y las herramientas `aarch64-linux-gnu-as`, `aarch64-linux-gnu-ld`, `qemu-aarch64` y `dot` en PATH.

```sh
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python manage.py runserver
```

El editor se abre en http://127.0.0.1:8000/. Permite crear, abrir, editar y descargar archivos `.ox`, compilar/ejecutar, inspeccionar ARM64 y exportar reportes. No requiere un servidor Node ni recursos de red externos.

Documentación: [Manual de usuario](docs/manual-usuario.md), [Manual técnico](docs/manual-tecnico.md), [Gramática BNF](docs/gramatica.bnf) y [Verificación de interfaz](docs/verificacion-interfaz.md).

## Compilar y ejecutar desde consola

```sh
python -m compiler tests/fixtures/entradas/99_integral_minimo.ox --run
python -m compiler tests/fixtures/entradas/99_integral_minimo.ox --run --emit /tmp/minimum.s
```

Sin `--run` ni `--emit`, se imprime el ensamblador. Los diagnósticos van a stderr; la salida del programa va a stdout. Si hay diagnósticos, el comando termina con código 1 aunque las instrucciones recuperadas hayan podido ejecutarse.

## API

- `GET /api/health/`: estado del servicio.
- `POST /api/compile/`: recibe JSON `{"source": "fn main() {}"}`; devuelve `success`, `assembly`, `diagnostics`, `ast` y `symbols`.
- `POST /api/run/`: recibe el mismo JSON y devuelve además `executed`, `stdout`, `stderr` y `exit_code`. Si falla una herramienta, `stage` identifica ensamblado (0), enlace (1) o ejecución (2).

Ambos endpoints incorporan `elapsed_ms` y `reports`: `errors_html`, `symbols_html`, `ast_dot`, `ast_svg` y `ast_error`. Los reportes corresponden al mismo artefacto de compilación, sin repetir su ejecución. Graphviz tiene límites de 3,000 nodos, cinco segundos y 8 MiB de SVG; si falla, se mantiene el resto de los resultados. La tabla incluye variables, parámetros y funciones; sus valores son literales iniciales, no valores finales de QEMU.

Los diagnósticos incluyen categoría, mensaje, línea, columna y fragmento cuando está disponible. `success` solo es verdadero cuando no hay diagnósticos ni fallos de herramientas. La recuperación permite obtener salida con `success: false`. Los errores del protocolo HTTP usan 400, 405, 413 o 415; los resultados del compilador usan 200. Las solicitudes del navegador requieren el token CSRF de Django.

El código fuente de la API está limitado a 64 KiB. Cada proceso tiene un límite de 5 segundos y 1 MiB de salida. Este servicio es para uso local; QEMU User Mode no constituye un aislamiento de seguridad para exponer código arbitrario a terceros.

## Funcionalidad actual

| Área | Estado |
| --- | --- |
| Lexer/parser PLY y AST con posiciones | Aceptan los siete archivos oficiales válidos |
| Tipos básicos | i32, f64, bool, char Unicode, String y None |
| Variables | Tipos explícitos/inferidos, valores predeterminados, mutabilidad, ámbitos y shadowing |
| Operadores | Aritméticos, relacionales, lógicos con cortocircuito y asignaciones compuestas |
| Strings | Literales, escapes, raw strings, String::from, concatenación, repetición y comparación |
| Control de flujo | if/else, while, loop, etiquetas, match, break y continue |
| Funciones | Parámetros, retornos, llamadas adelantadas, recursión y recursión mutua |
| Impresión | println! con argumentos y formatos {} y {:?}, incluidos arreglos anidados y escape de String/char dentro de arreglos |
| Arreglos y matrices | Tipos explícitos/inferidos, arreglos vacíos con contexto, repetición, valores predeterminados, acceso/asignación y memoria contigua en orden por filas |
| Slices | Vistas compartidas de solo lectura, rangos y límites comprobados |
| Funciones embebidas | typeof, random inclusivo, len, contains, replace, split, to_uppercase, to_lowercase y reverse mutable |
| Editor web | Resaltado, números de línea, atajos, archivos locales, borrador persistente y aviso de resultados antiguos |
| Reportes | Errores y símbolos exportables a HTML; AST Graphviz con zoom y descargas SVG/DOT |

Las pruebas comparan la salida real de QEMU con los ocho archivos oficiales: integral mínimo, básicos, intermedias, funciones, hoisting, embebidas, arreglos y errores. Los archivos de básicos y errores contienen fallos intencionales: se reportan y se continúa con las instrucciones válidas. Las pruebas del archivo de errores comprueban sus once diagnósticos y todos sus mensajes de control.

## Diseño del backend

- `compiler/semantic.py`: tipos, firmas de funciones registradas de antemano, ámbitos y bindings de símbolos. El análisis no ejecuta el programa.
- `compiler/codegen.py`: Visitor directo del AST a instrucciones ARM64, sin representación intermedia de tres direcciones.
- `compiler/runtime/aarch64.s`: impresión, cadenas, heap y comprobaciones de ejecución, usando syscalls Linux y sin libc.

Cada función tiene stack frame propio y preserva x29/x30; las variables ocupan slots de 8 bytes y los temporales respetan alineación de 16 bytes. Las llamadas usan x0–x7 para enteros/punteros y d0–d7 para f64; los resultados usan x0 o d0. Por ahora se admiten hasta ocho argumentos de cada clase; el paso de argumentos excedentes por stack está pendiente.

Los String tienen un encabezado con longitud en bytes seguido del contenido UTF-8, por lo que admiten caracteres nulos. String::from, concatenación y repetición reservan memoria en un heap de 1 MiB, sin recolección durante el programa. Los i32 usan aritmética de 32 bits; los f64 se calculan en doble precisión. El formateador decimal inicial imprime hasta seis decimales, conserva al menos uno y admite magnitudes menores a 1e12; la impresión de mayor precisión/científica queda pendiente. División entre cero, agotamiento de heap y errores de impresión terminan el binario con un mensaje en stderr.

Las operaciones aritméticas incompatibles producen None; las declaraciones con inicializador incompatible usan el valor predeterminado del tipo declarado. Las instrucciones que usan identificadores desconocidos, llamadas inválidas o índices incorrectos se omiten. Si un inicializador falla por un índice dinámico, la variable conserva su valor predeterminado. Las asignaciones y transferencias inválidas se omiten para continuar con las instrucciones válidas.

### Arreglos y vistas

Cada arreglo tiene un descriptor de dos palabras: cantidad de elementos y puntero a datos. Los datos de arreglos multidimensionales se aplanan en un único bloque contiguo **row-major**. El desplazamiento de una matriz es `(fila * columnas + columna) * tamaño del escalar`; cada dimensión se comprueba antes de acceder. Los valores básicos ocupan slots de 8 bytes dentro del bloque.

Los arreglos tienen semántica de valor al declarar, asignar, pasar parámetros o retornar; se copian los datos para evitar que modificar una copia cambie el original. Las cadenas dentro de arreglos comparten contenido inmutable. Los slices conservan un descriptor con longitud y puntero a una porción del bloque original; no copian sus elementos. Sus elementos son de solo lectura, incluso si la variable del slice se declara con `mut`; esa variable sí puede reasignarse a otra vista. `reverse()` intercambia elementos o filas completos y exige un arreglo mutable.

Los índices y rangos constantes inválidos se reportan al compilar. Los límites dinámicos se comprueban en ARM64; si fallan, se informa la posición de origen y se restaura el stack al inicio de la instrucción para continuar con la siguiente. El proceso puede terminar con código 0 y aun así devolver `success: false` por estos diagnósticos. API y CLI usan la misma traducción de los diagnósticos de ejecución.

### Funciones embebidas

`len()` mide bytes UTF-8 para String y elementos para arreglos/slices. `contains()` busca subcadenas o valores básicos, incluidos String, bool, char y f64. `replace()` sustituye todas las coincidencias no superpuestas. `split()` conserva campos vacíos y devuelve un arreglo de String con longitud determinada en ejecución. Un separador vacío divide en límites de caracteres Unicode y conserva los campos vacíos de los extremos.

`to_uppercase()` y `to_lowercase()` transforman escalares Unicode en ARM64 utilizando tablas de la base Unicode incluida en Python, incluidas expansiones como `ß → SS`; no se implementan reglas contextuales como la sigma griega final. El contenido fuente no se interpreta en Python. `random(min, max)` usa `getrandom` de Linux y muestreo por rechazo para obtener valores inclusivos sin sesgo de módulo, incluso en el rango i32 completo. Rangos inválidos constantes o dinámicos generan diagnósticos.

Limitaciones pendientes: precisión/rango de impresión f64, argumentos excedentes por stack y captura de valores finales para la tabla de símbolos. La consola recibe la salida al terminar la solicitud; no utiliza streaming.

## Verificación

```sh
python manage.py check
python -m pytest -q
node --check static/editor.js
```

Los casos oficiales originales están en `tests/fixtures/`. Las pruebas requieren las herramientas ARM64 y QEMU instaladas; no sustituyen la ejecución por una simulación en Python.
