from pathlib import Path
import pytest
from compiler.lexer import Lexer
from compiler.parser import Parser, parse

FIXTURES = Path(__file__).parent / "fixtures" / "entradas"

@pytest.mark.parametrize("path", [p for p in FIXTURES.glob("*.ox") if p.name != "8_errores.ox"], ids=lambda p: p.name)
def test_official_valid_programs(path):
    result = parse(path.read_text())
    assert not result.diagnostics
    assert any(node.value == "main" for node in result.ast.children)


def test_precedence_and_source_positions():
    result = parse("fn main() {\n let x = 1 + 2 * 3;\n}")
    declaration = result.ast.children[0].children[-1].children[0]
    expression = declaration.children[0]
    assert expression.value == "+"
    assert expression.children[1].value == "*"
    assert declaration.position.line == 2
    assert declaration.position.column == 2


def test_raw_strings_unicode_and_labels():
    lexer = Lexer("r\"C:\\Users\" r#\"Dijo: \"Hola\"\"# 'ñ' 'externo: loop {}")
    tokens = list(iter(lexer.token, None))
    assert not lexer.diagnostics
    assert [t.type for t in tokens[:4]] == ["STRING", "STRING", "CHAR", "LABEL"]
    assert tokens[0].value == "C:\\Users"
    assert tokens[1].value == 'Dijo: "Hola"'
    assert tokens[2].value == "ñ"


def test_errors_preserve_main_and_following_statements():
    result = parse((FIXTURES / "8_errores.ox").read_text())
    assert len(result.ast.children) == 2
    main = result.ast.children[-1]
    assert main.value == "main"
    statements = main.children[-1].children
    assert statements[-1].kind == "macro_call"
    assert statements[-1].children[1].value["value"] == "fin"
    assert {d.category for d in result.diagnostics} == {"Léxico", "Sintáctico"}
    assert any(d.position.line == 25 and d.position.column == 17 for d in result.diagnostics)


def test_type_names_are_not_string_literals():
    assert parse('fn main() { let x: "i32" = 1; }').diagnostics


def test_parser_reuse_does_not_leak_diagnostics():
    parser = Parser()
    assert parser.parse("@").diagnostics
    assert not parser.parse("fn main() {}").diagnostics
