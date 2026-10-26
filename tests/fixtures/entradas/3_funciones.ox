// =====================================================================
//  OxigenNative - Proyecto 2 - Archivo de calificacion UNIFICADO: 3_funciones
//  SECCION 3 - Funciones, criterios 3.1 a 3.8 (26 pts); 3.9 va aparte
//
//  Reune los archivos por criterio de entradas/. Cada criterio tiene su banner y
//  sus bloques CASO; cada bloque usa variables propias, asi que se puede borrar
//  un criterio completo (o un caso) sin romper el resto.
//  Salida esperada: calificacion/esperadas/3_funciones.esperado.txt
//
//  Criterios incluidos:
//    - 3.1: Funcion sin parametros y sin retorno greet() (2 pts)
//    - 3.2: gen_pascal() sin parametros y sin retorno, recursiva (2 pts)
//    - 3.3: print_msg(msg: String) con parametros y sin retorno (2 pts)
//    - 3.4: show_factorial(n: i32) recursiva, con parametros y sin retorno (2 pts)
//    - 3.5: euclidean_distance(...) -> f64 (4 pts)
//    - 3.6: fibonacci(n: i32) -> i32 recursiva (4 pts)
//    - 3.7: aprox_pi() + helper_leibniz() (5 pts)
//    - 3.8: resolve_hanoi(...) recursiva (5 pts)
// =====================================================================
// ---- Funciones del criterio 3.1: Funcion sin parametros y sin retorno greet() (2 pts) ----
fn greet() {
    println!("Hola desde greet");
}
// ---- Funciones del criterio 3.2: gen_pascal() sin parametros y sin retorno, recursiva (2 pts) ----
// Elemento (fila f, columna c) = suma de los dos de arriba; los bordes valen 1.
fn pascal_celda(f: i32, c: i32) -> i32 {
    if c == 0 || c == f {
        return 1;
    }
    return pascal_celda(f - 1, c - 1) + pascal_celda(f - 1, c);
}

// Imprime la fila f desde la columna c, una celda por linea.
fn pascal_imprimir_fila(f: i32, c: i32) {
    if c <= f {
        println!("{}", pascal_celda(f, c));
        pascal_imprimir_fila(f, c + 1);
    }
}

// Imprime las filas f .. total-1, cada una cerrada con "---".
fn pascal_filas(f: i32, total: i32) {
    if f < total {
        pascal_imprimir_fila(f, 0);
        println!("---");
        pascal_filas(f + 1, total);
    }
}

fn gen_pascal() {
    pascal_filas(0, 5);
}
// ---- Funciones del criterio 3.3: print_msg(msg: String) con parametros y sin retorno (2 pts) ----
fn print_msg(msg: String) {
    println!("Mensaje: {}", msg);
}
// ---- Funciones del criterio 3.4: show_factorial(n: i32) recursiva, con parametros y sin retorno (2 pts) ----
fn factorial(n: i32) -> i32 {
    if n <= 1 {
        return 1;
    }
    return n * factorial(n - 1);
}

fn show_factorial(n: i32) {
    if n > 1 {
        show_factorial(n - 1);
    }
    println!("{}! = {}", n, factorial(n));
}
// ---- Funciones del criterio 3.5: euclidean_distance(...) -> f64 (4 pts) ----
fn abs_f(x: f64) -> f64 {
    if x < 0.0 {
        return 0.0 - x;
    }
    return x;
}

// Raiz cuadrada por Newton-Raphson: x <- (x + v / x) / 2, 40 iteraciones.
fn sqrt_newton(valor: f64) -> f64 {
    if valor <= 0.0 {
        return 0.0;
    }
    let mut x: f64 = valor;
    let mut i: i32 = 0;
    while i < 40 {
        x = (x + valor / x) / 2.0;
        i += 1;
    }
    return x;
}

fn euclidean_distance(x1: f64, y1: f64, x2: f64, y2: f64) -> f64 {
    let dx: f64 = x2 - x1;
    let dy: f64 = y2 - y1;
    return sqrt_newton(dx * dx + dy * dy);
}
// ---- Funciones del criterio 3.6: fibonacci(n: i32) -> i32 recursiva (4 pts) ----
fn fibonacci(n: i32) -> i32 {
    if n < 2 {
        return n;
    }
    return fibonacci(n - 1) + fibonacci(n - 2);
}
// ---- Funciones del criterio 3.7: aprox_pi() + helper_leibniz() (5 pts) ----
fn helper_leibniz(k: i32) -> f64 {
    let denominador: f64 = 2.0 * k + 1.0;
    if k % 2 == 0 {
        return 1.0 / denominador;
    }
    return 0.0 - 1.0 / denominador;
}

fn aprox_pi() -> f64 {
    let mut suma: f64 = 0.0;
    let mut k: i32 = 0;
    while k < 1000 {
        suma += helper_leibniz(k);
        k += 1;
    }
    return 4.0 * suma;
}
// ---- Funciones del criterio 3.8: resolve_hanoi(...) recursiva (5 pts) ----
fn resolve_hanoi(n: i32, origen: char, auxiliar: char, destino: char) {
    if n == 1 {
        println!("Mover disco 1 de {} a {}", origen, destino);
    } else {
        resolve_hanoi(n - 1, origen, destino, auxiliar);
        println!("Mover disco {} de {} a {}", n, origen, destino);
        resolve_hanoi(n - 1, auxiliar, origen, destino);
    }
}

