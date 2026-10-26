from pathlib import Path
import subprocess
import sys


def test_cli_runs_minimum_and_can_save_executed_assembly(tmp_path):
    assembly = tmp_path / "minimum.s"
    result = subprocess.run([sys.executable, "-m", "compiler", "tests/fixtures/entradas/99_integral_minimo.ox", "--run", "--emit", str(assembly)], text=True, capture_output=True, timeout=10)
    assert result.returncode == 0, result.stderr
    assert result.stdout == Path("tests/fixtures/esperadas/99_integral_minimo.esperado.txt").read_text()
    assert "ox_fn_main:" in assembly.read_text()


def test_cli_reports_diagnostics_and_preserves_recovered_output(tmp_path):
    source = tmp_path / "invalid.ox"
    source.write_text('fn main(){ println!(missing); println!("fin"); }')
    result = subprocess.run([sys.executable, "-m", "compiler", str(source), "--run"], text=True, capture_output=True, timeout=10)
    assert result.returncode == 1
    assert "Error Semántico" in result.stderr
    assert result.stdout == "fin\n"


def test_cli_formats_recovered_runtime_diagnostics(tmp_path):
    source = tmp_path / "bounds.ox"
    source.write_text('fn main(){let a=[1]; let i=9; println!(a[i]); println!("fin");}')
    result = subprocess.run([sys.executable, "-m", "compiler", str(source), "--run"], text=True, capture_output=True, timeout=10)
    assert result.returncode == 1
    assert result.stdout == "fin\n"
    assert "[Error Semántico] Línea 1, Columna" in result.stderr
    assert "Índice fuera de los límites" in result.stderr
    assert "OXERR" not in result.stderr
