// =====================================================================
//  OxigenNative - Proyecto 2 - Archivo de calificacion UNIFICADO: 8_errores
//  Criterio 8.1: Reporte de errores + tabla (0.1 c/u)
//
//  ESTE ARCHIVO ESTA ROTO A PROPOSITO. Reune los tipos de error de 3.5.1 y el
//  comentario sin cerrar de 3.2.2. Entre error y error hay un println! de
//  control: si aparecen todos en consola, la resiliencia funciona.
//  Salida esperada: calificacion/esperadas/8_errores.esperado.txt
//
//  ORDEN: el error sintactico (falta ';') va casi al final y el comentario sin
//  cerrar va AL FINAL a proposito, porque absorbe el resto del archivo (incluida
//  la '}' de main). Por eso "llave sin cerrar" aparece como consecuencia en
//  cascada del comentario y no como caso independiente.
// =====================================================================

fn suma(a: i32, b: i32) {
    println!("{}", a + b);
}

fn main() {
    // ===== CASO 8.1-0: inicio [salida: 1 linea] =====
    println!("inicio");

    // ===== CASO 8.1-a: caracter no reconocido (LEXICO) [salida: 1 linea] =====
    let total = @100;
    println!("control 1");

    // ===== CASO 8.1-b: variable no declarada (SEMANTICO) [salida: 1 linea] =====
    println!("{}", no_declarada);
    println!("control 2");

    // ===== CASO 8.1-c: tipos incompatibles, 2 errores (SEMANTICO) [salida: 1 linea] =====
    let edad: i32 = "veinte";
    let x: i32 = 10;
    let y = x + "5";
    println!("control 3");

    // ===== CASO 8.1-d: variable inmutable modificada (SEMANTICO) [salida: 1 linea] =====
    let contador = 10;
    contador = 20;
    println!("control 4");

    // ===== CASO 8.1-e: indice fuera de limites (SEMANTICO) [salida: 1 linea] =====
    let numeros = [10, 20, 30];
    println!("{}", numeros[5]);
    println!("control 5");

    // ===== CASO 8.1-f: funcion no declarada (SEMANTICO) [salida: 1 linea] =====
    saludar();
    println!("control 6");

    // ===== CASO 8.1-g: numero incorrecto de argumentos (SEMANTICO) [salida: 1 linea] =====
    suma(10);
    println!("control 7");

    // ===== CASO 8.1-h: falta punto y coma (SINTACTICO) [salida: 1 linea] =====
    let z = 10
    println!("control 8");

    // ===== CASO 8.1-i: fin del programa [salida: 1 linea] =====
    println!("fin");

    // ===== CASO 8.1-j: comentario sin cerrar (LEXICO) y llave sin cerrar (SINTACTICO, en cascada) =====
    /* este comentario nunca se cierra y absorbe la llave de main
    println!("esto queda dentro del comentario");
}
