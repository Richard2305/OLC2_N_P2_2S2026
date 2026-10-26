import json
import os
from unittest.mock import patch
from xml.etree import ElementTree
import django
from django.test import Client
import pytest
from compiler.pipeline import execute_source
from compiler.reports import ast_to_dot, build_reports

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()


def test_home_initializes_csrf_and_real_examples():
    client = Client(enforce_csrf_checks=True)
    page = client.get("/")
    assert page.status_code == 200
    assert "csrftoken" in client.cookies
    assert b'id="source"' in page.content
    assert b'id="examples-data"' in page.content
    source = 'fn main(){let x=3; println!(x);}'
    response = client.post("/api/run/", data={"source": source}, content_type="application/json", HTTP_X_CSRFTOKEN=client.cookies["csrftoken"].value)
    result = response.json()
    assert result["success"] and result["stdout"] == "3\n"
    assert result["elapsed_ms"] >= 0
    assert "digraph AST" in result["reports"]["ast_dot"]
    assert "Tabla de símbolos" in result["reports"]["symbols_html"]
    tree = ElementTree.fromstring(result["reports"]["ast_svg"])
    assert tree.tag.endswith("svg")


def test_reports_escape_source_in_html_and_dot():
    source = 'fn main(){let x = "<script>alert(1)</script>"; println!(x);}'
    result = execute_source(source)
    reports = build_reports(result)
    assert "<script>alert" not in reports["symbols_html"]
    assert "&lt;script&gt;" in reports["symbols_html"]
    assert "&lt;script&gt;" in reports["ast_svg"]
    ElementTree.fromstring(reports["ast_svg"])


def test_runtime_diagnostics_are_in_the_exported_report():
    response = Client().post("/api/run/", data={"source": 'fn main(){let a=[1]; let i=8; println!(a[i]); println!("fin");}'}, content_type="application/json")
    result = response.json()
    assert not result["success"]
    assert result["stdout"] == "fin\n"
    assert "Índice fuera de los límites" in result["reports"]["errors_html"]
    assert "Línea" in result["reports"]["errors_html"]


def test_missing_graphviz_does_not_break_compilation_or_html_reports():
    with patch("compiler.reports.graphviz_svg", side_effect=FileNotFoundError()):
        response = Client().post("/api/compile/", data={"source": "fn main(){}"}, content_type="application/json")
    result = response.json()
    assert result["success"]
    assert result["reports"]["ast_svg"] is None
    assert result["reports"]["ast_dot"]
    assert "Graphviz" in result["reports"]["ast_error"]
    assert result["reports"]["errors_html"]


def test_large_graph_is_bounded_without_losing_ast_or_other_reports():
    result = execute_source('fn main(){println!("ok");}')
    with patch("compiler.reports.MAX_GRAPH_NODES", 2):
        reports = build_reports(result)
    assert reports["ast_svg"] is None
    assert "límite" in reports["ast_error"]
    assert reports["symbols_html"]
    assert result["ast"]["kind"] == "program"


def test_function_and_parameter_symbols_keep_distinct_categories():
    result = execute_source('fn f(n:i32)->i32{return n;} fn main(){let x=3; println!(f(x));}')
    by_name = {symbol["name"]: symbol for symbol in result["symbols"]}
    assert by_name["f"]["category"] == "Función"
    assert by_name["f"]["type"] == "i32"
    assert by_name["n"]["category"] == "Parámetro"
    assert by_name["x"]["value"] == "3"
    assert by_name["n"]["value"] == "—"


def test_dot_labels_cannot_inject_graphviz_attributes_or_links():
    payload = '\" ]; injected [URL=\"javascript:alert(1)\"]; //'
    dot = ast_to_dot({"kind": "literal", "value": payload, "position": {"line": 1, "column": 1}, "children": []})
    # Escaped quotes keep the entire payload inside a single node label.
    assert dot.count(' [label=') == 1
    assert dot.count('n0 [label=') == 1
    reports = build_reports({"ast": {"kind": "literal", "value": payload, "children": []}})
    assert reports["ast_svg"]
    assert 'xlink:href=' not in reports["ast_svg"]
