from dataclasses import dataclass, field

@dataclass(frozen=True)
class SourcePosition:
    line: int
    column: int

@dataclass(frozen=True)
class Diagnostic:
    category: str
    message: str
    position: SourcePosition
    fragment: str = ""

@dataclass
class CompilationResult:
    assembly: str = ""
    diagnostics: list[Diagnostic] = field(default_factory=list)
    ast: object = None
    symbols: list = field(default_factory=list)
