"""Local compiler API. CSRF protection remains enabled for browser requests."""
from dataclasses import asdict
import json
from pathlib import Path
from time import perf_counter
from django.conf import settings
from django.shortcuts import render
from django.views.decorators.csrf import ensure_csrf_cookie
from django.http import JsonResponse
from django.core.exceptions import RequestDataTooBig
from django.views.decorators.http import require_POST, require_GET
from compiler.pipeline import compile_source, execute_source
from compiler.reports import build_reports

MAX_SOURCE_BYTES = 65536


def source_from_request(request):
    if request.content_type != "application/json":
        return None, JsonResponse({"error": "Se requiere application/json."}, status=415)
    try:
        payload = json.loads(request.body)
    except RequestDataTooBig:
        return None, JsonResponse({"error": "Solicitud demasiado grande."}, status=413)
    except (ValueError, UnicodeError):
        return None, JsonResponse({"error": "JSON inválido."}, status=400)
    if not isinstance(payload, dict) or not isinstance(payload.get("source"), str):
        return None, JsonResponse({"error": "source debe ser una cadena."}, status=400)
    try:
        size = len(payload["source"].encode("utf-8"))
    except UnicodeError:
        return None, JsonResponse({"error": "source debe contener Unicode válido."}, status=400)
    if size > MAX_SOURCE_BYTES:
        return None, JsonResponse({"error": "El código excede 64 KiB."}, status=413)
    return payload["source"], None


@require_POST
def compile_view(request):
    source, error = source_from_request(request)
    if error is not None:
        return error
    started = perf_counter()
    compiled = compile_source(source)
    return report_response({**asdict(compiled), "success": not compiled.diagnostics}, started)


@require_POST
def run_view(request):
    source, error = source_from_request(request)
    if error is not None:
        return error
    started = perf_counter()
    return report_response(execute_source(source), started)


def report_response(result, started):
    result["reports"] = build_reports(result)
    result["elapsed_ms"] = round((perf_counter() - started) * 1000, 1)
    return JsonResponse(result)


@ensure_csrf_cookie
@require_GET
def home(request):
    definitions = [("inicio.ox", "Funciones y recursión"), ("matrices.ox", "Arreglos y slices"), ("diagnosticos.ox", "Recuperación de errores")]
    examples = [{"name": name, "description": description, "source": (Path(settings.BASE_DIR) / "examples" / name).read_text(encoding="utf-8")}
                for name, description in definitions]
    return render(request, "index.html", {"examples": examples, "initial_source": examples[0]["source"]})
