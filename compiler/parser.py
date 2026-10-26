"""PLY grammar producing a custom AST; no execution in grammar actions."""
from ply import yacc, lex
from compiler.lexer import Lexer
from compiler.ast import Node, ParseResult
from compiler.model import Diagnostic, SourcePosition

class Parser:
    tokens = Lexer.tokens
    precedence = (("left", "OR"), ("left", "AND"),
                  ("nonassoc", "EQ", "NE", "<", ">", "LE", "GE"),
                  ("left", "+", "-"), ("left", "*", "/", "%"),
                  ("right", "UNARY"),
                  ("left", "POSTFIX", "(", "[", ".", "!"))

    def __init__(self):
        self.parser = yacc.yacc(module=self, start="program", write_tables=False, debug=False)

    def node(self, kind, p, value=None, children=None):
        first = p[1] if len(p) > 1 else None
        position = first.position if isinstance(first, Node) else self.scanner.position(p.lexpos(1) if len(p) > 1 else 0)
        return Node(kind, position, value, children or [])

    def parse(self, source):
        self.scanner = Lexer(source)
        self.diagnostics = self.scanner.diagnostics
        self.pending = None
        self.insertions = set()
        self.open_braces = 0
        self.previous_end = self.last_end = 0
        tree = self.parser.parse(lexer=self.scanner.lexer, tokenfunc=self.next_token, tracking=True)
        return ParseResult(tree or Node("program", SourcePosition(1, 1)), self.diagnostics)

    def next_token(self):
        if self.pending is not None:
            token, self.pending = self.pending, None
            return token
        token = self.scanner.token()
        if token:
            self.previous_end, self.last_end = self.last_end, self.scanner.lexer.lexpos
            if token.type == "{":
                self.open_braces += 1
            elif token.type == "}":
                self.open_braces -= 1
        return token

    def synthetic(self, kind, offset):
        token = lex.LexToken()
        token.type = token.value = kind
        token.lexpos = offset
        token.lineno = self.scanner.position(offset).line
        return token

    def p_program(self, p):
        "program : functions"
        p[0] = Node("program", SourcePosition(1, 1), children=p[1])

    def p_functions(self, p):
        """functions : functions function
                     | empty"""
        p[0] = p[1] + [p[2]] if len(p) == 3 else []

    def p_function(self, p):
        "function : FN ID '(' parameters ')' result_type block"
        p[0] = self.node("function", p, p[2], p[4] + [p[6], p[7]])

    def p_parameters(self, p):
        """parameters : parameter_list
                      | empty"""
        p[0] = p[1] or []

    def p_parameter_list(self, p):
        """parameter_list : parameter_list ',' parameter
                          | parameter"""
        p[0] = p[1] + [p[3]] if len(p) == 4 else [p[1]]

    def p_parameter(self, p):
        "parameter : ID ':' type"
        p[0] = self.node("parameter", p, p[1], [p[3]])

    def p_result_type(self, p):
        """result_type : ARROW type
                       | empty"""
        p[0] = p[2] if len(p) == 3 else Node("type", SourcePosition(1, 1), "unit")

    def p_type(self, p):
        """type : I32
                | F64
                | BOOL
                | CHAR_TYPE
                | STRING_TYPE
                | '[' type ';' INTEGER ']'"""
        p[0] = self.node("array_type", p, p[4], [p[2]]) if len(p) == 6 else self.node("type", p, p[1])

    def p_block(self, p):
        "block : '{' statements '}'"
        p[0] = self.node("block", p, children=p[2])

    def p_statement_error(self, p):
        "statement : error ';'"
        p[0] = None

    def p_statements(self, p):
        """statements : statements statement
                      | empty"""
        p[0] = p[1] + ([p[2]] if p[2] is not None else []) if len(p) == 3 else []

    def p_statement(self, p):
        """statement : declaration ';'
                     | expression ';'
                     | assignment ';'
                     | if_statement
                     | while_statement
                     | loop_statement
                     | match_statement
                     | block"""
        p[0] = p[1]

    def p_declaration(self, p):
        "declaration : LET mutable ID annotation initializer"
        p[0] = self.node("declaration", p, {"name": p[3], "mutable": p[2]}, [n for n in [p[4], p[5]] if n is not None])

    def p_mutable(self, p):
        """mutable : MUT
                   | empty"""
        p[0] = p[1] is not None

    def p_annotation(self, p):
        """annotation : ':' type
                      | empty"""
        p[0] = p[2] if len(p) == 3 else None

    def p_initializer(self, p):
        """initializer : '=' expression
                       | empty"""
        p[0] = p[2] if len(p) == 3 else None

    def p_assignment(self, p):
        """assignment : expression '=' expression
                      | expression ADDASSIGN expression
                      | expression SUBASSIGN expression
                      | expression MULASSIGN expression
                      | expression DIVASSIGN expression
                      | expression MODASSIGN expression"""
        p[0] = self.node("assignment", p, p[2], [p[1], p[3]])

    def p_transfer(self, p):
        """statement : RETURN optional_expression ';'
                     | BREAK optional_label ';'
                     | CONTINUE optional_label ';'"""
        p[0] = self.node(p[1], p, p[2] if not isinstance(p[2], Node) else None,
                         [p[2]] if isinstance(p[2], Node) else [])

    def p_optional_expression(self, p):
        """optional_expression : expression
                               | empty"""
        p[0] = p[1]

    def p_optional_label(self, p):
        """optional_label : LABEL
                          | empty"""
        p[0] = p[1]

    def p_if(self, p):
        "if_statement : IF expression block else_clause"
        p[0] = self.node("if", p, children=[p[2], p[3]] + ([p[4]] if p[4] else []))

    def p_else(self, p):
        """else_clause : ELSE block
                       | ELSE if_statement
                       | empty"""
        p[0] = p[2] if len(p) == 3 else None

    def p_while(self, p):
        "while_statement : WHILE expression block"
        p[0] = self.node("while", p, children=[p[2], p[3]])

    def p_loop(self, p):
        """loop_statement : LOOP block
                          | LABEL ':' LOOP block"""
        p[0] = self.node("loop", p, p[1] if len(p) == 5 else None, [p[4] if len(p) == 5 else p[2]])

    def p_match(self, p):
        "match_statement : MATCH expression '{' arms '}'"
        p[0] = self.node("match", p, children=[p[2]] + p[4])

    def p_arms(self, p):
        """arms : arms arm
                | empty"""
        p[0] = p[1] + [p[2]] if len(p) == 3 else []

    def p_arm(self, p):
        """arm : expression FATARROW expression ','
               | expression FATARROW block ','
               | expression FATARROW block"""
        p[0] = self.node("arm", p, children=[p[1], p[3]])

    def p_binary(self, p):
        """expression : expression '+' expression
                      | expression '-' expression
                      | expression '*' expression
                      | expression '/' expression
                      | expression '%' expression
                      | expression EQ expression
                      | expression NE expression
                      | expression '<' expression
                      | expression '>' expression
                      | expression LE expression
                      | expression GE expression
                      | expression AND expression
                      | expression OR expression"""
        p[0] = self.node("binary", p, p[2], [p[1], p[3]])
        p[0].position = self.scanner.position(p.lexpos(2))

    def p_unary(self, p):
        """expression : '-' expression %prec UNARY
                      | '!' expression %prec UNARY
                      | '&' expression %prec UNARY"""
        p[0] = self.node("unary", p, p[1], [p[2]])

    def p_group(self, p):
        "expression : '(' expression ')'"
        p[0] = p[2]

    def p_literal(self, p):
        """expression : INTEGER
                      | FLOAT
                      | STRING
                      | CHAR
                      | TRUE
                      | FALSE
                      | NONE"""
        kind = p.slice[1].type
        value = {"TRUE": True, "FALSE": False, "NONE": None}.get(kind, p[1])
        p[0] = self.node("literal", p, {"type": kind, "value": value})

    def p_identifier(self, p):
        """expression : ID
                      | STRING_TYPE PATH ID"""
        p[0] = self.node("identifier", p, p[1] if len(p) == 2 else p[1] + "::" + p[3])

    def p_call(self, p):
        """expression : expression '(' arguments ')' %prec POSTFIX
                      | expression '!' '(' arguments ')' %prec POSTFIX"""
        p[0] = self.node("macro_call" if len(p) == 6 else "call", p,
                         children=[p[1]] + (p[4] if len(p) == 6 else p[3]))

    def p_method(self, p):
        "expression : expression '.' ID '(' arguments ')' %prec POSTFIX"
        p[0] = self.node("method_call", p, p[3], [p[1]] + p[5])

    def p_index(self, p):
        """expression : expression '[' expression ']' %prec POSTFIX
                      | expression '[' expression RANGE expression ']' %prec POSTFIX"""
        p[0] = self.node("slice" if len(p) == 7 else "index", p,
                         children=[p[1], p[3]] + ([p[5]] if len(p) == 7 else []))

    def p_array(self, p):
        """expression : '[' arguments ']'
                      | '[' expression ';' expression ']'"""
        p[0] = self.node("array_repeat" if len(p) == 6 else "array", p,
                         children=[p[2], p[4]] if len(p) == 6 else p[2])

    def p_arguments(self, p):
        """arguments : argument_list
                     | empty"""
        p[0] = p[1] or []

    def p_argument_list(self, p):
        """argument_list : argument_list ',' expression
                         | expression"""
        p[0] = p[1] + [p[3]] if len(p) == 4 else [p[1]]

    def p_empty(self, p):
        "empty :"
        p[0] = None

    def p_error(self, token):
        offset = token.lexpos if token else len(self.scanner.source)
        position = self.scanner.position(offset)
        actions = self.parser.action.get(self.parser.state, {})
        key = (offset, self.parser.state)
        recovery = None
        if token and token.type in {"ID", "LET", "RETURN", "BREAK", "CONTINUE", "}"} and ";" in actions:
            recovery = ";"
        elif token is None and self.open_braces > 0:
            recovery = "}"
        if recovery and key not in self.insertions:
            self.insertions.add(key)
            diagnostic_offset = self.previous_end if recovery == ";" else offset
            position = self.scanner.position(diagnostic_offset)
            lines = self.scanner.source.splitlines()
            fragment = lines[position.line - 1] if position.line <= len(lines) else ""
            self.diagnostics.append(Diagnostic("Sintáctico", f"Se esperaba {recovery!r}.", position, fragment))
            self.pending = token
            if recovery == "}":
                self.open_braces -= 1
            self.parser.errok()
            return self.synthetic(recovery, offset)
        lines = self.scanner.source.splitlines()
        self.diagnostics.append(Diagnostic("Sintáctico", f"Token inesperado {token.value!r}." if token else "Fin de archivo inesperado.", position,
                                          lines[position.line - 1] if position.line <= len(lines) else ""))


def parse(source):
    return Parser().parse(source)
