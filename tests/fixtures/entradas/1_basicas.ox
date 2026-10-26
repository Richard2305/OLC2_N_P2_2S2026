// =====================================================================
//  OxigenNative - Proyecto 2 - Archivo de calificacion UNIFICADO: 1_basicas
//  SECCION 1 - Funcionalidades basicas (17 pts)
//
//  Reune los archivos por criterio de entradas/. Cada criterio tiene su banner y
//  sus bloques CASO; cada bloque usa variables propias, asi que se puede borrar
//  un criterio completo (o un caso) sin romper el resto.
//  Salida esperada: calificacion/esperadas/1_basicas.esperado.txt
//
//  Criterios incluidos:
//    - 1.1: Formato de identificadores (0.1 c/u = 0.6 pts)
//    - 1.2: Comentarios (0.2 c/u = 0.4 pts)
//    - 1.3: Declaracion inmutable larga sin inicializar (0.2 por tipo = 1 pt)
//    - 1.4: Declaracion inmutable larga inicializada (0.2 por tipo = 1 pt)
//    - 1.5: Declaracion inmutable inferida inicializada (0.2 por tipo = 1 pt)
//    - 1.6: Declaracion mutable sin inicializar (0.2 por tipo = 1 pt)
//    - 1.7: Declaracion mutable inicializada (0.2 por tipo = 1 pt)
//    - 1.8: Asignacion de variables mutables (0.2 por tipo = 1 pt)
//    - 1.9: Operadores de asignacion (0.25 c/u = 1.5 pts)
//    - 1.10: Operadores aritmeticos (0.2 c/u = 1 pt)
//    - 1.11: Operadores relacionales (0.25 c/u = 1.5 pts)
//    - 1.12: Operadores logicos (0.5 c/u = 1.5 pts)
//    - 1.13: Restriccion de cortocircuito (0.5 c/u = 1.5 pts)
//    - 1.14: Manejo de None (1 pt)
//    - 1.15: Literales y secuencias de escape (1 c/u = 2 pts)
// =====================================================================
// ---- Funciones del criterio 1.13: Restriccion de cortocircuito (0.5 c/u = 1.5 pts) ----
fn marca(n: i32) -> bool {
    println!("marca {}", n);
    return true;
}

