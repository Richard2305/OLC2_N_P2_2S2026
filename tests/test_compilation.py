from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import pytest
from compiler.pipeline import compile_source, execute_source
from compiler.runner import run_assembly

FIXTURES = Path(__file__).parent / "fixtures"

@pytest.mark.parametrize("name", ["99_integral_minimo", "1_basicas", "2_intermedias", "3_funciones", "3_09_main_hoisting", "4_embebidas", "5_arreglos"])
def test_official_program_runs_as_real_arm64(name):
    source = (FIXTURES / "entradas" / f"{name}.ox").read_text()
    expected = (FIXTURES / "esperadas" / f"{name}.esperado.txt").read_text()
    output = expected.split("## SALIDA ESTANDAR\n")[-1]
    result = execute_source(source)
    assert result["executed"], result
    assert result["exit_code"] == 0, result["stderr"]
    assert result["stdout"] == output
    assert "bl ox_fn_main" in result["assembly"]
    if name == "1_basicas":
        assert len(result["diagnostics"]) == 1
        diagnostic = result["diagnostics"][0]
        assert diagnostic["category"] == "Semántico"
        assert diagnostic["position"] == {"line": 465, "column": 23}
        assert not result["success"]  # Recovered output does not hide diagnostics.
    else:
        assert result["success"], result["diagnostics"]


def run(body, functions=""):
    return execute_source("fn main() {" + body + "}" + functions)


def test_scopes_shadowing_and_immutable_assignment_recovery():
    result = run('let x = 1; { let x = 2; println!(x); } x = 9; println!(x); println!(missing); println!("fin");')
    assert result["stdout"] == "2\n1\nfin\n"
    assert len(result["diagnostics"]) == 2
    assert "inmutable" in result["diagnostics"][0]["message"]
    assert len({s["scope"] for s in result["symbols"] if s["category"] == "Variable"}) == 2


def test_types_and_invalid_initializer_are_recovered_safely():
    result = run('let x: i32 = "oops"; println!(x); let y: i32 = 1.5; println!(y); if 1 { println!("bad"); } println!("fin");')
    assert result["stdout"] == "0\n0\nfin\n"
    assert len(result["diagnostics"]) == 3


def test_short_circuit_prevents_runtime_errors_and_side_effects():
    result = run('println!(false && (1 / 0 > 0)); println!(true || side()); println!(true && side());',
                 'fn side() -> bool { println!("side"); return true; }')
    assert result["success"], result
    assert result["stdout"] == "false\ntrue\nside\ntrue\n"


def test_float_arguments_return_and_independent_argument_register_classes():
    result = run('println!("{}", mixed(3, 2.5, 4, 1.0));',
                 'fn mixed(a: i32, b: f64, c: i32, d: f64) -> f64 { return (a + b) * (c - d); }')
    assert result["success"], result
    assert result["stdout"] == "16.5\n"


def test_eight_arguments_and_nested_calls_are_preserved():
    result = run('println!(sum(1, 2, 3, 4, 5, 6, 7, sum(1,1,1,1,1,1,1,1)));',
                 'fn sum(a:i32,b:i32,c:i32,d:i32,e:i32,f:i32,g:i32,h:i32)->i32 { return a+b+c+d+e+f+g+h; }')
    assert result["success"], result
    assert result["stdout"] == "36\n"


def test_print_arguments_are_evaluated_before_format_is_written():
    result = run('println!("valor {}", side());',
                 'fn side()->i32 { println!("primero"); return 7; }')
    assert result["success"], result
    assert result["stdout"] == "primero\nvalor 7\n"


def test_utf8_characters_and_embedded_null_strings():
    result = run('println!("{} {} {}", \'ñ\', \'漢\', \'😀\'); println!("a\\0b" + "é"); println!(2 * "ñ");')
    assert result["success"], result
    assert result["stdout"] == "ñ 漢 😀\na\0bé\nññ\n"


def test_signed_division_modulo_i32_boundary_and_f64_promotion():
    result = run('println!("{} {} {}", -7 / 3, -7 % 3, -2147483648); println!("{} {}", 5.5 % 2.0, 2 + 0.5);')
    assert result["success"], result
    assert result["stdout"] == "-2 -1 -2147483648\n1.5 2.5\n"


def test_match_break_and_continue_restore_expression_stack():
    result = run('let mut n = 0; loop { n += 1; match n { 1 => { continue; }, 2 => { break; }, _ => println!("bad"), } } println!(n);')
    assert result["success"], result
    assert result["stdout"] == "2\n"


@pytest.mark.parametrize("source", ["", "fn main(x:i32) {}", "fn main()->i32{return 1;}"])
def test_missing_or_invalid_entry_point_does_not_execute(source):
    result = execute_source(source)
    assert result["diagnostics"]
    assert not result["executed"]
    assert not result["assembly"]


def test_invalid_calls_return_diagnostics_without_crashing_backend():
    result = run('missing(); f(1); f("wrong", 2); println!("fin");',
                 'fn f(a:i32,b:i32) {}')
    assert len(result["diagnostics"]) == 3
    assert result["stdout"] == "fin\n"


def test_array_literal_executes_in_backend():
    result = run('let a = [1, 2]; println!("{:?}", a);')
    assert result["success"]
    assert result["stdout"] == "[1, 2]\n"


def test_runtime_division_by_zero_is_reported():
    result = run('let x = 0; println!(1 / x);')
    assert not result["success"]
    assert result["stage"] == 2
    assert result["exit_code"] == 1
    assert "División entre cero" in result["stderr"]


def test_runtime_heap_limit():
    result = run('println!(2000000 * "x");')
    assert not result["success"]
    assert "Heap agotado" in result["stderr"]


def test_execution_timeout():
    assembly = compile_source('fn main() { loop {} }').assembly
    result = run_assembly(assembly, timeout=0.1)
    assert not result["success"]
    assert result["stage"] == 2
    assert "Tiempo" in result["stderr"]


def test_output_limit():
    assembly = compile_source('fn main() { loop { println!("0123456789"); } }').assembly
    result = run_assembly(assembly, max_output=512)
    assert not result["success"]
    assert result["stage"] == 2
    assert len(result["stdout"].encode()) <= 512
    assert "Límite" in result["stderr"]


def test_compilations_are_isolated_between_threads():
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(run, ['let x=1; println!(x);', 'let x=2; println!(x);']))
    assert [r["stdout"] for r in results] == ["1\n", "2\n"]
    assert all(r["success"] for r in results)
