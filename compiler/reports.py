"""Self-contained HTML reports and a Graphviz rendering of the actual AST."""
from html import escape
import json
from pathlib import Path
import tempfile
from compiler.runner import _process

MAX_GRAPH_NODES = 3000
MAX_SVG_BYTES = 8 * 1024 * 1024


def ast_to_dot(tree):
    lines = ['digraph AST {', 'graph [rankdir=LR, bgcolor="transparent", pad="0.25", nodesep="0.15", ranksep="0.45"];',
             'node [shape=box, style="rounded,filled", fillcolor="#eff5fb", color="#9fb5ce", fontname="sans-serif", fontsize=11];',
             'edge [color="#6c88a5", arrowsize=0.6];']
    stack = [(tree, None)] if tree else []
    count = 0
    while stack:
        node, parent = stack.pop()
        if count >= MAX_GRAPH_NODES:
            raise ValueError(f"El AST excede el límite de {MAX_GRAPH_NODES} nodos del visor gráfico.")
        current = count
        count += 1
        value = node.get("value")
        detail = "" if value is None else json.dumps(value, ensure_ascii=False)
        if len(detail) > 100:
            detail = detail[:97] + "…"
        position = node.get("position", {})
        label = node.get("kind", "nodo") + ("\n" + detail if detail else "")
        label += f"\nL{position.get('line', '?')}:{position.get('column', '?')}"
        lines.append(f"n{current} [label={json.dumps(label, ensure_ascii=False)}];")
        if parent is not None:
            lines.append(f"n{parent} -> n{current};")
        stack.extend((child, current) for child in reversed(node.get("children", [])))
    return "\n".join(lines + ['}'])


def graphviz_svg(dot):
    with tempfile.TemporaryDirectory(prefix="oxigen-report-") as directory:
        source = Path(directory) / "ast.dot"
        source.write_text(dot, encoding="utf-8")
        rendered = _process(["dot", "-Tsvg", str(source)], timeout=5, max_output=MAX_SVG_BYTES)
    if not rendered["success"]:
        raise ValueError("Graphviz no pudo generar el gráfico dentro de los límites del visor.")
    return rendered["stdout"]


def html_table(title, headings, rows, note=""):
    headers = "".join(f"<th scope=col>{escape(str(value))}</th>" for value in headings)
    body = "".join("<tr>" + "".join(f"<td>{escape(str(value))}</td>" for value in row) + "</tr>" for row in rows)
    if not body:
        body = f'<tr><td colspan="{len(headings)}">Sin registros.</td></tr>'
    return f"""<!doctype html><html lang="es"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>{escape(title)} · OxigenNative</title>
<style>body{{font:15px/1.6 system-ui,sans-serif;color:#18344e;background:#f2f6fa;margin:0;padding:32px}}
main{{max-width:1200px;margin:auto}}h1{{font-size:26px}}table{{border-collapse:collapse;width:100%;background:white}}
th,td{{text-align:left;vertical-align:top;padding:12px;border:1px solid #cbd8e5;white-space:pre-wrap;overflow-wrap:anywhere}}
th{{background:#e6eef7}}.table{{overflow:auto}}p{{color:#49617a}}@media print{{body{{padding:0;background:white}}}}</style>
</head><body><main><p>OxigenNative / Reporte de compilación</p><h1>{escape(title)}</h1>
<p>{escape(note)}</p><div class="table"><table><thead><tr>{headers}</tr></thead><tbody>{body}</tbody></table></div>
</main></body></html>"""


def build_reports(result):
    errors = [(index, d["category"], d["message"], d["position"]["line"], d["position"]["column"], d.get("fragment", ""))
              for index, d in enumerate(result.get("diagnostics", []), 1)]
    symbols = [(index, s["name"], s.get("category", "Variable"), s["type"], s["scope"], s["line"],
                "Sí" if s["mutable"] else "No", s.get("value", "—"))
               for index, s in enumerate(result.get("symbols", []), 1)]
    reports = {
        "errors_html": html_table("Errores", ["No.", "Tipo", "Descripción", "Línea", "Columna", "Fragmento"], errors),
        "symbols_html": html_table("Tabla de símbolos", ["No.", "Identificador", "Categoría", "Tipo", "Ámbito", "Línea", "Mutable", "Valor inicial"], symbols,
            "Se muestran declaraciones y parámetros registrados en el análisis. Los valores iniciales literales no representan el estado final de QEMU; — indica un valor calculado o no disponible."),
        "ast_dot": None, "ast_svg": None, "ast_error": None,
    }
    try:
        reports["ast_dot"] = ast_to_dot(result.get("ast"))
        reports["ast_svg"] = graphviz_svg(reports["ast_dot"])
    except (OSError, ValueError) as error:
        reports["ast_error"] = str(error) if isinstance(error, ValueError) else "Graphviz no está disponible. Instala dot para generar el gráfico."
    return reports
