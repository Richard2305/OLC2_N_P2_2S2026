// =====================================================================
//  OxigenNative - Proyecto 2 - Archivo de calificacion UNIFICADO: 2_intermedias
//  SECCION 2 - Funcionalidades intermedias (18 pts)
//
//  Reune los archivos por criterio de entradas/. Cada criterio tiene su banner y
//  sus bloques CASO; cada bloque usa variables propias, asi que se puede borrar
//  un criterio completo (o un caso) sin romper el resto.
//  Salida esperada: calificacion/esperadas/2_intermedias.esperado.txt
//
//  Criterios incluidos:
//    - 2.1: If (2 pts)
//    - 2.2: Match (3 pts)
//    - 2.3: Loop (2 pts)
//    - 2.4: Loop + Tag (3 pts)
//    - 2.5: While (2 pts)
//    - 2.6: Break (3 pts)
//    - 2.7: Continue (3 pts)
// =====================================================================
fn main() {
    // ######################################################################
    // ## CRITERIO 2.1: If (2 pts)
    // ######################################################################
    // ===== CASO 2.1-a: if simple (una rama se ejecuta, otra no) [salida: 1 linea] =====
    let x: i32 = 10;
    if x > 5 {
        println!("mayor que 5");
    }
    if x > 20 {
        println!("mayor que 20");
    }

    // ===== CASO 2.1-b: if / else [salida: 1 linea] =====
    let n: i32 = 3;
    if n % 2 == 0 {
        println!("par");
    } else {
        println!("impar");
    }

    // ===== CASO 2.1-c: else if [salida: 1 linea] =====
    let nota: i32 = 75;
    if nota >= 90 {
        println!("excelente");
    } else if nota >= 60 {
        println!("aprobado");
    } else {
        println!("reprobado");
    }

    // ===== CASO 2.1-d: if anidado [salida: 1 linea] =====
    let a: i32 = 8;
    let b: i32 = 3;
    if a > 5 {
        if b > 5 {
            println!("ambos mayores que 5");
        } else {
            println!("solo a es mayor que 5");
        }
    } else {
        println!("ninguno");
    }

    // ===== CASO 2.1-e: condicion compuesta (&&, ||, !) [salida: 2 lineas] =====
    let edad: i32 = 20;
    let activo: bool = true;
    if edad >= 18 && activo {
        println!("acceso");
    } else {
        println!("denegado");
    }
    if edad < 18 || !activo {
        println!("bloqueado");
    } else {
        println!("libre");
    }

    // ######################################################################
    // ## CRITERIO 2.2: Match (3 pts)
    // ######################################################################
    // ===== CASO 2.2-a: coincide con un valor especifico [salida: 1 linea] =====
    let dia: i32 = 3;
    match dia {
        1 => println!("lunes"),
        2 => println!("martes"),
        3 => println!("miercoles"),
        _ => println!("otro dia"),
    }

    // ===== CASO 2.2-b: cae en el comodin [salida: 1 linea] =====
    let fuera: i32 = 9;
    match fuera {
        1 => println!("uno"),
        2 => println!("dos"),
        _ => println!("comodin"),
    }

    // ===== CASO 2.2-c: match sobre una expresion [salida: 1 linea] =====
    let base: i32 = 1;
    match base + 1 {
        1 => println!("uno"),
        2 => println!("dos"),
        _ => println!("otro"),
    }

    // ######################################################################
    // ## CRITERIO 2.3: Loop (2 pts)
    // ######################################################################
    // ===== CASO 2.3-a: loop con contador y break [salida: 3 lineas] =====
    let mut contador: i32 = 0;
    loop {
        contador += 1;
        println!("{}", contador);
        if contador == 3 {
            break;
        }
    }

    // ===== CASO 2.3-b: loop con acumulador (suma 1+2+3+4 = 10) [salida: 1 linea] =====
    let mut i: i32 = 0;
    let mut suma: i32 = 0;
    loop {
        i += 1;
        suma += i;
        if suma >= 10 {
            break;
        }
    }
    println!("{}", suma);

    // ######################################################################
    // ## CRITERIO 2.4: Loop + Tag (3 pts)
    // ######################################################################
    // ===== CASO 2.4-a: loops anidados con etiquetas [salida: 4 lineas] =====
    let mut fila: i32 = 0;
    'externo: loop {
        fila += 1;
        let mut col: i32 = 0;
        'interno: loop {
            col += 1;
            println!("({}, {})", fila, col);
            if col == 2 {
                break 'interno;
            }
        }
        if fila == 2 {
            break 'externo;
        }
    }

    // ===== CASO 2.4-b: loop con etiqueta y break normal [salida: 1 linea] =====
    'solo: loop {
        println!("dentro de solo");
        break;
    }

    // ######################################################################
    // ## CRITERIO 2.5: While (2 pts)
    // ######################################################################
    // ===== CASO 2.5-a: while con contador [salida: 3 lineas] =====
    let mut w: i32 = 3;
    while w > 0 {
        println!("{}", w);
        w -= 1;
    }

    // ===== CASO 2.5-b: while que no entra [salida: 1 linea] =====
    let mut n_05: i32 = 5;
    while n_05 < 0 {
        println!("no debe imprimirse");
        n_05 -= 1;
    }
    println!("sin iteraciones");

    // ######################################################################
    // ## CRITERIO 2.6: Break (3 pts)
    // ######################################################################
    // ===== CASO 2.6-a: break simple dentro de un while acotado [salida: 1 linea] =====
    let mut b1: i32 = 0;
    while b1 < 10 {
        b1 += 1;
        if b1 == 4 {
            break;
        }
    }
    println!("{}", b1);

    // ===== CASO 2.6-b: break simple solo sale del bucle interno [salida: 2 lineas] =====
    let mut i_06: i32 = 0;
    while i_06 < 2 {
        i_06 += 1;
        let mut j: i32 = 0;
        loop {
            j += 1;
            if j == 3 {
                break;
            }
        }
        println!("{} {}", i_06, j);
    }

    // ===== CASO 2.6-c: break 'etiqueta desde el bucle interno [salida: 2 lineas] =====
    'externo_06: loop {
        'interno_06: loop {
            println!("dentro");
            break 'externo_06;
            println!("esto no se ejecuta");
        }
        println!("esto tampoco se ejecuta");
    }
    println!("fuera");

    // ######################################################################
    // ## CRITERIO 2.7: Continue (3 pts)
    // ######################################################################
    // ===== CASO 2.7-a: continue simple (imprime solo los impares) [salida: 3 lineas] =====
    let mut i_07: i32 = 0;
    while i_07 < 6 {
        i_07 += 1;
        if i_07 % 2 == 0 {
            continue;
        }
        println!("{}", i_07);
    }

    // ===== CASO 2.7-b: continue 'etiqueta hacia el bucle externo [salida: 3 lineas] =====
    let mut fila_07: i32 = 0;
    'externo_07: loop {
        fila_07 += 1;
        if fila_07 > 3 {
            break 'externo_07;
        }
        let mut col_07: i32 = 0;
        'interno_07: loop {
            col_07 += 1;
            if col_07 > 3 {
                break 'interno_07;
            }
            if col_07 == 2 {
                continue 'externo_07;
            }
            println!("({}, {})", fila_07, col_07);
        }
        println!("fin de fila {}", fila_07);
    }
}
