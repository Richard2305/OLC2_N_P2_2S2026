import os
import json
import django
from django.test import Client

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()


def test_compile_endpoint_returns_assembly_ast_and_symbols():
    response = Client().post("/api/compile/", data=json.dumps({"source": "fn main(){let x=7; println!(x);}"}), content_type="application/json")
    assert response.status_code == 200
    result = response.json()
    assert result["success"]
    assert "ox_fn_main:" in result["assembly"]
    assert result["ast"]["kind"] == "program"
    assert result["symbols"][0]["name"] == "x"


def test_run_endpoint_returns_qemu_output():
    response = Client().post("/api/run/", data={"source": 'fn main(){println!("Hola");}'}, content_type="application/json")
    result = response.json()
    assert result["success"]
    assert result["executed"]
    assert result["stdout"] == "Hola\n"


def test_api_validates_content_type_json_shape_source_and_size():
    client = Client()
    assert client.get("/api/run/").status_code == 405
    assert client.post("/api/run/", data="x", content_type="text/plain").status_code == 415
    for payload in ["{", "[]", '{"source": 3}', '{"source": "\\ud800"}']:
        assert client.post("/api/run/", data=payload, content_type="application/json").status_code == 400
    assert client.post("/api/run/", data={"source": "x" * 65537}, content_type="application/json").status_code == 413


def test_browser_posts_keep_csrf_protection():
    client = Client(enforce_csrf_checks=True)
    assert client.post("/api/run/", data={"source": "fn main(){}"}, content_type="application/json").status_code == 403


def test_runtime_bounds_error_is_structured_and_execution_continues():
    response = Client().post("/api/run/", data={"source": 'fn main(){let a=[1,2]; let i=8; println!(a[i]); println!("fin");}'}, content_type="application/json")
    result = response.json()
    assert result["executed"] and not result["success"]
    assert result["exit_code"] == 0
    assert result["stdout"] == "fin\n"
    assert not result["stderr"]
    assert result["diagnostics"][0]["category"] == "Semántico"
    assert result["diagnostics"][0]["position"]["column"] > 1
    assert result["symbols"][0]["type"] == "[i32; 2]"