fn main() {
    // ######################################################################
    // ## CRITERIO 1.1: Formato de identificadores (0.1 c/u = 0.6 pts)
    // ######################################################################
    // ===== CASO 1.1-a: identificador en minusculas [salida: 1 linea] =====
    let contador = 10;
    println!("{}", contador);

    // ===== CASO 1.1-b: letras y digitos [salida: 1 linea] =====
    let valor2 = 2;
    println!("{}", valor2);

    // ===== CASO 1.1-c: guion bajo inicial [salida: 1 linea] =====
    let _oculto = 3;
    println!("{}", _oculto);

    // ===== CASO 1.1-d: guion bajo interno [salida: 1 linea] =====
    let mi_contador = 4;
    println!("{}", mi_contador);

    // ===== CASO 1.1-e: mayusculas y sensibilidad a mayusculas (edad, Edad, EDAD) [salida: 3 lineas] =====
    let edad = 20;
    let Edad = 25;
    let EDAD = 30;
    println!("{}", edad);
    println!("{}", Edad);
    println!("{}", EDAD);

    // ===== CASO 1.1-f: nombre largo [salida: 1 linea] =====
    let un_identificador_bastante_largo_para_probar_el_lexer = 6;
    println!("{}", un_identificador_bastante_largo_para_probar_el_lexer);

    // ######################################################################
    // ## CRITERIO 1.2: Comentarios (0.2 c/u = 0.4 pts)
    // ######################################################################
    // ===== CASO 1.2-a: comentario de linea [salida: 2 lineas] =====
    // let roto = ;   fn ( { println!("esto no se ejecuta");
    let a: i32 = 5; // comentario al final de la linea
    println!("{}", a);
    println!("linea ok"); // println!("esto tampoco se imprime");

    // ===== CASO 1.2-b: comentario de bloque multilinea [salida: 2 lineas] =====
    /*
       Comentario de bloque con varias lineas.
       println!("esto no se ejecuta");
       let roto = ;   fn ( { }
    */
    let b: i32 = 7 /* comentario en medio de la expresion */ + 1;
    println!("{}", b);
    println!("bloque ok");

    // ######################################################################
    // ## CRITERIO 1.3: Declaracion inmutable larga sin inicializar (0.2 por tipo = 1 pt)
    // ######################################################################
    // ===== CASO 1.3-a: i32 [salida: 1 linea] =====
    let vacio_i: i32;
    println!("{}", vacio_i);

    // ===== CASO 1.3-b: f64 [salida: 1 linea] =====
    let vacio_f: f64;
    println!("{}", vacio_f);

    // ===== CASO 1.3-c: bool [salida: 1 linea] =====
    let vacio_b: bool;
    println!("{}", vacio_b);

    // ===== CASO 1.3-d: char (solo declarar, sin imprimir) [salida: 0 lineas] =====
    let vacio_c: char;

    // ===== CASO 1.3-e: String (imprime una linea vacia) [salida: 1 linea] =====
    let vacio_s: String;
    println!("{}", vacio_s);

    // ######################################################################
    // ## CRITERIO 1.4: Declaracion inmutable larga inicializada (0.2 por tipo = 1 pt)
    // ######################################################################
    // ===== CASO 1.4-a: i32 [salida: 1 linea] =====
    let larga_i: i32 = 10;
    println!("{}", larga_i);

    // ===== CASO 1.4-b: f64 [salida: 1 linea] =====
    let larga_f: f64 = 2.5;
    println!("{}", larga_f);

    // ===== CASO 1.4-c: bool [salida: 1 linea] =====
    let larga_b: bool = true;
    println!("{}", larga_b);

    // ===== CASO 1.4-d: char [salida: 1 linea] =====
    let larga_c: char = 'A';
    println!("{}", larga_c);

    // ===== CASO 1.4-e: String [salida: 1 linea] =====
    let larga_s: String = String::from("Hola");
    println!("{}", larga_s);

    // ######################################################################
    // ## CRITERIO 1.5: Declaracion inmutable inferida inicializada (0.2 por tipo = 1 pt)
    // ######################################################################
    // ===== CASO 1.5-a: i32 inferido [salida: 1 linea] =====
    let inf_i = 7;
    println!("{}", inf_i);

    // ===== CASO 1.5-b: f64 inferido [salida: 1 linea] =====
    let inf_f = 0.5;
    println!("{}", inf_f);

    // ===== CASO 1.5-c: bool inferido [salida: 1 linea] =====
    let inf_b = false;
    println!("{}", inf_b);

    // ===== CASO 1.5-d: char inferido [salida: 1 linea] =====
    let inf_c = 'Z';
    println!("{}", inf_c);

    // ===== CASO 1.5-e: String inferido [salida: 1 linea] =====
    let inf_s = String::from("Mundo");
    println!("{}", inf_s);

    // ######################################################################
    // ## CRITERIO 1.6: Declaracion mutable sin inicializar (0.2 por tipo = 1 pt)
    // ######################################################################
    // ===== CASO 1.6-a: i32 [salida: 1 linea] =====
    let mut mvacio_i: i32;
    println!("{}", mvacio_i);

    // ===== CASO 1.6-b: f64 [salida: 1 linea] =====
    let mut mvacio_f: f64;
    println!("{}", mvacio_f);

    // ===== CASO 1.6-c: bool [salida: 1 linea] =====
    let mut mvacio_b: bool;
    println!("{}", mvacio_b);

    // ===== CASO 1.6-d: char (solo declarar, sin imprimir) [salida: 0 lineas] =====
    let mut mvacio_c: char;

    // ===== CASO 1.6-e: String (imprime una linea vacia) [salida: 1 linea] =====
    let mut mvacio_s: String;
    println!("{}", mvacio_s);

    // ######################################################################
    // ## CRITERIO 1.7: Declaracion mutable inicializada (0.2 por tipo = 1 pt)
    // ######################################################################
    // ===== CASO 1.7-a: i32 [salida: 1 linea] =====
    let mut minit_i: i32 = 100;
    println!("{}", minit_i);

    // ===== CASO 1.7-b: f64 [salida: 1 linea] =====
    let mut minit_f: f64 = 1.5;
    println!("{}", minit_f);

    // ===== CASO 1.7-c: bool [salida: 1 linea] =====
    let mut minit_b: bool = true;
    println!("{}", minit_b);

    // ===== CASO 1.7-d: char [salida: 1 linea] =====
    let mut minit_c: char = 'B';
    println!("{}", minit_c);

    // ===== CASO 1.7-e: String [salida: 1 linea] =====
    let mut minit_s: String = String::from("Rust");
    println!("{}", minit_s);

    // ######################################################################
    // ## CRITERIO 1.8: Asignacion de variables mutables (0.2 por tipo = 1 pt)
    // ######################################################################
    // ===== CASO 1.8-a: i32 [salida: 2 lineas] =====
    let mut asig_i: i32 = 1;
    println!("{}", asig_i);
    asig_i = 42;
    println!("{}", asig_i);

    // ===== CASO 1.8-b: f64 [salida: 2 lineas] =====
    let mut asig_f: f64 = 0.5;
    println!("{}", asig_f);
    asig_f = 9.5;
    println!("{}", asig_f);

    // ===== CASO 1.8-c: bool [salida: 2 lineas] =====
    let mut asig_b: bool = false;
    println!("{}", asig_b);
    asig_b = true;
    println!("{}", asig_b);

    // ===== CASO 1.8-d: char [salida: 2 lineas] =====
    let mut asig_c: char = 'X';
    println!("{}", asig_c);
    asig_c = 'C';
    println!("{}", asig_c);

    // ===== CASO 1.8-e: String [salida: 2 lineas] =====
    let mut asig_s: String = String::from("uno");
    println!("{}", asig_s);
    asig_s = String::from("dos");
    println!("{}", asig_s);

    // ######################################################################
    // ## CRITERIO 1.9: Operadores de asignacion (0.25 c/u = 1.5 pts)
    // ######################################################################
    // ===== CASO 1.9-a: = [salida: 1 linea] =====
    let mut va: i32 = 1;
    va = 5;
    println!("{}", va);

    // ===== CASO 1.9-b: += [salida: 1 linea] =====
    let mut vb: i32 = 10;
    vb += 5;
    println!("{}", vb);

    // ===== CASO 1.9-c: -= [salida: 1 linea] =====
    let mut vc: i32 = 10;
    vc -= 3;
    println!("{}", vc);

    // ===== CASO 1.9-d: *= [salida: 1 linea] =====
    let mut vd: i32 = 6;
    vd *= 7;
    println!("{}", vd);

    // ===== CASO 1.9-e: /= [salida: 1 linea] =====
    let mut ve: i32 = 20;
    ve /= 4;
    println!("{}", ve);

    // ===== CASO 1.9-f: %= [salida: 1 linea] =====
    let mut vf: i32 = 17;
    vf %= 5;
    println!("{}", vf);

    // ######################################################################
    // ## CRITERIO 1.10: Operadores aritmeticos (0.2 c/u = 1 pt)
    // ######################################################################
    // ===== CASO 1.10-a: suma (i32+i32, i32+f64, String+String) [salida: 3 lineas] =====
    let sa: i32 = 10;
    let sb: i32 = 4;
    let sc: f64 = 2.5;
    let s1 = String::from("Hola ");
    let s2 = String::from("Mundo");
    let sum_ii = sa + sb;
    let sum_if = sa + sc;
    let sum_ss = s1 + s2;
    println!("{}", sum_ii);
    println!("{}", sum_if);
    println!("{}", sum_ss);

    // ===== CASO 1.10-b: resta (i32-i32, f64-i32, negacion unaria) [salida: 3 lineas] =====
    let ra: i32 = 10;
    let rb: i32 = 4;
    let rc: f64 = 2.5;
    let res_ii = ra - rb;
    let res_fi = rc - rb;
    let res_neg = -ra;
    println!("{}", res_ii);
    println!("{}", res_fi);
    println!("{}", res_neg);

    // ===== CASO 1.10-c: multiplicacion (i32*i32, i32*f64, i32*String) [salida: 3 lineas] =====
    let ma: i32 = 10;
    let mb: i32 = 4;
    let mk: i32 = 3;
    let mf: f64 = 2.5;
    let ms = String::from("ab");
    let mul_ii = ma * mb;
    let mul_if = mk * mf;
    let mul_is = mk * ms;
    println!("{}", mul_ii);
    println!("{}", mul_if);
    println!("{}", mul_is);

    // ===== CASO 1.10-d: division (i32/i32, f64/i32, i32/f64) [salida: 3 lineas] =====
    let da: i32 = 20;
    let db: i32 = 5;
    let df: f64 = 7.5;
    let dk: i32 = 3;
    let dp: i32 = 15;
    let dt: f64 = 2.0;
    let div_ii = da / db;
    let div_fi = df / dk;
    let div_if = dp / dt;
    println!("{}", div_ii);
    println!("{}", div_fi);
    println!("{}", div_if);

    // ===== CASO 1.10-e: modulo (i32%i32, i32%f64, f64%i32) [salida: 3 lineas] =====
    let ea: i32 = 17;
    let eb: i32 = 5;
    let ec: i32 = 8;
    let ef: f64 = 2.5;
    let eg: f64 = 7.5;
    let ek: i32 = 2;
    let mod_ii = ea % eb;
    let mod_if = ec % ef;
    let mod_fi = eg % ek;
    println!("{}", mod_ii);
    println!("{}", mod_if);
    println!("{}", mod_fi);

    // ######################################################################
    // ## CRITERIO 1.11: Operadores relacionales (0.25 c/u = 1.5 pts)
    // ######################################################################
    // ===== CASO 1.11-a: == [salida: 6 lineas] =====
    let ea_11: i32 = 5;
    let eb_11: i32 = 5;
    let ef_11: f64 = 2.5;
    let eg_11: f64 = 2.5;
    let ec1: char = 'a';
    let ec2: char = 'b';
    let es1 = String::from("hola");
    let es2 = String::from("hola");
    println!("{}", ea_11 == eb_11);
    println!("{}", ea_11 == ef_11);
    println!("{}", ef_11 == eg_11);
    println!("{}", ec1 == ec2);
    println!("{}", es1 == es2);
    println!("{}", true == false);

    // ===== CASO 1.11-b: != [salida: 6 lineas] =====
    let na: i32 = 5;
    let nb: i32 = 5;
    let nf: f64 = 2.5;
    let ng: f64 = 2.5;
    let nc1: char = 'a';
    let nc2: char = 'b';
    let ns1 = String::from("hola");
    let ns2 = String::from("hola");
    println!("{}", na != nb);
    println!("{}", na != nf);
    println!("{}", nf != ng);
    println!("{}", nc1 != nc2);
    println!("{}", ns1 != ns2);
    println!("{}", true != false);

    // ===== CASO 1.11-c: > [salida: 4 lineas] =====
    let ga: i32 = 7;
    let gb: i32 = 3;
    let gf: f64 = 3.5;
    let gh: f64 = 2.5;
    let gc1: char = 'b';
    let gc2: char = 'a';
    println!("{}", ga > gb);
    println!("{}", gb > gf);
    println!("{}", gh > gh);
    println!("{}", gc1 > gc2);

    // ===== CASO 1.11-d: >= [salida: 4 lineas] =====
    let ha: i32 = 7;
    let hb: i32 = 3;
    let hf: f64 = 3.5;
    let hh: f64 = 2.5;
    let hc1: char = 'a';
    let hc2: char = 'b';
    println!("{}", ha >= ha);
    println!("{}", hb >= hf);
    println!("{}", hh >= hh);
    println!("{}", hc1 >= hc2);

    // ===== CASO 1.11-e: < [salida: 4 lineas] =====
    let la: i32 = 7;
    let lb: i32 = 3;
    let lf: f64 = 3.5;
    let lh: f64 = 2.5;
    let lc1: char = 'a';
    let lc2: char = 'b';
    println!("{}", lb < la);
    println!("{}", lb < lf);
    println!("{}", lh < lh);
    println!("{}", lc1 < lc2);

    // ===== CASO 1.11-f: <= [salida: 4 lineas] =====
    let ia: i32 = 7;
    let ib: i32 = 3;
    let ig: i32 = 4;
    let ih: f64 = 3.5;
    let ij: f64 = 2.5;
    let ic1: char = 'b';
    let ic2: char = 'a';
    println!("{}", ia <= ib);
    println!("{}", ig <= ih);
    println!("{}", ij <= ij);
    println!("{}", ic1 <= ic2);

    // ######################################################################
    // ## CRITERIO 1.12: Operadores logicos (0.5 c/u = 1.5 pts)
    // ######################################################################
    // ===== CASO 1.12-a: ! (negacion) [salida: 2 lineas] =====
    let nt: bool = true;
    let nf_12: bool = false;
    println!("{}", !nt);
    println!("{}", !nf_12);

    // ===== CASO 1.12-b: && (conjuncion) [salida: 4 lineas] =====
    let at: bool = true;
    let af: bool = false;
    println!("{}", at && at);
    println!("{}", at && af);
    println!("{}", af && at);
    println!("{}", af && af);

    // ===== CASO 1.12-c: || (disyuncion) [salida: 4 lineas] =====
    let ot: bool = true;
    let of: bool = false;
    println!("{}", ot || ot);
    println!("{}", ot || of);
    println!("{}", of || ot);
    println!("{}", of || of);

    // ######################################################################
    // ## CRITERIO 1.13: Restriccion de cortocircuito (0.5 c/u = 1.5 pts)
    // ######################################################################
    // ===== CASO 1.13-a: false && f()  -> f() no se evalua [salida: 1 linea] =====
    let ca: bool = false;
    let ra_13: bool = ca && marca(1);
    println!("{}", ra_13);

    // ===== CASO 1.13-b: true || f()  -> f() no se evalua [salida: 1 linea] =====
    let cb: bool = true;
    let rb_13: bool = cb || marca(2);
    println!("{}", rb_13);

    // ===== CASO 1.13-c: combinado (false && f()) || (true && f()) [salida: 2 lineas] =====
    let cc: bool = false;
    let cd: bool = true;
    let rc_13: bool = (cc && marca(3)) || (cd && marca(4));
    println!("{}", rc_13);

    // ######################################################################
    // ## CRITERIO 1.14: Manejo de None (1 pt)
    // ######################################################################
    // ===== CASO 1.14: i32 + String -> None [salida: 2 lineas] =====
    let n: i32 = 10;
    let nombre = String::from("Ana");
    let resultado = n + nombre;
    println!("{}", resultado);
    println!("continua");

    // ######################################################################
    // ## CRITERIO 1.15: Literales y secuencias de escape (1 c/u = 2 pts)
    // ######################################################################
    // ===== CASO 1.15-a: secuencias de escape [salida: 4 lineas] =====
    let mensaje = String::from("Hola\nRust");
    let comillas = String::from("Dijo: \"Hola\"");
    let ruta = String::from("C:\\Users\\Diego");
    println!("{}", mensaje);
    println!("{}", comillas);
    println!("{}", ruta);

    // ===== CASO 1.15-b: raw strings [salida: 2 lineas] =====
    let ruta_raw = String::from(r"C:\Users\Diego");
    let texto_raw = String::from(r#"Dijo: "Hola Rust""#);
    println!("{}", ruta_raw);
    println!("{}", texto_raw);
}
