"""python -m compiler program.ox [--run] [--emit program.s]"""
import argparse
from pathlib import Path
import sys
from compiler.pipeline import compile_source, execute_compiled


def main():
    parser = argparse.ArgumentParser(description="Compilar OxigenNative a ARM64")
    parser.add_argument("source", type=Path)
    parser.add_argument("--run", action="store_true", help="Ensamblar, enlazar y ejecutar con QEMU")
    parser.add_argument("--emit", type=Path, help="Guardar el ensamblador generado")
    args = parser.parse_args()
    try:
        source = args.source.read_text(encoding="utf-8")
        result = compile_source(source)
    except (OSError, UnicodeError) as error:
        parser.exit(2, f"{error}\n")
    for diagnostic in result.diagnostics:
        p = diagnostic.position
        print(f"[Error {diagnostic.category}] Línea {p.line}, Columna {p.column}\n{diagnostic.message}", file=sys.stderr)
    if args.emit and result.assembly:
        args.emit.write_text(result.assembly, encoding="utf-8")
    successful = not result.diagnostics
    if args.run and result.assembly:
        execution = execute_compiled(result, source)
        for diagnostic in execution["diagnostics"][len(result.diagnostics):]:
            p = diagnostic["position"]
            print(f"[Error {diagnostic['category']}] Línea {p['line']}, Columna {p['column']}\n{diagnostic['message']}", file=sys.stderr)
        print(execution["stdout"], end="")
        print(execution["stderr"], end="", file=sys.stderr)
        successful = successful and execution["success"]
    elif not args.emit and not args.run:
        print(result.assembly, end="")
    return 0 if successful else 1

if __name__ == "__main__":
    sys.exit(main())
