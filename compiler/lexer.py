"""PLY scanner. Each instance owns its source and diagnostic collection."""
import ast
from ply import lex
from compiler.model import Diagnostic, SourcePosition

class Lexer:
    reserved = {word: word.upper() for word in (
        "fn let mut if else while loop match break continue return true false None i32 f64 bool char String"
    ).split()}
    reserved.update({"char": "CHAR_TYPE", "String": "STRING_TYPE"})
    tokens = tuple(reserved.values()) + (
        "ID", "INTEGER", "FLOAT", "STRING", "CHAR", "LABEL", "ARROW", "FATARROW",
        "EQ", "NE", "LE", "GE", "AND", "OR", "ADDASSIGN", "SUBASSIGN", "MULASSIGN",
        "DIVASSIGN", "MODASSIGN", "PATH", "RANGE",
    )
    literals = "+-*/%!=<>(){}[];:,.&|"
    t_ARROW = r"->"
    t_FATARROW = r"=>"
    t_EQ = r"=="
    t_NE = r"!="
    t_LE = r"<="
    t_GE = r">="
    t_AND = r"&&"
    t_OR = r"\|\|"
    t_ADDASSIGN = r"\+="
    t_SUBASSIGN = r"-="
    t_MULASSIGN = r"\*="
    t_DIVASSIGN = r"/="
    t_MODASSIGN = r"%="
    t_PATH = r"::"
    t_RANGE = r"\.\."
    t_ignore = " \t\r"

    def __init__(self, source=""):
        self.source = source
        self.diagnostics = []
        self.lexer = lex.lex(module=self)
        self.lexer.input(source)

    def position(self, offset):
        return SourcePosition(self.source.count("\n", 0, offset) + 1,
                              offset - self.source.rfind("\n", 0, offset))

    def report(self, message, offset):
        position = self.position(offset)
        lines = self.source.splitlines()
        self.diagnostics.append(Diagnostic("Léxico", message, position,
                                          lines[position.line - 1] if lines else ""))

    def t_comment(self, t):
        r"//[^\n]*|/\*[\s\S]*?(?:\*/|$)"
        t.lexer.lineno += t.value.count("\n")
        if t.value.startswith("/*") and not t.value.endswith("*/"):
            self.report("Comentario de bloque sin cerrar.", t.lexpos)

    def t_raw_string(self, t):
        r'r(?:\#*)"'
        hashes = t.value[1:-1]
        end = t.lexer.lexdata.find('"' + hashes, t.lexer.lexpos)
        if end < 0:
            self.report("Cadena sin cerrar.", t.lexpos)
            t.lexer.lexpos = len(self.source)
            return
        t.type = "STRING"
        t.value = self.source[t.lexer.lexpos:end]
        t.lexer.lineno += t.value.count("\n")
        t.lexer.lexpos = end + 1 + len(hashes)
        return t

    def t_STRING(self, t):
        r'"(?:[^"\\\n]|\\.)*"'
        try:
            t.value = ast.literal_eval(t.value)
        except (SyntaxError, ValueError):
            self.report("Secuencia de escape inválida.", t.lexpos)
            t.value = ""
        return t

    def t_CHAR(self, t):
        r"'(?:[^'\\\n]|\\.)'"
        try:
            t.value = ast.literal_eval(t.value)
        except (SyntaxError, ValueError):
            self.report("Carácter inválido.", t.lexpos)
            t.value = ""
        return t

    def t_LABEL(self, t):
        r"'[a-zA-Z_][a-zA-Z_0-9]*"
        t.value = t.value[1:]
        return t

    def t_FLOAT(self, t):
        r"\d+\.\d+(?:[eE][+-]?\d+)?|\d+[eE][+-]?\d+"
        t.value = float(t.value)
        return t

    def t_INTEGER(self, t):
        r"\d+"
        t.value = int(t.value)
        return t

    def t_ID(self, t):
        r"[a-zA-Z_][a-zA-Z_0-9]*"
        t.type = self.reserved.get(t.value, "ID")
        return t

    def t_newline(self, t):
        r"\n+"
        t.lexer.lineno += len(t.value)

    def t_error(self, t):
        self.report(f"Carácter no reconocido {t.value[0]!r}.", t.lexpos)
        t.lexer.skip(1)

    def token(self):
        return self.lexer.token()
