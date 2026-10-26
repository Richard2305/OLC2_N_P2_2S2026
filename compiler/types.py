"""Canonical type names and row-major storage shared by analysis/code generation."""
from dataclasses import dataclass
from functools import lru_cache

@dataclass(frozen=True)
class Sequence:
    element: str
    length: int | None
    borrowed: bool = False


def array_type(element, length):
    return f"[{element}; {length}]"


def slice_type(element):
    return f"&[{element}]"


@lru_cache(maxsize=4096)
def sequence(type_):
    if type_.startswith("&[") and type_.endswith("]"):
        return Sequence(type_[2:-1], None, True)
    if type_.startswith("[") and type_.endswith("]"):
        inside = type_[1:-1]
        # A semicolon belongs to this dimension only at nesting depth zero.
        depth = 0
        for index, character in enumerate(inside):
            if character == "[":
                depth += 1
            elif character == "]":
                depth -= 1
            elif character == ";" and depth == 0:
                return Sequence(inside[:index].strip(), int(inside[index + 1:].strip()))
        return Sequence(inside, None)
    return None


def storage_size(type_):
    info = sequence(type_)
    return info.length * storage_size(info.element) if info and info.length is not None else 8


def fixed_array(type_):
    info = sequence(type_)
    return info is not None and info.length is not None


def leaf_type(type_):
    while fixed_array(type_):
        type_ = sequence(type_).element
    return type_
