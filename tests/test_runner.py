from pathlib import Path
from compiler.runner import run_assembly

def test_real_arm64_execution():
    result = run_assembly(Path("examples/hello.s").read_text())
    assert result["success"], result
    assert result["stdout"] == "OxigenNative ARM64\n"

def test_invalid_assembly_is_reported():
    result = run_assembly("this is not assembly")
    assert not result["success"]
    assert result["stage"] == 0
