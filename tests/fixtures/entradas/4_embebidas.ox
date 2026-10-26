// =====================================================================
//  OxigenNative - Proyecto 2 - Archivo de calificacion UNIFICADO: 4_embebidas
//  SECCION 4 - Funciones embebidas (10 pts)
//
//  Reune los archivos por criterio de entradas/. Cada criterio tiene su banner y
//  sus bloques CASO; cada bloque usa variables propias, asi que se puede borrar
//  un criterio completo (o un caso) sin romper el resto.
//  Salida esperada: calificacion/esperadas/4_embebidas.esperado.txt
//
//  Criterios incluidos:
//    - 4.1: println!() (1 pt)
//    - 4.2: typeof() (1 pt)
//    - 4.3: random(min, max) (1 pt)
//    - 4.4: len() (1 pt)
//    - 4.5: contains() (1 pt)
//    - 4.6: replace(a, b) (1 pt)
//    - 4.7: split(separador) (1 pt)
//    - 4.8: to_uppercase() (1 pt)
//    - 4.9: to_lowercase() (1 pt)
//    - 4.10: reverse() (1 pt)
// =====================================================================
fn main() {
    // ######################################################################
    // ## CRITERIO 4.1: println!() (1 pt)
    // ######################################################################
    // ===== CASO 4.1-a: literal [salida: 1 linea] =====
    println!("Hola Mundo");

    // ===== CASO 4.1-b: {} con una variable [salida: 2 lineas] =====
    let texto = String::from("Hola Mundo");
    println!("{}", texto);
    println!("Texto: {}", texto);

    // ===== CASO 4.1-c: {} con varias variables y una expresion [salida: 3 lineas] =====
    let nombre = String::from("Ana");
    let edad: i32 = 20;
    let activo: bool = true;
    println!("{} tiene {} anios", nombre, edad);
    println!("{}-{}-{}", nombre, edad, activo);
    println!("Suma: {}", edad + 5);

    // ===== CASO 4.1-d: sin formato, println!(variable) [salida: 1 linea] =====
    let libre = String::from("Hola Mundo");
    println!(libre);

    // ===== CASO 4.1-e: {:?} con arreglo [salida: 2 lineas] =====
    let numeros = [1, 2, 3];
    println!("{:?}", numeros);
    println!("Arreglo: {:?}", numeros);

    // ######################################################################
    // ## CRITERIO 4.2: typeof() (1 pt)
    // ######################################################################
    // ===== CASO 4.2-a: i32 [salida: 1 linea] =====
    let t_i: i32 = 1;
    println!("{}", typeof(t_i));

    // ===== CASO 4.2-b: f64 [salida: 1 linea] =====
    let t_f: f64 = 1.5;
    println!("{}", typeof(t_f));

    // ===== CASO 4.2-c: bool [salida: 1 linea] =====
    let t_b: bool = true;
    println!("{}", typeof(t_b));

    // ===== CASO 4.2-d: char [salida: 1 linea] =====
    let t_c: char = 'a';
    println!("{}", typeof(t_c));

    // ===== CASO 4.2-e: String [salida: 1 linea] =====
    let t_s: String = String::from("texto");
    println!("{}", typeof(t_s));

    // ######################################################################
    // ## CRITERIO 4.3: random(min, max) (1 pt)
    // ######################################################################
    // ===== CASO 4.3-a: random(1, 10) [salida: 1 linea] =====
    let r1: i32 = random(1, 10);
    if r1 >= 1 && r1 <= 10 {
        println!("ok");
    } else {
        println!("fuera de rango");
    }

    // ===== CASO 4.3-b: random(100, 200) [salida: 1 linea] =====
    let r2: i32 = random(100, 200);
    if r2 >= 100 && r2 <= 200 {
        println!("ok");
    } else {
        println!("fuera de rango");
    }

    // ######################################################################
    // ## CRITERIO 4.4: len() (1 pt)
    // ######################################################################
    // ===== CASO 4.4-a: len() de String [salida: 2 lineas] =====
    let l_s1 = String::from("Hola Mundo");
    let l_s2 = String::from("Compiladores");
    println!("{}", l_s1.len());
    println!("{}", l_s2.len());

    // ===== CASO 4.4-b: len() de arreglo [salida: 2 lineas] =====
    let l_a1 = [10, 20, 30];
    let l_a2: [i32; 5] = [1, 2, 3, 4, 5];
    println!("{}", l_a1.len());
    println!("{}", l_a2.len());

    // ######################################################################
    // ## CRITERIO 4.5: contains() (1 pt)
    // ######################################################################
    // ===== CASO 4.5-a: contains en String [salida: 2 lineas] =====
    let c_s = String::from("Hola Mundo");
    println!("{}", c_s.contains("Mundo"));
    println!("{}", c_s.contains("Rust"));

    // ===== CASO 4.5-b: contains en arreglo [salida: 2 lineas] =====
    let c_a = [10, 20, 30];
    println!("{}", c_a.contains(20));
    println!("{}", c_a.contains(99));

    // ######################################################################
    // ## CRITERIO 4.6: replace(a, b) (1 pt)
    // ######################################################################
    // ===== CASO 4.6-a: replace con coincidencia [salida: 1 linea] =====
    let r_s1 = String::from("Hola Mundo");
    println!("{}", r_s1.replace("Mundo", "Rust"));

    // ===== CASO 4.6-b: replace sin coincidencia [salida: 1 linea] =====
    let r_s2 = String::from("Hola Mundo");
    println!("{}", r_s2.replace("xyz", "abc"));

    // ######################################################################
    // ## CRITERIO 4.7: split(separador) (1 pt)
    // ######################################################################
    // ===== CASO 4.7-a: separador espacio [salida: 1 linea] =====
    let sp_s1 = String::from("Hola Mundo");
    println!("{:?}", sp_s1.split(" "));

    // ===== CASO 4.7-b: separador coma, tres partes [salida: 1 linea] =====
    let sp_s2 = String::from("a,b,c");
    println!("{:?}", sp_s2.split(","));

    // ######################################################################
    // ## CRITERIO 4.8: to_uppercase() (1 pt)
    // ######################################################################
    // ===== CASO 4.8-a: texto con mayusculas y minusculas [salida: 1 linea] =====
    let up_s1 = String::from("Hola Mundo");
    println!("{}", up_s1.to_uppercase());

    // ===== CASO 4.8-b: texto con digitos [salida: 1 linea] =====
    let up_s2 = String::from("Abc123");
    println!("{}", up_s2.to_uppercase());

    // ######################################################################
    // ## CRITERIO 4.9: to_lowercase() (1 pt)
    // ######################################################################
    // ===== CASO 4.9-a: texto con mayusculas y minusculas [salida: 1 linea] =====
    let low_s1 = String::from("Hola Mundo");
    println!("{}", low_s1.to_lowercase());

    // ===== CASO 4.9-b: texto con digitos [salida: 1 linea] =====
    let low_s2 = String::from("Abc123");
    println!("{}", low_s2.to_lowercase());

    // ######################################################################
    // ## CRITERIO 4.10: reverse() (1 pt)
    // ######################################################################
    // ===== CASO 4.10-a: longitud impar [salida: 1 linea] =====
    let mut rev_a = [10, 20, 30];
    rev_a.reverse();
    println!("{:?}", rev_a);

    // ===== CASO 4.10-b: longitud par [salida: 1 linea] =====
    let mut rev_b = [1, 2, 3, 4];
    rev_b.reverse();
    println!("{:?}", rev_b);

    // ===== CASO 4.10-c: doble reverse devuelve el original [salida: 1 linea] =====
    let mut rev_c = [1, 2, 3];
    rev_c.reverse();
    rev_c.reverse();
    println!("{:?}", rev_c);
}
