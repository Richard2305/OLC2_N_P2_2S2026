"""Assemble, link and execute AArch64 with bounded output and wall time."""
import os
from pathlib import Path
import selectors
import signal
import subprocess
import tempfile
import time

DEFAULT_OUTPUT_LIMIT = 1024 * 1024


def _process(command, timeout, max_output):
    chunks = {"stdout": bytearray(), "stderr": bytearray()}
    reason = None
    with subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                          start_new_session=True) as process:
        with selectors.DefaultSelector() as selector:
            selector.register(process.stdout, selectors.EVENT_READ, "stdout")
            selector.register(process.stderr, selectors.EVENT_READ, "stderr")
            deadline = time.monotonic() + timeout
            size = 0
            while selector.get_map():
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    reason = "Tiempo de ejecución excedido."
                    break
                for key, _ in selector.select(remaining):
                    data = os.read(key.fd, 65536)
                    if not data:
                        selector.unregister(key.fileobj)
                        continue
                    allowed = max(0, max_output - size)
                    chunks[key.data].extend(data[:allowed])
                    size += len(data)
                    if size > max_output:
                        reason = "Límite de salida excedido."
                        break
                if reason:
                    break
            if reason:
                os.killpg(process.pid, signal.SIGKILL)
            try:
                process.wait(timeout=max(0.01, deadline - time.monotonic()))
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
                process.wait()
                reason = "Tiempo de ejecución excedido."
    stdout, stderr = (chunks[key].decode("utf-8", errors="replace") for key in ("stdout", "stderr"))
    if reason:
        stderr += ("\n" if stderr else "") + reason
    return {"success": process.returncode == 0 and reason is None,
            "stdout": stdout, "stderr": stderr, "exit_code": process.returncode}


def run_assembly(assembly: str, timeout: float = 5, max_output: int = DEFAULT_OUTPUT_LIMIT) -> dict:
    if timeout <= 0 or max_output <= 0:
        raise ValueError("timeout y max_output deben ser positivos")
    with tempfile.TemporaryDirectory(prefix="oxigen-") as directory:
        root = Path(directory)
        source, obj, executable = root / "program.s", root / "program.o", root / "program"
        source.write_text(assembly, encoding="utf-8")
        stages = [
            ["aarch64-linux-gnu-as", str(source), "-o", str(obj)],
            ["aarch64-linux-gnu-ld", str(obj), "-o", str(executable)],
            ["qemu-aarch64", str(executable)],
        ]
        for index, command in enumerate(stages):
            try:
                result = _process(command, timeout, max_output)
            except OSError as error:
                return {"success": False, "stage": index, "stdout": "", "stderr": str(error)}
            if not result["success"]:
                return {**result, "stage": index}
        return result
