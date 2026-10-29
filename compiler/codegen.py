"""Direct AST-to-AArch64 visitor. Values use x0 internally, f64 as IEEE bits.

Function boundaries follow AAPCS64: integer/pointer arguments x0-x7,
float arguments d0-d7, return x0 or d0. Expression spills are 16-byte aligned.
"""
from pathlib import Path
import struct
from compiler.types import sequence, storage_size, fixed_array, leaf_type

class Generator:
    def __init__(self, analysis):
        self.analysis = analysis
        self.lines = []
        self.constants = {}
        self.counter = 0
        self.loops = []
        self.print_helpers = {}
        self.case_tables = set()

    def emit(self, *lines):
        self.lines.extend(lines)

    def label(self, prefix="branch"):
        self.counter += 1
        return f".Lox_{prefix}_{self.counter}"

    def string(self, text):
        if text not in self.constants:
            self.constants[text] = f".Lox_string_{len(self.constants)}"
        return self.constants[text]

    def address(self, label, register="x0"):
        self.emit(f"adrp {register}, {label}", f"add {register}, {register}, :lo12:{label}")

    def type(self, node):
        return self.analysis.types.get(id(node), "None")

    def local_address(self, symbol):
        self.emit(f"ldr x9, ={symbol.offset}", "sub x9, x29, x9")

    def store(self, symbol, register="x0"):
        self.local_address(symbol)
        self.emit(f"str {register}, [x9]")

    def load(self, symbol):
        self.local_address(symbol)
        self.emit("ldr x0, [x9]")

    def push(self):
        self.emit("str x0, [sp, #-16]!")

    def pop(self, register="x1"):
        self.emit(f"ldr {register}, [sp], #16")

    def generate(self):
        self.emit(".text", ".global _start", "_start:")
        main = self.analysis.functions.get("main")
        if main and id(main.node) not in self.analysis.invalid:
            self.emit("bl ox_fn_main")
        self.emit("mov x0, #0", "mov x8, #93", "svc #0")
        for function in self.analysis.functions.values():
            if id(function.node) not in self.analysis.invalid:
                self.function(function)
        generated = set()
        while set(self.print_helpers) - generated:
            type_ = next(t for t in self.print_helpers if t not in generated)
            generated.add(type_)
            self.array_printer(type_)
        self.emit(".section .rodata")
        self.unicode_tables()
        for text, label in self.constants.items():
            data = text.encode("utf-8")
            self.emit(".balign 8", f"{label}:", f".quad {len(data)}")
            if data:
                self.emit(".byte " + ",".join(str(byte) for byte in data))
        runtime = Path(__file__).with_name("runtime") / "aarch64.s"
        collections = Path(__file__).with_name("runtime") / "collections.s"
        strings = Path(__file__).with_name("runtime") / "strings.s"
        return "\n".join(self.lines) + "\n" + runtime.read_text() + "\n" + collections.read_text() + "\n" + strings.read_text()

    def function(self, function):
        self.current = function
        self.return_label = self.label("return")
        frame = (function.slots * 8 + 15) // 16 * 16
        self.emit(f"ox_fn_{function.node.value}:", "stp x29, x30, [sp, #-16]!", "mov x29, sp",
                  f"ldr x9, ={frame}", "sub sp, sp, x9")
        integer, floating = 0, 0
        for node, (_, type_) in zip(function.node.children[:-2], function.parameters):
            symbol = self.analysis.bindings[id(node)]
            if type_ == "f64":
                self.emit(f"fmov x10, d{floating}")
                floating += 1
                self.store(symbol, "x10")
            else:
                self.store(symbol, f"x{integer}")
                integer += 1
        for statement in function.node.children[-1].children:
            self.statement(statement)
        self.default(function.result)
        if function.result == "f64":
            self.emit("fmov d0, x0")
        self.emit(f"{self.return_label}:", "mov sp, x29", "ldp x29, x30, [sp], #16", "ret", ".ltorg")

    def default(self, type_):
        if fixed_array(type_):
            info = sequence(type_)
            self.new_array(info.length, storage_size(info.element))
            self.push()
            self.default(leaf_type(type_))
            self.emit("mov x2, x0", "ldr x0, [sp]", "ldr x0, [x0, #8]",
                      f"ldr x1, ={storage_size(type_) // 8}", "bl ox_fill")
            self.pop("x0")
        elif sequence(type_):
            self.new_array(0, 8)
        elif type_ == "String":
            self.address(self.string(""))
        else:
            self.emit("mov x0, #0")

    def convert(self, actual, expected):
        if actual == "i32" and expected == "f64":
            self.emit("scvtf d0, x0", "fmov x0, d0")

    def statement(self, node):
        if id(node) in self.analysis.invalid:
            return
        previous = getattr(self, "failure_label", None)
        self.failure_label = self.label("recover")
        offset = self.analysis.recoveries[id(node)]
        self.emit("mov x10, sp", f"ldr x9, ={offset}", "sub x9, x29, x9", "str x10, [x9]")
        self.statement_body(node)
        self.emit(f"{self.failure_label}:", f"ldr x9, ={offset}", "sub x9, x29, x9", "ldr x9, [x9]", "mov sp, x9")
        self.failure_label = previous

    def statement_body(self, node):
        if id(node) in self.analysis.invalid:
            return
        kind = node.kind
        if kind == "block":
            for child in node.children:
                self.statement(child)
        elif kind == "declaration":
            symbol = self.analysis.bindings.get(id(node))
            if not symbol:
                return
            initializer = next((n for n in node.children if n.kind not in {"type", "array_type"}), None)
            if initializer and id(initializer) not in self.analysis.invalid:
                if self.can_fail(initializer):
                    self.default(symbol.type)
                    self.store(symbol)
                self.expression(initializer)
                self.convert(self.type(initializer), symbol.type)
                self.clone_array(symbol.type, initializer)
            else:
                self.default(symbol.type)
            self.store(symbol)
        elif kind == "assignment":
            left, right = node.children
            expected = self.type(left)
            if left.kind == "index":
                self.index_address(left)
                self.push()
            if node.value == "=":
                self.expression(right)
                self.convert(self.type(right), expected)
                if left.kind == "identifier":
                    self.clone_array(expected, right)
            else:
                if left.kind == "identifier":
                    self.expression(left)
                else:
                    self.emit("ldr x0, [x0]")
                self.push()
                self.expression(right)
                self.pop()
                self.binary(node.value[0], expected, self.type(right))
            if left.kind == "identifier":
                self.store(self.analysis.bindings[id(left)])
            else:
                self.pop("x1")
                self.copy_to_address(expected)
        elif kind == "if":
            otherwise, end = self.label("else"), self.label("endif")
            self.expression(node.children[0])
            self.emit(f"cbz x0, {otherwise}")
            self.statement(node.children[1])
            self.emit(f"b {end}", f"{otherwise}:")
            if len(node.children) == 3:
                self.statement(node.children[2])
            self.emit(f"{end}:")
        elif kind in {"while", "loop"}:
            begin, end = self.label("loop"), self.label("endloop")
            self.loops.append((node.value if kind == "loop" else None, begin, end))
            self.emit(f"{begin}:")
            if kind == "while":
                extra = self.label("extra_loop")
                self.expression(node.children[0])
                self.emit(f"cbz x0, {extra}")
            self.statement(node.children[-1])
            if kind == "while":
                self.emit(f"b {begin}")
                self.loops.pop()
                self.loops.append((None, end, end))
                self.emit(f"{extra}:")
                self.statement(node.children[-1])
                self.emit(f"b {end}")
            else:
                self.emit(f"b {begin}")
            self.loops.pop()
            self.emit(f"{end}:")
        elif kind in {"break", "continue"}:
            loop = next(loop for loop in reversed(self.loops) if node.value is None or loop[0] == node.value)
            self.emit(f"b {loop[2] if kind == 'break' else loop[1]}")
        elif kind == "return":
            if node.children:
                self.expression(node.children[0])
                self.convert(self.type(node.children[0]), self.current.result)
                self.clone_array(self.current.result, node.children[0])
                if self.current.result == "f64":
                    self.emit("fmov d0, x0")
            self.emit(f"b {self.return_label}")
        elif kind == "match":
            # Store the scrutinee in a frame-local temporary, so break/continue do not leak spills.
            self.expression(node.children[0])
            self.push()
            # The match spill is released before entering any arm body.
            end = self.label("endmatch")
            bodies = []
            for arm in node.children[1:]:
                if id(arm) in self.analysis.invalid:
                    continue
                pattern, body = arm.children
                label = self.label("arm")
                bodies.append((label, body))
                if pattern.kind == "identifier" and pattern.value == "_":
                    self.emit(f"b {label}")
                    break
                self.expression(pattern)
                self.emit("ldr x1, [sp]")
                self.binary("==", self.type(node.children[0]), self.type(pattern))
                self.emit(f"cbnz x0, {label}")
            self.emit("add sp, sp, #16", f"b {end}")
            for label, body in bodies:
                self.emit(f"{label}:", "add sp, sp, #16")
                self.statement(body)
                self.emit(f"b {end}")
            self.emit(f"{end}:")
        else:
            self.expression(node)

    def expression(self, node):
        if id(node) in self.analysis.invalid:
            self.emit("mov x0, #0")
            return
        kind = node.kind
        if kind == "literal":
            value = node.value["value"]
            type_ = self.type(node)
            if type_ == "String":
                self.address(self.string(value))
            elif type_ == "f64":
                bits = struct.unpack("<Q", struct.pack("<d", value))[0]
                self.emit(f"ldr x0, =0x{bits:016x}")
            elif type_ == "char":
                self.emit(f"ldr x0, ={ord(value) if value else 0}")
            else:
                self.emit(f"ldr x0, ={int(value or 0)}")
        elif kind == "identifier":
            symbol = self.analysis.bindings.get(id(node))
            if symbol:
                self.load(symbol)
            else:
                self.emit("mov x0, #0")
        elif kind == "unary":
            self.expression(node.children[0])
            if node.value == "&":
                pass
            elif node.value == "!":
                self.emit("eor x0, x0, #1")
            elif self.type(node) == "f64":
                self.emit("fmov d0, x0", "fneg d0, d0", "fmov x0, d0")
            else:
                self.emit("neg w0, w0", "sxtw x0, w0")
        elif kind == "binary":
            left, right = node.children
            self.expression(left)
            if node.value in {"&&", "||"}:
                end = self.label("short_circuit")
                self.emit(f"{'cbz' if node.value == '&&' else 'cbnz'} x0, {end}")
                self.expression(right)
                self.emit(f"{end}:")
            else:
                self.push()
                self.expression(right)
                self.pop()
                self.binary(node.value, self.type(left), self.type(right))
        elif kind == "macro_call":
            pieces = self.analysis.formats.get(id(node), [])
            arguments = [piece for piece in pieces if not isinstance(piece, str)]
            # Evaluate every argument before writing any part of the format string.
            for argument in arguments:
                self.expression(argument)
                self.push()
            index = 0
            for piece in pieces:
                if isinstance(piece, str):
                    if piece:
                        self.address(self.string(piece))
                        self.emit("bl ox_write")
                else:
                    offset = (len(arguments) - 1 - index) * 16
                    self.emit(f"ldr x9, ={offset}", "add x9, sp, x9", "ldr x0, [x9]")
                    self.print_value(self.type(piece))
                    index += 1
            if arguments:
                self.emit(f"ldr x9, ={len(arguments) * 16}", "add sp, sp, x9")
            self.address(self.string("\n"))
            self.emit("bl ox_write", "mov x0, #0")
        elif kind == "call":
            callee, *arguments = node.children
            if callee.value == "String::new":
                self.address(self.string(""))
                self.emit("bl ox_clone")
                return
            if callee.value == "typeof":
                self.expression(arguments[0])
                self.address(self.string(self.type(arguments[0])))
                return
            if callee.value == "random":
                for argument in arguments:
                    self.expression(argument)
                    self.push()
                self.pop("x1")
                self.pop("x0")
                okay = self.label("random_range")
                self.emit("cmp x0, x1", f"b.le {okay}")
                self.runtime_error(node, "El mínimo de random no puede ser mayor que el máximo.")
                self.emit(f"{okay}:", "bl ox_random")
                return
            if callee.value == "String::from":
                self.expression(arguments[0])
                self.emit("bl ox_clone")
                return
            function = self.analysis.functions[callee.value]
            locations = []
            integer, floating = 0, 0
            for argument, (_, type_) in zip(arguments, function.parameters):
                self.expression(argument)
                self.convert(self.type(argument), type_)
                self.clone_array(type_, argument)
                self.push()
                if type_ == "f64":
                    locations.append(f"d{floating}")
                    floating += 1
                else:
                    locations.append(f"x{integer}")
                    integer += 1
            for location in reversed(locations):
                self.pop("x9")
                self.emit(f"fmov {location}, x9" if location.startswith("d") else f"mov {location}, x9")
            self.emit(f"bl ox_fn_{callee.value}")
            if function.result == "f64":
                self.emit("fmov x0, d0")
        elif kind in {"array", "array_repeat"}:
            info = sequence(self.type(node))
            stride = storage_size(info.element)
            self.new_array(info.length, stride)
            self.push()
            values = node.children if kind == "array" else node.children[:1]
            for index, value in enumerate(values):
                self.expression(value)
                self.convert(self.type(value), info.element)
                if kind == "array_repeat":
                    self.push()
                    self.emit("ldr x0, [sp, #16]", "ldr x1, [x0, #8]",
                              "ldr x0, [sp]", f"ldr x2, ={info.length}", f"ldr x3, ={stride}")
                    if fixed_array(info.element):
                        self.emit("ldr x0, [x0, #8]", "bl ox_repeat_block")
                    else:
                        self.emit("bl ox_repeat_slot")
                    self.emit("add sp, sp, #16")
                else:
                    self.emit("ldr x1, [sp]", "ldr x1, [x1, #8]", f"ldr x9, ={index * stride}", "add x1, x1, x9")
                    self.copy_to_address(info.element)
            self.pop("x0")
        elif kind == "index":
            self.index_address(node)
            if fixed_array(self.type(node)):
                self.view_array(self.type(node))
            else:
                self.emit("ldr x0, [x0]")
        elif kind == "slice":
            base, start, end = node.children
            info = sequence(self.type(base))
            for child in node.children:
                self.expression(child)
                self.push()
            self.pop("x2")
            self.pop("x1")
            self.pop("x0")
            okay, bad = self.label("slice_ok"), self.label("slice_bad")
            self.emit("cmp x1, #0", f"b.lt {bad}", "cmp x1, x2", f"b.gt {bad}",
                      "ldr x9, [x0]", "cmp x2, x9", f"b.ls {okay}", f"{bad}:")
            self.runtime_error(node, "Rango fuera de los límites del arreglo.")
            self.emit(f"{okay}:", "ldr x0, [x0, #8]", f"ldr x9, ={storage_size(info.element)}",
                      "madd x0, x1, x9, x0", "sub x1, x2, x1", "bl ox_array_view")
        elif kind == "method_call":
            self.method(node)
        else:
            self.emit("mov x0, #0")

    def print_value(self, type_):
        if sequence(type_):
            if type_ not in self.print_helpers:
                self.print_helpers[type_] = f"ox_print_array_{len(self.print_helpers)}"
            self.emit(f"bl {self.print_helpers[type_]}")
        elif type_ == "String":
            self.emit("bl ox_write")
        elif type_ == "char":
            self.emit("bl ox_print_char")
        elif type_ == "f64":
            self.emit("bl ox_print_float")
        elif type_ == "bool":
            no, end = self.label("false"), self.label("printed_bool")
            self.emit(f"cbz x0, {no}")
            self.address(self.string("true"))
            self.emit(f"b {end}", f"{no}:")
            self.address(self.string("false"))
            self.emit(f"{end}:", "bl ox_write")
        elif type_ == "None":
            self.address(self.string("None"))
            self.emit("bl ox_write")
        else:
            self.emit("bl ox_print_i32")

    def binary(self, operator, left, right):
        # x1 = left operand, x0 = right operand; result x0.
        relational = operator in {"==", "!=", "<", "<=", ">", ">="}
        condition = {"==": "eq", "!=": "ne", "<": "lt", "<=": "le", ">": "gt", ">=": "ge"}.get(operator)
        if left == right == "String":
            self.emit("mov x9, x0", "mov x0, x1", "mov x1, x9")
            if operator == "+":
                self.emit("bl ox_concat")
            else:
                self.emit("bl ox_compare_strings", "cmp x0, #0", f"cset x0, {condition}")
        elif operator == "*" and "String" in {left, right}:
            if right == "String":
                pass  # x0 is the string and x1 is the count.
            else:
                self.emit("mov x9, x0", "mov x0, x1", "mov x1, x9")
            self.emit("bl ox_repeat")
        elif "f64" in {left, right}:
            self.emit("fmov d0, x1" if left == "f64" else "scvtf d0, x1",
                      "fmov d1, x0" if right == "f64" else "scvtf d1, x0")
            if relational:
                self.emit("fcmp d0, d1")
                # Ordered less/less-equal exclude NaN (AArch64 unordered sets V and C).
                condition = {"<": "mi", "<=": "ls"}.get(operator, condition)
                self.emit(f"cset x0, {condition}")
            else:
                if operator in {"/", "%"}:
                    self.emit("fcmp d1, #0.0", "b.eq ox_div_zero")
                if operator == "%":
                    self.emit("fdiv d2, d0, d1", "frintz d2, d2", "fmsub d0, d2, d1, d0")
                else:
                    instruction = {"+": "fadd", "-": "fsub", "*": "fmul", "/": "fdiv"}[operator]
                    self.emit(f"{instruction} d0, d0, d1")
                self.emit("fmov x0, d0")
        elif relational:
            self.emit("cmp x1, x0", f"cset x0, {condition}")
        else:
            if operator in {"/", "%"}:
                self.emit("cbz x0, ox_div_zero")
            if operator == "%":
                self.emit("sdiv w9, w1, w0", "msub w0, w9, w0, w1")
            elif operator == "/":
                self.emit("sdiv w0, w1, w0")
            else:
                self.emit(f"{ {'+': 'add', '-': 'sub', '*': 'mul'}[operator]} w0, w1, w0")
            self.emit("sxtw x0, w0")

    def can_fail(self, node):
        if node.kind in {"index", "slice"}:
            return True
        if node.kind == "call" and node.children[0].kind == "identifier" and node.children[0].value == "random":
            return True
        return any(self.can_fail(child) for child in node.children)

    def new_array(self, length, stride):
        self.emit(f"ldr x0, ={length}", f"ldr x1, ={stride}", "bl ox_array_new")

    def clone_array(self, type_, node=None):
        info = sequence(type_)
        if info and not info.borrowed and (node is None or node.kind in {"identifier", "index"}):
            self.emit(f"ldr x1, ={storage_size(sequence(type_).element)}", "bl ox_array_clone")

    def copy_to_address(self, type_):
        # x0 is a value/descriptor and x1 is a destination inside a flat array.
        if fixed_array(type_):
            self.emit("ldr x0, [x0, #8]", f"ldr x2, ={storage_size(type_)}", "bl ox_copy")
        else:
            self.emit("str x0, [x1]")

    def view_array(self, type_):
        self.emit(f"ldr x1, ={sequence(type_).length}", "bl ox_array_view")

    def runtime_error(self, node, message):
        p = node.position
        self.address(self.string(f"OXERR\t{p.line}\t{p.column}\t{message}\n"))
        self.emit("bl ox_write_error", f"b {self.failure_label}")

    def index_address(self, node):
        base, index = node.children
        self.expression(base)
        self.push()
        self.expression(index)
        self.pop("x1")
        okay = self.label("index_ok")
        self.emit("ldr x9, [x1]", "cmp x0, x9", f"b.lo {okay}")
        self.runtime_error(node, "Índice fuera de los límites del arreglo.")
        self.emit(f"{okay}:", "ldr x1, [x1, #8]", f"ldr x9, ={storage_size(self.type(node))}",
                  "madd x0, x0, x9, x1")

    def method(self, node):
        receiver, *arguments = node.children
        type_ = self.type(receiver)
        info = sequence(type_)
        name = node.value
        for child in node.children:
            self.expression(child)
            if name == "contains" and child is not receiver and info:
                self.convert(self.type(child), info.element)
            self.push()
        for index in reversed(range(len(node.children))):
            self.pop(f"x{index}")
        if name == "len":
            self.emit("ldr x0, [x0]")
        elif name == "contains":
            if type_ == "String":
                self.emit("bl ox_string_contains")
            else:
                self.array_contains(info.element)
        elif name == "reverse":
            self.emit(f"ldr x1, ={storage_size(info.element)}", "bl ox_array_reverse", "mov x0, #0")
        elif name == "replace":
            self.emit("bl ox_string_replace")
        elif name == "split":
            self.emit("bl ox_string_split")
        elif name in {"to_uppercase", "to_lowercase"}:
            which = "upper" if name == "to_uppercase" else "lower"
            self.case_tables.add(which)
            self.address(f"ox_unicode_{which}", "x1")
            self.emit(f"ldr x2, =ox_unicode_{which}_length", "bl ox_string_case")

    def array_contains(self, element):
        begin, found, end = self.label("contains"), self.label("found"), self.label("contains_end")
        self.emit("stp x0, x1, [sp, #-32]!", "str xzr, [sp, #16]", f"{begin}:",
                  "ldr x9, [sp]", "ldr x10, [sp, #16]", "ldr x11, [x9]", "cmp x10, x11", f"b.hs {end}",
                  "ldr x9, [x9, #8]", "ldr x1, [x9, x10, lsl #3]", "ldr x0, [sp, #8]")
        self.binary("==", element, element)
        self.emit(f"cbnz x0, {found}", "ldr x10, [sp, #16]", "add x10, x10, #1", "str x10, [sp, #16]", f"b {begin}",
                  f"{end}:", "mov x0, #0", f"{found}:", "add sp, sp, #32")

    def array_printer(self, type_):
        info = sequence(type_)
        begin, end = self.label("print_items"), self.label("print_items_done")
        self.emit(f"{self.print_helpers[type_]}:", "stp x29, x30, [sp, #-48]!", "str x0, [sp, #16]", "str xzr, [sp, #24]",
                  "mov x0, #91", "bl ox_print_char", f"{begin}:", "ldr x9, [sp, #16]", "ldr x10, [sp, #24]", "ldr x11, [x9]",
                  "cmp x10, x11", f"b.hs {end}")
        first = self.label("first_item")
        self.emit(f"cbz x10, {first}")
        self.address(self.string(", "))
        self.emit("bl ox_write", f"{first}:", "ldr x9, [sp, #16]", "ldr x9, [x9, #8]", "ldr x10, [sp, #24]",
                  f"ldr x11, ={storage_size(info.element)}", "madd x0, x10, x11, x9")
        if fixed_array(info.element):
            self.view_array(info.element)
        else:
            self.emit("ldr x0, [x0]")
        if info.element == "String":
            self.emit("bl ox_debug_string")
        elif info.element == "char":
            self.emit("bl ox_debug_char")
        else:
            self.print_value(info.element)
        self.emit("ldr x10, [sp, #24]", "add x10, x10, #1", "str x10, [sp, #24]", f"b {begin}", f"{end}:",
                  "mov x0, #93", "bl ox_print_char", "ldp x29, x30, [sp], #48", "ret", ".ltorg")

    def unicode_tables(self):
        from compiler.unicode_data import case_mapping
        for which in sorted(self.case_tables):
            mappings = case_mapping(which)
            self.emit(".balign 8", f"ox_unicode_{which}:")
            for character, converted in mappings:
                self.emit(f".quad {character}, {self.string(converted)}")
            self.emit(f".equ ox_unicode_{which}_length, {len(mappings)}")
