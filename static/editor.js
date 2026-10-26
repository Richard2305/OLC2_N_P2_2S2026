/* Native editor controls; all displayed compiler data is treated as text. */
(() => {
  "use strict";
  const $ = (id) => document.getElementById(id);
  const editor = $("source");
  const fileName = $("file-name");
  const examples = JSON.parse($("examples-data").textContent);
  const MAX_BYTES = 65536;
  const MAX_DRAFT_BYTES = 1024 * 1024;
  const DRAFT_KEY = "oxigen.editor.v1";
  const encoder = new TextEncoder();
  let savedSource = editor.value;
  let savedName = fileName.value;
  let busy = false;
  let latest = null;
  let resultSource = null;
  let astUrl = null;
  let zoom = 1;
  let draftTimer;

  const escapeText = (value) => String(value).replace(/[&<>"']/g, (character) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
  })[character]);

  function setStatus(message, state = "ready") {
    $("status-text").textContent = message;
    $("app-status").dataset.state = state;
  }

  function isDirty() {
    return editor.value !== savedSource || fileName.value !== savedName;
  }

  function persistDraft() {
    clearTimeout(draftTimer);
    try {
      if (encoder.encode(editor.value).length > MAX_DRAFT_BYTES) throw new Error("draft-size");
      localStorage.setItem(DRAFT_KEY, JSON.stringify({source: editor.value, name: fileName.value, savedSource, savedName}));
      $("draft-state").textContent = "Borrador local";
    } catch {
      $("draft-state").textContent = "Borrador no disponible";
    }
  }

  function updateControls() {
    const oversized = encoder.encode(editor.value).length > MAX_BYTES;
    $("run-button").disabled = busy || oversized;
    $("compile-button").disabled = busy || oversized;
    ["new-button", "open-button", "file-input"].forEach((id) => { $(id).disabled = busy; });
    document.querySelectorAll("[data-example]").forEach((button) => { button.disabled = busy; });
    fileName.disabled = busy;
    editor.readOnly = busy;
    $("dirty-indicator").hidden = !isDirty();
    document.querySelector(".main-workspace").setAttribute("aria-busy", String(busy));
    if (oversized) setStatus("El código excede 64 KiB. Puedes guardarlo para conservarlo.", "error");
  }

  function cursorPosition() {
    const before = editor.value.slice(0, editor.selectionStart);
    const line = before.split("\n").length;
    const column = before.length - before.lastIndexOf("\n");
    $("cursor-position").textContent = `Línea ${line}, columna ${column}`;
    const active = $("line-numbers").querySelector(".active-line");
    if (active) active.classList.remove("active-line");
    $("line-numbers").children[line - 1]?.classList.add("active-line");
  }

  function syncScroll() {
    $("source-highlight").scrollTop = editor.scrollTop;
    $("source-highlight").scrollLeft = editor.scrollLeft;
    $("line-numbers").scrollTop = editor.scrollTop;
  }

  // Wraps each match in a span whose class comes from the first matching capture group.
  function markup(text, pattern, kinds) {
    let last = 0;
    let html = "";
    for (const match of text.matchAll(pattern)) {
      html += escapeText(text.slice(last, match.index));
      const kind = kinds[match.slice(1).findIndex(Boolean)] ?? kinds[kinds.length - 1];
      html += `<span class="${kind}">${escapeText(match[0])}</span>`;
      last = match.index + match[0].length;
    }
    return html + escapeText(text.slice(last));
  }

  const SOURCE_TOKENS = /(\/\/[^\n]*|\/\*[\s\S]*?(?:\*\/|$))|((?:r#*)?"(?:\\.|[^"\\])*"#*|'(?:\\.|[^'\\])')|\b(fn|let|mut|if|else|while|loop|match|break|continue|return|true|false|None|i32|f64|bool|char|String)\b|\b\d+(?:\.\d+)?\b/g;
  const ASM_TOKENS = /((?:\/\/|@).*$)|("(?:\\.|[^"\\])*")|(#-?[\w.]+|=[\w.]+|\b-?\d+\b)|\b([xwdsqv]\d{1,2}|sp|xzr|wzr|lr|fp)\b/g;

  function highlightAssembly(text) {
    return text.trimEnd().split("\n").map((line) => {
      const [, indent, label = "", gap, word = "", rest] = /^(\s*)([\w.$]+:)?(\s*)([.\w]+)?(.*)$/.exec(line);
      const wordClass = word.startsWith(".") ? "asm-directive" : "asm-mnemonic";
      let html = escapeText(indent);
      if (label) html += `<span class="asm-label">${escapeText(label)}</span>`;
      html += escapeText(gap);
      if (word) html += `<span class="${wordClass}">${escapeText(word)}</span>`;
      html += markup(rest, ASM_TOKENS, ["asm-comment", "asm-string", "asm-number", "asm-register"]);
      return `<span class="asm-line${label ? " is-label" : ""}">${html}</span>`;
    }).join("\n");
  }

  function setPipeline(states = {}, railState = "") {
    $("pipeline").dataset.state = railState;
    $("pipeline").querySelectorAll("[data-step]").forEach((step) => { step.dataset.state = states[step.dataset.step] || "idle"; });
  }

  function highlight() {
    const source = editor.value;
    $("source-highlight").innerHTML = markup(source, SOURCE_TOKENS, ["syntax-comment", "syntax-string", "syntax-keyword", "syntax-number"]) + "\n";
    const fragment = document.createDocumentFragment();
    const errorLines = new Set(latest && resultSource === source ? latest.diagnostics.map((d) => d.position.line) : []);
    for (let line = 1; line <= source.split("\n").length; line += 1) {
      const number = document.createElement("span");
      number.textContent = line;
      if (errorLines.has(line)) number.classList.add("error-line");
      fragment.append(number);
    }
    $("line-numbers").replaceChildren(fragment);
    const bytes = encoder.encode(source).length;
    $("source-size").textContent = bytes >= 1024 ? `${(bytes / 1024).toFixed(1)} KiB` : `${bytes} B`;
    cursorPosition();
    syncScroll();
  }

  function changed() {
    highlight();
    updateControls();
    if (latest) {
      const stale = resultSource !== editor.value;
      $("result-version").textContent = stale ? "Resultados de la versión anterior" : "Resultados del código actual";
      $("result-version").classList.toggle("is-stale", stale);
    }
    clearTimeout(draftTimer);
    draftTimer = setTimeout(persistDraft, 350);
  }

  function download(content, name, mime) {
    const url = URL.createObjectURL(new Blob([content], {type: mime}));
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = name;
    document.body.append(anchor);
    anchor.click();
    anchor.remove();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  }

  function baseName() {
    return fileName.value.trim().replace(/[\\/\x00-\x1f]/g, "_").replace(/\.ox$/i, "") || "programa";
  }

  function updateCommand() {
    $("console-command").textContent = `qemu-aarch64 ./${baseName()}`;
  }

  function saveFile() {
    const name = `${baseName()}.ox`;
    download(editor.value, name, "text/plain;charset=utf-8");
    fileName.value = name;
    savedName = name;
    savedSource = editor.value;
    persistDraft();
    updateControls();
    setStatus(`Archivo preparado para descargar: ${name}`);
  }

  async function canReplace() {
    if (!isDirty()) return true;
    const dialog = $("discard-dialog");
    dialog.returnValue = "cancel";
    return new Promise((resolve) => {
      dialog.addEventListener("close", () => resolve(dialog.returnValue === "replace"), {once: true});
      dialog.showModal();
    });
  }

  function selectExample(index) {
    document.querySelectorAll("[data-example]").forEach((button) => {
      const selected = Number(button.dataset.example) === index;
      button.classList.toggle("selected", selected);
      if (selected) button.setAttribute("aria-current", "true");
      else button.removeAttribute("aria-current");
    });
  }

  function resetResults() {
    latest = null;
    resultSource = null;
    if (astUrl) URL.revokeObjectURL(astUrl);
    astUrl = null;
    $("ast-image").removeAttribute("src");
    $("assembly-code").textContent = "";
    $("assembly-code").hidden = true;
    $("assembly-empty").hidden = false;
    $("assembly-state").textContent = "Sin compilar";
    $("assembly-lines").textContent = "0 líneas";
    $("stdout").textContent = "";
    $("stderr").textContent = "";
    $("stdout").hidden = $("stderr").hidden = true;
    $("console-placeholder").hidden = false;
    $("console-placeholder").textContent = "La salida de tu programa aparecerá aquí.";
    $("console-state").textContent = "Listo para ejecutar";
    $("elapsed-time").textContent = "—";
    $("exit-code").hidden = true;
    setPipeline();
    $("errors-description").textContent = "Compila para revisar el análisis del programa.";
    $("errors-empty").hidden = false;
    $("errors-empty").querySelector("p").textContent = "Aún no hay un análisis.";
    $("errors-table-wrap").hidden = true;
    $("errors-body").replaceChildren();
    $("error-count").textContent = $("symbol-count").textContent = "0";
    $("error-count").classList.remove("has-errors");
    $("symbols-empty").hidden = false;
    $("symbols-table-wrap").hidden = true;
    $("symbols-body").replaceChildren();
    $("ast-empty").hidden = false;
    $("ast-empty").textContent = "Compila para visualizar la estructura del programa.";
    $("ast-viewport").hidden = $("ast-structure").hidden = true;
    $("ast-json").textContent = "";
    $("result-version").textContent = "Sin resultados";
    $("result-version").classList.remove("is-stale");
    ["download-assembly", "download-errors", "download-symbols", "download-svg", "download-dot", "ast-zoom-in", "ast-zoom-out", "ast-fit"].forEach((id) => { $(id).disabled = true; });
  }

  function replaceFile(source, name, index = -1, dirty = false) {
    resetResults();
    editor.value = source;
    fileName.value = name;
    savedSource = dirty ? "" : source;
    savedName = name;
    editor.scrollTop = editor.scrollLeft = 0;
    editor.setSelectionRange(0, 0);
    selectExample(index);
    changed();
    persistDraft();
    editor.focus();
    setStatus(`Archivo abierto: ${name}`);
  }

  function activateTab(name, focus = false) {
    for (const tab of ["errors", "symbols", "ast"]) {
      const selected = tab === name;
      $("tab-" + tab).setAttribute("aria-selected", String(selected));
      $("tab-" + tab).tabIndex = selected ? 0 : -1;
      $("panel-" + tab).hidden = !selected;
    }
    if (focus) $("tab-" + name).focus();
    if (name === "ast") requestAnimationFrame(resizeAst);
  }

  function goToPosition(position) {
    if (editor.value !== resultSource) {
      setStatus("Ejecuta el código actual para actualizar las ubicaciones de los errores.", "error");
      return;
    }
    const lines = editor.value.split("\n");
    const line = Math.max(1, Math.min(position.line, lines.length));
    let offset = 0;
    for (let index = 0; index < line - 1; index += 1) offset += lines[index].length + 1;
    offset += Math.max(0, Math.min(position.column - 1, lines[line - 1].length));
    editor.focus();
    editor.setSelectionRange(offset, offset);
    editor.scrollTop = Math.max(0, (line - 1) * 23 - editor.clientHeight / 3);
    cursorPosition();
    syncScroll();
  }

  function cell(row, value) {
    const td = document.createElement("td");
    td.textContent = value;
    row.append(td);
    return td;
  }

  function renderErrors(diagnostics) {
    $("error-count").textContent = diagnostics.length;
    $("error-count").classList.toggle("has-errors", diagnostics.length > 0);
    $("errors-description").textContent = diagnostics.length ? `${diagnostics.length} diagnóstico${diagnostics.length === 1 ? "" : "s"}. Selecciona una ubicación para ir al código.` : "El análisis no encontró errores.";
    $("errors-empty").hidden = diagnostics.length > 0;
    $("errors-empty").querySelector("p").textContent = "Sin errores en este programa.";
    $("errors-table-wrap").hidden = !diagnostics.length;
    const fragment = document.createDocumentFragment();
    for (const diagnostic of diagnostics) {
      const row = document.createElement("tr");
      const badge = document.createElement("span");
      badge.className = "error-type";
      badge.textContent = diagnostic.category;
      cell(row, "").append(badge);
      const description = cell(row, diagnostic.message);
      if (diagnostic.fragment) {
        const code = document.createElement("code");
        code.textContent = diagnostic.fragment;
        description.append(code);
      }
      const button = document.createElement("button");
      button.type = "button";
      button.className = "location-button";
      button.textContent = `L${diagnostic.position.line}:${diagnostic.position.column}`;
      button.setAttribute("aria-label", `Ir a línea ${diagnostic.position.line}, columna ${diagnostic.position.column}`);
      button.addEventListener("click", () => goToPosition(diagnostic.position));
      cell(row, "").append(button);
      fragment.append(row);
    }
    $("errors-body").replaceChildren(fragment);
  }

  function renderSymbols(symbols) {
    $("symbol-count").textContent = symbols.length;
    $("symbols-empty").hidden = symbols.length > 0;
    $("symbols-table-wrap").hidden = !symbols.length;
    const fragment = document.createDocumentFragment();
    for (const symbol of symbols) {
      const row = document.createElement("tr");
      [symbol.name, symbol.category || "Variable", symbol.type, symbol.scope, symbol.line, symbol.mutable ? "Sí" : "No", symbol.value || "—"].forEach((value) => cell(row, value));
      fragment.append(row);
    }
    $("symbols-body").replaceChildren(fragment);
  }

  function resizeAst() {
    if (!astUrl || $("panel-ast").hidden) return;
    const width = Math.max(200, $("ast-viewport").clientWidth - 40);
    $("ast-image").style.width = `${width * zoom}px`;
  }

  function renderAst(result) {
    const reports = result.reports;
    $("ast-json").textContent = JSON.stringify(result.ast, null, 2);
    $("ast-structure").hidden = !result.ast;
    $("download-dot").disabled = !reports.ast_dot;
    $("download-svg").disabled = !reports.ast_svg;
    if (reports.ast_svg) {
      astUrl = URL.createObjectURL(new Blob([reports.ast_svg], {type: "image/svg+xml"}));
      $("ast-image").src = astUrl;
      $("ast-empty").hidden = true;
      $("ast-viewport").hidden = false;
      zoom = 1;
      ["ast-zoom-in", "ast-zoom-out", "ast-fit"].forEach((id) => { $(id).disabled = false; });
      resizeAst();
    } else {
      $("ast-empty").textContent = reports.ast_error || "No se pudo generar el gráfico. Puedes consultar la estructura de texto.";
    }
  }

  function renderResult(result, source, shouldRun) {
    latest = result;
    resultSource = source;
    $("result-version").textContent = "Resultados del código actual";
    $("assembly-code").innerHTML = highlightAssembly(result.assembly);
    $("assembly-code").hidden = !result.assembly;
    $("assembly-empty").hidden = !!result.assembly;
    $("assembly-state").textContent = result.executed ? "Código enviado a QEMU" : result.assembly ? "Código generado" : "Sin ensamblador";
    $("assembly-lines").textContent = `${result.assembly ? result.assembly.trimEnd().split("\n").length : 0} líneas`;
    $("download-assembly").disabled = !result.assembly;
    $("stdout").textContent = result.stdout || "";
    $("stderr").textContent = result.stderr || "";
    $("stdout").hidden = !result.stdout;
    $("stderr").hidden = !result.stderr;
    $("console-placeholder").hidden = !!(result.stdout || result.stderr);
    $("console-placeholder").textContent = !shouldRun ? "Compilación terminada. Ejecuta el programa para ver su salida." : result.executed ? "El programa terminó sin imprimir." : "No se ejecutó el programa. Revisa los diagnósticos.";
    $("elapsed-time").textContent = `${Math.round(result.elapsed_ms)} ms de procesamiento`;
    $("exit-code").hidden = result.exit_code === null || result.exit_code === undefined;
    $("exit-code").textContent = `Salida ${result.exit_code}`;
    $("exit-code").classList.toggle("is-failure", result.exit_code !== 0);
    const failed = new Set(result.diagnostics.map((diagnostic) => diagnostic.category));
    const mark = (category) => failed.has(category) ? "error" : "done";
    setPipeline({
      source: "done", lexer: mark("Léxico"), parser: mark("Sintáctico"), semantic: mark("Semántico"),
      codegen: result.assembly ? "done" : "error",
      qemu: !shouldRun || !result.assembly ? "idle" : result.executed && result.exit_code === 0 ? "done" : "error",
    });
    const state = result.success ? shouldRun ? "Ejecución completada" : "Compilación completada" : result.diagnostics.length ? "Finalizado con diagnósticos" : "Error de ejecución";
    $("console-state").textContent = state;
    setStatus(state, result.success ? "ready" : "error");
    renderErrors(result.diagnostics);
    if (result.diagnostics.length) activateTab("errors");
    renderSymbols(result.symbols);
    renderAst(result);
    $("download-errors").disabled = !result.reports.errors_html;
    $("download-symbols").disabled = !result.reports.symbols_html;
    highlight();
  }

  async function processSource(shouldRun) {
    if (busy || encoder.encode(editor.value).length > MAX_BYTES) return;
    const source = editor.value;
    resetResults();
    busy = true;
    updateControls();
    setStatus(shouldRun ? "Compilando y ejecutando…" : "Compilando…", "busy");
    setPipeline({}, "busy");
    updateCommand();
    $("console-state").textContent = shouldRun ? "Compilando y ejecutando…" : "Compilando…";
    $("console-placeholder").textContent = "Procesando el programa…";
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), 25000);
    try {
      const token = document.cookie.split("; ").find((cookie) => cookie.startsWith("csrftoken="))?.split("=")[1];
      const response = await fetch(shouldRun ? "/api/run/" : "/api/compile/", {
        method: "POST", headers: {"Content-Type": "application/json", "X-CSRFToken": token ? decodeURIComponent(token) : ""},
        credentials: "same-origin", body: JSON.stringify({source}), signal: controller.signal,
      });
      if (!response.ok) {
        const payload = await response.json().catch(() => ({}));
        throw new Error(payload.error || (response.status === 403 ? "La sesión del editor expiró. Recarga la página; tu borrador se conserva." : `El servidor respondió con un error (${response.status}).`));
      }
      renderResult(await response.json(), source, shouldRun);
    } catch (error) {
      const message = error.name === "AbortError" ? "La solicitud tardó demasiado. Intenta compilar un programa más pequeño." : error instanceof TypeError ? "No se pudo conectar con el servidor. Comprueba que siga en ejecución." : error.message;
      $("console-placeholder").textContent = message;
      $("console-state").textContent = "No se recibieron resultados";
      setPipeline();
      setStatus(message, "error");
    } finally {
      clearTimeout(timer);
      busy = false;
      updateControls();
    }
  }

  $("new-button").addEventListener("click", async () => { if (await canReplace()) replaceFile("fn main() {\n    \n}\n", "programa.ox", -1, true); });
  $("open-button").addEventListener("click", () => $("file-input").click());
  $("file-input").addEventListener("change", async (event) => {
    const file = event.target.files[0];
    event.target.value = "";
    if (!file) return;
    if (file.size > MAX_BYTES) return setStatus("El archivo excede 64 KiB.", "error");
    try {
      const source = new TextDecoder("utf-8", {fatal: true}).decode(await file.arrayBuffer());
      if (await canReplace()) replaceFile(source.replace(/\r\n?/g, "\n"), file.name);
    } catch {
      setStatus("No se pudo abrir el archivo. Comprueba que sea texto UTF-8.", "error");
    }
  });
  document.querySelectorAll("[data-example]").forEach((button) => button.addEventListener("click", async () => {
    const index = Number(button.dataset.example);
    if (await canReplace()) replaceFile(examples[index].source, examples[index].name, index);
  }));
  $("save-button").addEventListener("click", saveFile);
  $("compile-button").addEventListener("click", () => processSource(false));
  $("run-button").addEventListener("click", () => processSource(true));
  $("reports-button").addEventListener("click", () => { $("reports-section").scrollIntoView({block: "start"}); $("tab-errors").focus(); activateTab("errors"); });
  $("clear-console").addEventListener("click", () => {
    $("stdout").hidden = $("stderr").hidden = true;
    $("console-placeholder").hidden = false;
    $("console-placeholder").textContent = "Consola vacía. Los reportes se conservan.";
  });
  for (const name of ["errors", "symbols", "ast"]) {
    $("tab-" + name).addEventListener("click", () => activateTab(name));
    $("tab-" + name).addEventListener("keydown", (event) => {
      const names = ["errors", "symbols", "ast"];
      const current = names.indexOf(name);
      if (!["ArrowLeft", "ArrowRight", "Home", "End"].includes(event.key)) return;
      event.preventDefault();
      const index = event.key === "Home" ? 0 : event.key === "End" ? 2 : (current + (event.key === "ArrowRight" ? 1 : 2)) % 3;
      activateTab(names[index], true);
    });
  }
  $("download-assembly").addEventListener("click", () => { if (latest?.assembly) download(latest.assembly, `${baseName()}.s`, "text/plain;charset=utf-8"); });
  for (const [id, key, extension, mime] of [
    ["download-errors", "errors_html", "errores.html", "text/html;charset=utf-8"],
    ["download-symbols", "symbols_html", "simbolos.html", "text/html;charset=utf-8"],
    ["download-svg", "ast_svg", "ast.svg", "image/svg+xml"],
    ["download-dot", "ast_dot", "ast.dot", "text/vnd.graphviz;charset=utf-8"],
  ]) $(id).addEventListener("click", () => { if (latest?.reports[key]) download(latest.reports[key], `${baseName()}-${extension}`, mime); });
  $("ast-zoom-in").addEventListener("click", () => { zoom = Math.min(16, zoom * 1.5); resizeAst(); });
  $("ast-zoom-out").addEventListener("click", () => { zoom = Math.max(.25, zoom / 1.5); resizeAst(); });
  $("ast-fit").addEventListener("click", () => { zoom = 1; resizeAst(); });
  window.addEventListener("resize", resizeAst);
  $("help-button").addEventListener("click", () => $("help-dialog").showModal());
  $("shortcuts-button").addEventListener("click", () => $("help-dialog").showModal());
  editor.addEventListener("input", changed);
  editor.addEventListener("scroll", syncScroll);
  ["click", "keyup", "select"].forEach((event) => editor.addEventListener(event, cursorPosition));
  fileName.addEventListener("input", () => { updateControls(); updateCommand(); clearTimeout(draftTimer); draftTimer = setTimeout(persistDraft, 350); });
  editor.addEventListener("keydown", (event) => {
    if (event.key !== "Tab" || busy) return;
    event.preventDefault();
    const start = editor.selectionStart;
    const end = editor.selectionEnd;
    const lineStart = editor.value.lastIndexOf("\n", start - 1) + 1;
    if (start === end && !event.shiftKey) editor.setRangeText("    ", start, end, "end");
    else {
      const selected = editor.value.slice(lineStart, end);
      const replacement = selected.split("\n").map((line) => event.shiftKey ? line.replace(/^ {1,4}/, "") : "    " + line).join("\n");
      editor.setRangeText(replacement, lineStart, end, "select");
    }
    changed();
  });
  document.addEventListener("keydown", (event) => {
    if (!(event.ctrlKey || event.metaKey) || document.querySelector("dialog[open]")) return;
    if (event.key === "Enter") { event.preventDefault(); processSource(true); }
    else if (event.key.toLowerCase() === "s") { event.preventDefault(); saveFile(); }
    else if (event.key.toLowerCase() === "o") { event.preventDefault(); if (!busy) $("file-input").click(); }
  });
  window.addEventListener("beforeunload", (event) => {
    persistDraft();
    if (isDirty()) { event.preventDefault(); event.returnValue = ""; }
  });
  try {
    const draft = JSON.parse(localStorage.getItem(DRAFT_KEY));
    if (draft && typeof draft.source === "string" && typeof draft.name === "string" && encoder.encode(draft.source).length <= MAX_DRAFT_BYTES) {
      editor.value = draft.source;
      fileName.value = draft.name.slice(0, 100);
      savedSource = typeof draft.savedSource === "string" ? draft.savedSource : "";
      savedName = typeof draft.savedName === "string" ? draft.savedName : draft.name;
      const index = examples.findIndex((example) => example.source === draft.source && example.name === draft.name);
      selectExample(index);
      setStatus("Borrador local recuperado");
    }
  } catch { /* Storage may be disabled; editing and downloading still work. */ }
  highlight();
  updateControls();
  updateCommand();
})();
