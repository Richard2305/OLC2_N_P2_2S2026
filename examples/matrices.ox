fn main() {
    let mut matriz: [[i32; 3]; 2] = [[1, 2, 3], [4, 5, 6]];
    matriz[1][2] = 42;

    println!("Matriz: {:?}", matriz);
    println!("Elemento [1][2]: {}", matriz[1][2]);

    let fila = &matriz[0..1];
    println!("Primera fila: {:?}", fila);
    println!("Cantidad de filas: {}", matriz.len());
}
