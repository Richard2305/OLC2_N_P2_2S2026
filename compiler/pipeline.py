"""Public compilation boundary shared by CLI and HTTP services."""
from dataclasses import asdict
from compiler.codegen import Generator
from compiler.model import CompilationResult, Diagnostic, SourcePosition
from compiler.parser import parse
from compiler.runner import run_assembly
from compiler.semantic import analyze


def compile_source(source: str) -> CompilationResult:
    parsed = parse(source)
    analysis = analyze(parsed.ast, source)
    main = analysis.functions.get("main")
    assembly = Generator(analysis).generate() if main and id(main.node) not in analysis.invalid else ""
    return CompilationResult(assembly=assembly,
        diagnostics=sorted(parsed.diagnostics + analysis.diagnostics, key=lambda d: (d.position.line, d.position.column)),
        ast=parsed.ast, symbols=analysis.symbols)


def execute_source(source: str, timeout: float = 5) -> dict:
    return execute_compiled(compile_source(source), source, timeout)


def execute_compiled(compiled: CompilationResult, source: str, timeout: float = 5) -> dict:
    """Execute precisely the compilation artifact shown by the API or CLI."""
    result = asdict(compiled)
    result.update({"success": False, "executed": False, "stdout": "", "stderr": "", "exit_code": None})
    if compiled.assembly:
        execution = run_assembly(compiled.assembly, timeout)
        runtime_diagnostics = []
        stderr_lines = []
        for line in execution["stderr"].splitlines(keepends=True):
            parts = line.rstrip("\n").split("\t", 3)
            if len(parts) == 4 and parts[0] == "OXERR" and parts[1].isdigit() and parts[2].isdigit():
                position = SourcePosition(int(parts[1]), int(parts[2]))
                lines = source.splitlines()
                fragment = lines[position.line - 1] if 0 < position.line <= len(lines) else ""
                runtime_diagnostics.append(asdict(Diagnostic("Semántico", parts[3], position, fragment)))
            else:
                stderr_lines.append(line)
        execution["stderr"] = "".join(stderr_lines)
        result.update(execution)
        result["diagnostics"].extend(runtime_diagnostics)
        result["executed"] = execution.get("stage", 2) == 2 and "exit_code" in execution
        result["success"] = execution["success"] and not result["diagnostics"]
    return result
