// Una función, dos formas de ver el resultado.
fn fibonacci(n: i32) -> i32 {
    if n <= 1 {
        return n;
    }
    return fibonacci(n - 1) + fibonacci(n - 2);
}

fn main() {
    let nombre = String::from("OxigenNative");
    let limite: i32 = 8;

    println!("Hola desde {}", nombre);
    println!("Fibonacci de {}: {}", limite, fibonacci(limite));

    let mut numeros = [10, 20, 30, 40];
    numeros.reverse();
    println!("Arreglo invertido: {:?}", numeros);

    let parte = &numeros[1..3];
    println!("Slice: {:?}", parte);
}