fn main() {
    // ######################################################################
    // ## CRITERIO 3.1: Funcion sin parametros y sin retorno greet() (2 pts)
    // ######################################################################
    // ===== CASO 3.1: llamar greet() dos veces [salida: 5 lineas] =====
    println!("inicio");
    greet();
    println!("medio");
    greet();
    println!("fin");

    // ######################################################################
    // ## CRITERIO 3.2: gen_pascal() sin parametros y sin retorno, recursiva (2 pts)
    // ######################################################################
    // ===== CASO 3.2: triangulo de Pascal de 5 filas [salida: 20 lineas] =====
    gen_pascal();

    // ######################################################################
    // ## CRITERIO 3.3: print_msg(msg: String) con parametros y sin retorno (2 pts)
    // ######################################################################
    // ===== CASO 3.3-a: argumento literal [salida: 1 linea] =====
    print_msg(String::from("Hola"));

    // ===== CASO 3.3-b: argumento variable [salida: 1 linea] =====
    let texto = String::from("Compiladores");
    print_msg(texto);

    // ######################################################################
    // ## CRITERIO 3.4: show_factorial(n: i32) recursiva, con parametros y sin retorno (2 pts)
    // ######################################################################
    // ===== CASO 3.4-a: show_factorial(5) [salida: 5 lineas] =====
    show_factorial(5);

    // ===== CASO 3.4-b: caso base show_factorial(1) [salida: 1 linea] =====
    show_factorial(1);

    // ######################################################################
    // ## CRITERIO 3.5: euclidean_distance(...) -> f64 (4 pts)
    // ######################################################################
    // ===== CASO 3.5-a: (0,0)-(3,4), distancia 5 [salida: 1 linea] =====
    let d1: f64 = euclidean_distance(0.0, 0.0, 3.0, 4.0);
    println!("{}", abs_f(d1 - 5.0) < 0.0001);

    // ===== CASO 3.5-b: (0,0)-(6,8), distancia 10 [salida: 1 linea] =====
    let d2: f64 = euclidean_distance(0.0, 0.0, 6.0, 8.0);
    println!("{}", abs_f(d2 - 10.0) < 0.0001);

    // ===== CASO 3.5-c: (1,1)-(4,5), distancia 5 [salida: 1 linea] =====
    let d3: f64 = euclidean_distance(1.0, 1.0, 4.0, 5.0);
    println!("{}", abs_f(d3 - 5.0) < 0.0001);

    // ===== CASO 3.5-d: mismo punto, distancia 0 [salida: 1 linea] =====
    let d4: f64 = euclidean_distance(2.0, 2.0, 2.0, 2.0);
    println!("{}", abs_f(d4) < 0.0001);

    // ===== CASO 3.5-e: control negativo (la distancia 5 NO es 6) [salida: 1 linea] =====
    println!("{}", abs_f(d1 - 6.0) < 0.0001);

    // ######################################################################
    // ## CRITERIO 3.6: fibonacci(n: i32) -> i32 recursiva (4 pts)
    // ######################################################################
    // ===== CASO 3.6-a: casos base fibonacci(0) y fibonacci(1) [salida: 2 lineas] =====
    println!("{}", fibonacci(0));
    println!("{}", fibonacci(1));

    // ===== CASO 3.6-b: fibonacci(2) y fibonacci(5) [salida: 2 lineas] =====
    println!("{}", fibonacci(2));
    println!("{}", fibonacci(5));

    // ===== CASO 3.6-c: fibonacci(10) [salida: 1 linea] =====
    println!("{}", fibonacci(10));

    // ===== CASO 3.6-d: fibonacci(15) [salida: 1 linea] =====
    println!("{}", fibonacci(15));

    // ######################################################################
    // ## CRITERIO 3.7: aprox_pi() + helper_leibniz() (5 pts)
    // ######################################################################
    // ===== CASO 3.7-a: terminos de helper_leibniz [salida: 3 lineas] =====
    println!("{}", helper_leibniz(0) == 1.0);
    println!("{}", helper_leibniz(1) < 0.0);
    println!("{}", helper_leibniz(2) > 0.0);

    // ===== CASO 3.7-b: aprox_pi() esta entre 3.14 y 3.15 [salida: 1 linea] =====
    let pi: f64 = aprox_pi();
    println!("{}", pi > 3.14 && pi < 3.15);

    // ######################################################################
    // ## CRITERIO 3.8: resolve_hanoi(...) recursiva (5 pts)
    // ######################################################################
    // ===== CASO 3.8-a: 2 discos [salida: 4 lineas] =====
    println!("Hanoi con 2 discos");
    resolve_hanoi(2, 'A', 'B', 'C');

    // ===== CASO 3.8-b: 3 discos [salida: 8 lineas] =====
    println!("Hanoi con 3 discos");
    resolve_hanoi(3, 'A', 'B', 'C');
}
