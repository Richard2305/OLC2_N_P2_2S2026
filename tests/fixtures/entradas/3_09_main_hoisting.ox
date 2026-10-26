// =====================================================================
//  OxigenNative - Proyecto 2 - Archivo de calificacion 3_09
//  Criterio 3.9: Main (hoisting) (2 pts)
//  main esta declarada PRIMERO y llama funciones declaradas despues. Ademas
//  es_par() invoca a es_impar(), que se declara mas abajo.
//  Si el compilador no hace hoisting de funciones, este archivo falla completo.
//  Salida esperada: esperadas/3_09_main_hoisting.esperado.txt
// =====================================================================

fn main() {
    // ===== CASO 3.9-a: llamadas a funciones declaradas despues de main [salida: 4 lineas] =====
    println!("inicio de main");
    saludar();
    let s: i32 = sumar(2, 3);
    println!("sumar: {}", s);
    println!("cuadrado: {}", cuadrado(s));

    // ===== CASO 3.9-b: funciones que se llaman entre si hacia adelante [salida: 2 lineas] =====
    println!("{}", es_par(10));
    println!("{}", es_impar(10));
}

fn saludar() {
    println!("Hola desde saludar");
}

fn sumar(a: i32, b: i32) -> i32 {
    return a + b;
}

fn cuadrado(n: i32) -> i32 {
    return n * n;
}

fn es_par(n: i32) -> bool {
    if n == 0 {
        return true;
    }
    return es_impar(n - 1);
}

fn es_impar(n: i32) -> bool {
    if n == 0 {
        return false;
    }
    return es_par(n - 1);
}
