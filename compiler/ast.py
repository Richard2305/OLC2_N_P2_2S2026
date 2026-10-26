"""Source-positioned, serializable syntax tree, independent of PLY."""
from dataclasses import dataclass, field
from typing import Any
from compiler.model import SourcePosition

@dataclass
class Node:
    kind: str
    position: SourcePosition
    value: Any = None
    children: list["Node"] = field(default_factory=list)

@dataclass
class ParseResult:
    ast: Node
    diagnostics: list
