"""Static analysis, scopes and source bindings for the ARM64 backend.

Expression types and symbol bindings belong to each compilation, never to global state.
Invalid expressions evaluate to None; invalid statements are omitted by code generation.
"""
from dataclasses import dataclass, field
import re
from compiler.model import Diagnostic
from compiler.types import array_type, slice_type, sequence, storage_size, fixed_array

PRIMITIVES = {"i32", "f64", "bool", "char", "String", "None", "unit"}
NUMERIC = {"i32", "f64"}

@dataclass
class Symbol:
    name: str
    type: str
    mutable: bool
    scope: str
    line: int
    offset: int
    category: str = "Variable"
    value: str = "—"

@dataclass
class Function:
    node: object
    parameters: list
    result: str
    slots: int = 0

@dataclass
class Analysis:
    functions: dict = field(default_factory=dict)
    types: dict = field(default_factory=dict)
    bindings: dict = field(default_factory=dict)
    symbols: list = field(default_factory=list)
    diagnostics: list = field(default_factory=list)
    invalid: set = field(default_factory=set)
    formats: dict = field(default_factory=dict)
    poisoned: set = field(default_factory=set)
    recoveries: dict = field(default_factory=dict)

class Analyzer:
    def __init__(self, source):
        self.source = source.splitlines()
        self.result = Analysis()
        self.scopes = []
        self.loops = []
        self.current = None
        self.scope_counter = 0

    def error(self, node, message):
        p = node.position
        self.result.diagnostics.append(Diagnostic("Semántico", message, p,
            self.source[p.line - 1] if p.line <= len(self.source) else ""))

    def type_node(self, node):
        if node.kind == "array_type":
            element = self.type_node(node.children[0])
            result = array_type(element, node.value)
            if node.value > 2147483647 or storage_size(result) > 1048544:
                self.reject(node, "El tamaño del arreglo excede la capacidad del heap.")
                return "None"
            return result
        return node.value

    @staticmethod
    def constant_integer(node):
        if node.kind == "literal" and node.value["type"] == "INTEGER":
            return node.value["value"]
        if node.kind == "unary" and node.value == "-":
            value = Analyzer.constant_integer(node.children[0])
            return -value if value is not None else None
        return None

    def poison(self, node, message=None):
        if message:
            self.reject(node, message)
        else:
            self.result.invalid.add(id(node))
        self.result.poisoned.add(id(node))

    def mutable_target(self, node, elements=False):
        current = node
        while current.kind in {"index", "slice", "unary"} and current.children:
            info = sequence(self.result.types.get(id(current), "None"))
            if info and info.borrowed:
                return False
            current = current.children[0]
        symbol = self.result.bindings.get(id(current)) if current.kind == "identifier" else None
        if symbol is None or not symbol.mutable or ((node.kind != "identifier" or elements) and sequence(symbol.type) and sequence(symbol.type).borrowed):
            return False
        return True

    def lookup(self, node):
        for scope in reversed(self.scopes):
            if node.value in scope:
                symbol = scope[node.value]
                self.result.bindings[id(node)] = symbol
                return symbol
        self.error(node, f"La variable {node.value!r} no ha sido declarada.")
        return None

    def define(self, node, name, type_, mutable):
        self.current.slots += 1
        symbol = Symbol(name, type_, mutable, self.scopes[-1][None], node.position.line,
                        self.current.slots * 8)
        symbol.category = "Parámetro" if node.kind == "parameter" else "Variable"
        if node.kind == "declaration":
            initial = next((n for n in node.children if n.kind not in {"type", "array_type"}), None)
            if initial and initial.kind == "literal":
                value = initial.value["value"]
                symbol.value = repr(value) if isinstance(value, str) else str(value).lower() if isinstance(value, bool) else str(value)
        self.scopes[-1][name] = symbol
        self.result.symbols.append(symbol)
        self.result.bindings[id(node)] = symbol
        return symbol

    def analyze(self, tree):
        for node in tree.children:
            name = node.value
            if name in self.result.functions:
                self.error(node, f"La función {name!r} ya fue declarada.")
                self.result.invalid.add(id(node))
                continue
            params = node.children[:-2]
            signature = [(p.value, self.type_node(p.children[0])) for p in params]
            result = self.type_node(node.children[-2])
            # Stack arguments beyond the eight registers in each AAPCS class are deferred.
            if sum(t == "f64" for _, t in signature) > 8 or sum(t != "f64" for _, t in signature) > 8:
                self.error(node, "Se admiten hasta ocho parámetros por clase de registros (enteros y flotantes).")
                self.result.invalid.add(id(node))
            self.result.functions[name] = Function(node, signature, result)
        main = self.result.functions.get("main")
        if not main:
            self.error(tree, "Se requiere una función main.")
        elif main.parameters or main.result != "unit":
            self.error(main.node, "main debe declararse sin parámetros ni retorno.")
            self.result.invalid.add(id(main.node))
        for name, function in self.result.functions.items():
            self.current = function
            self.scopes = [{None: name}]
            seen = set()
            for node, (param, type_) in zip(function.node.children[:-2], function.parameters):
                if param in seen:
                    self.error(node, f"El parámetro {param!r} está duplicado.")
                seen.add(param)
                self.define(node, param, type_, False)
            self.block(function.node.children[-1], nested=False)
            if function.result != "unit" and not self.returns(function.node.children[-1]):
                self.error(function.node, f"La función {name!r} puede terminar sin retornar {function.result}.")
        for name, function in self.result.functions.items():
            self.result.symbols.append(Symbol(name, function.result, False, "Global", function.node.position.line, 0, "Función"))
        return self.result

    def returns(self, node):
        if node.kind == "return":
            return True
        if node.kind == "block":
            return any(self.returns(child) for child in node.children)
        return node.kind == "if" and len(node.children) == 3 and all(self.returns(n) for n in node.children[1:])

    def block(self, node, nested=True):
        if nested:
            self.scope_counter += 1
            self.scopes.append({None: f"{self.current.node.value}/bloque{self.scope_counter}"})
        for child in node.children:
            self.statement(child)
        if nested:
            self.scopes.pop()

    def reject(self, node, message):
        self.error(node, message)
        self.result.invalid.add(id(node))

    def statement(self, node):
        self.current.slots += 1
        self.result.recoveries[id(node)] = self.current.slots * 8
        kind = node.kind
        if kind == "block":
            self.block(node)
        elif kind == "declaration":
            annotation = next((n for n in node.children if n.kind in {"type", "array_type"}), None)
            initializer = next((n for n in node.children if n is not annotation), None)
            declared = self.type_node(annotation) if annotation else None
            actual = self.expression(initializer, declared) if initializer else None
            expected = declared if annotation else actual
            if expected is None or expected == "unit":
                self.reject(node, "La declaración requiere un tipo o un valor inicial válido.")
                return
            if actual and not self.compatible(expected, actual):
                self.error(initializer, f"No es posible asignar un valor de tipo {actual} a una variable de tipo {expected}.")
                self.result.invalid.add(id(initializer))
            self.define(node, node.value["name"], expected, node.value["mutable"])
        elif kind == "assignment":
            left, right = node.children
            expected = self.expression(left)
            actual = self.expression(right, expected)
            if left.kind not in {"identifier", "index"}:
                self.reject(node, "El destino debe ser una variable o un elemento de arreglo.")
            elif id(left) in self.result.poisoned:
                self.result.invalid.add(id(node))
            elif not self.mutable_target(left):
                self.reject(node, "No es posible modificar el destino porque fue declarado como inmutable o es un slice de solo lectura.")
            if node.value != "=":
                actual = self.binary_type(node, expected, actual, node.value[0])
            if not self.compatible(expected, actual):
                self.reject(node, f"No es posible asignar un valor de tipo {actual} a una variable de tipo {expected}.")
        elif kind in {"if", "while"}:
            if self.expression(node.children[0]) != "bool":
                self.reject(node, "La condición debe ser de tipo bool.")
            if kind == "while":
                self.loops.append(None)
            for branch in node.children[1:]:
                self.statement(branch)
            if kind == "while":
                self.loops.pop()
        elif kind == "loop":
            if node.value is not None and node.value in self.loops:
                self.reject(node, f"La etiqueta {node.value!r} ya está activa.")
            self.loops.append(node.value)
            self.statement(node.children[0])
            self.loops.pop()
        elif kind in {"break", "continue"}:
            if not self.loops or (node.value is not None and node.value not in self.loops):
                self.reject(node, "Transferencia fuera de un bucle o etiqueta desconocida.")
        elif kind == "return":
            actual = self.expression(node.children[0], self.current.result) if node.children else "unit"
            if not self.compatible(self.current.result, actual):
                self.reject(node, f"Se esperaba un retorno {self.current.result}, se obtuvo {actual}.")
        elif kind == "match":
            matched = self.expression(node.children[0])
            for arm in node.children[1:]:
                pattern, body = arm.children
                if not (pattern.kind == "identifier" and pattern.value == "_"):
                    type_ = self.expression(pattern)
                    if self.binary_type(arm, matched, type_, "==") == "None":
                        self.result.invalid.add(id(arm))
                self.statement(body)
        else:
            self.expression(node)

    @staticmethod
    def compatible(expected, actual):
        return expected == actual or (expected == "f64" and actual == "i32")

    def binary_type(self, node, left, right, operator):
        if operator in {"&&", "||"}:
            if left == right == "bool":
                return "bool"
        elif operator in {"==", "!=", "<", "<=", ">", ">="}:
            if (left == right and left not in {"unit", "None"} and not sequence(left)) or {left, right} <= NUMERIC or {left, right} == {"i32", "char"}:
                return "bool"
        elif {left, right} <= NUMERIC:
            return "f64" if "f64" in {left, right} else "i32"
        elif operator == "+" and left == right == "String":
            return "String"
        elif operator == "*" and (left, right) in {("i32", "String"), ("String", "i32")}:
            return "String"
        self.error(node, f"No es posible aplicar el operador {operator!r} entre los tipos {left} y {right}.")
        self.result.invalid.add(id(node))
        return "None"

    def expression(self, node, expected=None):
        kind = node.kind
        type_ = "None"
        if kind == "literal":
            type_ = {"INTEGER": "i32", "FLOAT": "f64", "TRUE": "bool", "FALSE": "bool", "CHAR": "char", "STRING": "String", "NONE": "None"}[node.value["type"]]
            if type_ == "i32" and not -2147483648 <= node.value["value"] <= 2147483647:
                self.reject(node, "Literal fuera del rango i32.")
                type_ = "None"
        elif kind == "identifier":
            symbol = self.lookup(node)
            type_ = symbol.type if symbol else "None"
            if symbol is None:
                self.poison(node)
        elif kind == "binary":
            left, right = [self.expression(n) for n in node.children]
            type_ = self.binary_type(node, left, right, node.value)
        elif kind == "unary":
            child = node.children[0]
            if node.value == "-" and child.kind == "literal" and child.value == {"type": "INTEGER", "value": 2147483648}:
                self.result.types[id(child)] = "i32"
                type_ = "i32"
            else:
                operand = self.expression(child)
                if node.value == "!" and operand == "bool":
                    type_ = "bool"
                elif node.value == "&" and child.kind == "slice" and sequence(operand):
                    type_ = operand
                elif node.value == "-" and operand in NUMERIC:
                    type_ = operand
                else:
                    self.reject(node, f"Operador unario {node.value!r} incompatible con {operand}.")
        elif kind in {"call", "macro_call"}:
            callee, *arguments = node.children
            name = callee.value if callee.kind == "identifier" else ""
            signature = self.result.functions[name].parameters if name in self.result.functions else []
            types = [self.expression(n, signature[i][1] if i < len(signature) else None) for i, n in enumerate(arguments)]
            if kind == "macro_call" and name == "println":
                self.print_format(node, arguments, types)
                type_ = "unit"
            elif kind == "call" and name == "String::new":
                if not types:
                    type_ = "String"
                else:
                    self.poison(node, "String::new no recibe argumentos.")
            elif kind == "call" and name == "typeof":
                if len(types) == 1 and types[0] != "unit":
                    type_ = "String"
                else:
                    self.poison(node, "typeof requiere exactamente un valor.")
            elif kind == "call" and name == "random":
                if types != ["i32", "i32"]:
                    self.poison(node, "random requiere dos argumentos i32.")
                elif all(self.constant_integer(a) is not None for a in arguments) and self.constant_integer(arguments[0]) > self.constant_integer(arguments[1]):
                    self.poison(node, "El mínimo de random no puede ser mayor que el máximo.")
                else:
                    type_ = "i32"
            elif kind == "call" and name == "String::from":
                if types == ["String"]:
                    type_ = "String"
                else:
                    self.reject(node, "String::from requiere exactamente una cadena.")
            elif kind == "call" and name in self.result.functions:
                function = self.result.functions[name]
                if id(function.node) in self.result.invalid:
                    self.reject(node, f"La función {name!r} no tiene una firma válida.")
                elif len(types) != len(function.parameters):
                    self.reject(node, f"La función {name!r} esperaba {len(function.parameters)} argumentos, pero recibió {len(types)}.")
                elif any(not self.compatible(t, a) for (_, t), a in zip(function.parameters, types)):
                    self.reject(node, f"Tipos de argumentos incompatibles en {name!r}.")
                else:
                    type_ = function.result
            else:
                self.reject(node, f"La función {name!r} no ha sido declarada.")
        elif kind in {"array", "array_repeat"}:
            context = sequence(expected) if expected else None
            if kind == "array_repeat":
                element, count = node.children
                count_type = self.expression(count)
                length = self.constant_integer(count)
                if count_type != "i32" or length is None or length < 0:
                    self.poison(node, "La longitud de repetición debe ser una constante i32 no negativa.")
                    length = 0
                values = [element]
            else:
                values, length = node.children, len(node.children)
            types = [self.expression(n, context.element if context else None) for n in values]
            element_type = context.element if context else (types[0] if types else "None")
            if not context and types and set(types) <= NUMERIC:
                element_type = "f64" if "f64" in types else "i32"
            if not types and not context:
                self.poison(node, "Un arreglo vacío requiere una anotación de tipo.")
            elif element_type == "unit" or any(not self.compatible(element_type, t) for t in types):
                self.poison(node, "Todos los elementos del arreglo deben tener un tipo compatible y la misma forma.")
            type_ = array_type(element_type, length)
            if storage_size(type_) > 1048544:
                self.poison(node, "El tamaño del arreglo excede la capacidad del heap.")
                type_ = "None"
        elif kind in {"index", "slice"}:
            base, *indices = node.children
            base_type = self.expression(base)
            info = sequence(base_type)
            index_types = [self.expression(index) for index in indices]
            constants = [self.constant_integer(index) for index in indices]
            if not info or any(t != "i32" for t in index_types):
                self.poison(node, "El acceso requiere un arreglo y un índice de tipo i32.")
            elif kind == "index":
                if constants[0] is not None and (constants[0] < 0 or info.length is not None and constants[0] >= info.length):
                    self.poison(node, "Índice fuera de los límites del arreglo.")
                else:
                    type_ = info.element
            elif (constants[0] is not None and constants[0] < 0 or
                  all(c is not None for c in constants) and constants[0] > constants[1] or
                  constants[1] is not None and info.length is not None and constants[1] > info.length):
                self.poison(node, "Rango fuera de los límites del arreglo.")
            else:
                type_ = slice_type(info.element)
        elif kind == "method_call":
            receiver, *arguments = node.children
            receiver_type = self.expression(receiver)
            types = [self.expression(n) for n in arguments]
            info = sequence(receiver_type)
            name = node.value
            if name == "len" and not types and (receiver_type == "String" or info):
                type_ = "i32"
            elif name == "contains" and ((receiver_type == "String" and types == ["String"]) or
                    (info and len(types) == 1 and not sequence(info.element) and self.compatible(info.element, types[0]))):
                type_ = "bool"
            elif name in {"to_uppercase", "to_lowercase"} and receiver_type == "String" and not types:
                type_ = "String"
            elif name == "replace" and receiver_type == "String" and types == ["String", "String"]:
                type_ = "String"
            elif name == "split" and receiver_type == "String" and types == ["String"]:
                type_ = "[String]"
            elif name == "reverse" and info and not types:
                if not self.mutable_target(receiver, elements=True):
                    self.poison(node, "reverse requiere un arreglo mutable; los slices son de solo lectura.")
                else:
                    type_ = "unit"
            else:
                self.poison(node, f"El método {name!r} no admite estos argumentos para {receiver_type}.")
        else:
            self.poison(node, f"La construcción {kind!r} aún no está implementada en el generador ARM64.")
        if kind in {"call", "macro_call", "method_call"} and id(node) in self.result.invalid:
            self.result.poisoned.add(id(node))
        if any(id(child) in self.result.poisoned for child in node.children):
            self.poison(node)
        self.result.types[id(node)] = type_
        return type_

    def print_format(self, node, arguments, types):
        if any(id(argument) in self.result.poisoned for argument in arguments):
            self.poison(node)
            return
        if not arguments:
            self.result.formats[id(node)] = [""]
            return
        if len(arguments) == 1:
            self.result.formats[id(node)] = [arguments[0]]
            if types[0] == "unit":
                self.reject(node, "No se puede imprimir un valor sin retorno.")
            return
        template = arguments[0]
        if template.kind != "literal" or types[0] != "String":
            self.reject(node, "El formato de println! debe ser una cadena literal.")
            return
        pieces = re.split(r"(\{\}|\{:\?\})", template.value["value"])
        slots = [i for i, s in enumerate(pieces) if s in {"{}", "{:?}"}]
        if len(slots) != len(arguments) - 1 or "unit" in types[1:]:
            self.reject(node, "La cantidad o el tipo de argumentos no corresponde al formato de println!.")
            return
        for index, argument in zip(slots, arguments[1:]):
            pieces[index] = argument
        self.result.formats[id(node)] = pieces


def analyze(tree, source):
    return Analyzer(source).analyze(tree)
