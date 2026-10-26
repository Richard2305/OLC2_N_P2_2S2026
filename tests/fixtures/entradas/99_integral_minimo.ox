// =====================================================================
//  OxigenNative - Proyecto 2 - Archivo de calificacion 99
//  Programa integral minimo (enunciado 3.6): operaciones aritmeticas, logicas,
//  declaracion de variables con los 5 tipos y println!.
//  Salida esperada: esperadas/99_integral_minimo.esperado.txt
// =====================================================================

fn main() {
    // ===== Declaracion de variables con los 5 tipos =====
    let a: i32 = 12;
    let b: i32 = 4;
    let c: f64 = 2.5;
    let ok: bool = true;
    let letra: char = 'Z';
    let texto: String = String::from("Oxigen");

    // ===== CASO 99-a: aritmetica [salida: 6 lineas] =====
    println!("{}", a + b);
    println!("{}", a - b);
    println!("{}", a * b);
    println!("{}", a / b);
    println!("{}", a % 5);
    println!("{}", a + c);

    // ===== CASO 99-b: logica [salida: 3 lineas] =====
    println!("{}", ok && !ok);
    println!("{}", ok || false);
    println!("{}", a > b && b > 0);

    // ===== CASO 99-c: println! con String, char y varios valores [salida: 3 lineas] =====
    println!("{}", texto);
    println!("{}", letra);
    println!("{} mide {} y {}", texto, c, ok);
}
