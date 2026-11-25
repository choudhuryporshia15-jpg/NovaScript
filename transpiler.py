"""Token-aware transpiler from NovaScript to Python for the supported subset."""
from .lexer import tokenize

BINARY = {
    "PLUS":"+","MINUS":"-","STAR":"*","SLASH":"/","PERCENT":"%",
    "EQEQ":"==","BANGEQ":"!=","LESS":"<","LESSEQ":"<=",
    "GREATER":">","GREATEREQ":">=","AND":"and","OR":"or",
}

class TranspileError(Exception): pass

class Transpiler:
    def __init__(self, source):
        self.tokens = tokenize(source)
        self.i = 0
        self.lines = []
        self.indent = 0

    def peek(self): return self.tokens[self.i]
    def take(self): t=self.peek(); self.i += 1; return t
    def match(self, *k):
        if self.peek().kind in k: return self.take()
        return None
    def expect(self, k):
        t=self.match(k)
        if not t: raise TranspileError(f"Expected {k} at {self.peek().line}:{self.peek().column}")
        return t
    def skip_lines(self):
        while self.match("NEWLINE","SEMI"): pass
    def emit(self, text): self.lines.append("    "*self.indent + text)

    # Convert expression tokens without rewriting strings or identifiers.
    def expression_text(self, stop):
        parts=[]
        while self.peek().kind not in stop and self.peek().kind not in ("EOF","NEWLINE","SEMI","RBRACE","COMMA"):
            t=self.take()
            if t.kind == "STRING": parts.append(repr(t.value))
            elif t.kind == "NUMBER": parts.append(repr(t.value))
            elif t.kind == "IDENT": parts.append(t.value)
            elif t.kind in ("TRUE","FALSE","NULL"): parts.append({"TRUE":"True","FALSE":"False","NULL":"None"}[t.kind])
            elif t.kind in BINARY: parts.append(BINARY[t.kind])
            elif t.kind == "NOT": parts.append("not")
            elif t.kind == "MINUS": parts.append("-")
            elif t.kind == "LPAREN": parts.append("(")
            elif t.kind == "RPAREN": parts.append(")")
            else: raise TranspileError(f"Unsupported expression token {t.kind}")
        if not parts: raise TranspileError("Expected expression")
        return " ".join(parts)

    def block(self):
        self.expect("LBRACE")
        self.indent += 1
        self.skip_lines()
        count=0
        while self.peek().kind not in ("RBRACE","EOF"):
            self.statement(); count += 1
            self.skip_lines()
        self.expect("RBRACE")
        self.indent -= 1
        if count == 0: self.emit("pass")

    def statement(self):
        if self.match("STORE"):
            name=self.expect("IDENT").value; self.expect("EQUAL")
            expr=self.expression_text({"NEWLINE","SEMI","RBRACE"})
            self.emit(f"{name} = {expr}")
        elif self.match("SHOW"):
            vals=[self.expression_text({"COMMA","NEWLINE","SEMI","RBRACE"})]
            while self.match("COMMA"):
                vals.append(self.expression_text({"COMMA","NEWLINE","SEMI","RBRACE"}))
            self.emit("print(" + ", ".join(vals) + ")")
        elif self.match("WHEN"):
            cond=self.expression_text({"LBRACE"})
            self.emit(f"if {cond}:"); self.block()
            self.skip_lines()
            if self.match("OTHERWISE"):
                self.emit("else:"); self.block()
        elif self.match("LOOP"):
            cond=self.expression_text({"LBRACE"})
            self.emit(f"while {cond}:"); self.block()
        else:
            raise TranspileError(f"Unsupported statement at {self.peek().line}:{self.peek().column}")

    def transpile(self):
        self.skip_lines()
        while self.peek().kind != "EOF":
            self.statement(); self.skip_lines()
        return "\n".join(self.lines) + ("\n" if self.lines else "")

def transpile(source):
    return Transpiler(source).transpile()
