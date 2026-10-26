fn main() {
    let contador: i32 = 10;
    contador = 20; // No se puede modificar una variable inmutable.
    println!("El contador sigue en {}", contador);

    let numeros = [1, 2, 3];
    let indice: i32 = 8;
    println!("{}", numeros[indice]); // Se detecta durante la ejecución.

    println!("El programa continúa después del error.");
}
