"""Recursive-descent parser and AST definitions."""
from dataclasses import dataclass
from .lexer import tokenize

class ParseError(Exception):
    pass

@dataclass
class Literal: value: object
@dataclass
class Variable: name: str
@dataclass
class Unary: op: str; right: object
@dataclass
class Binary: left: object; op: str; right: object
@dataclass
class Store: name: str; value: object
@dataclass
class Show: values: list
@dataclass
class When: condition: object; yes: list; no: list
@dataclass
class Loop: condition: object; body: list
@dataclass
class Program: statements: list

class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.current = 0

    def peek(self): return self.tokens[self.current]
    def previous(self): return self.tokens[self.current - 1]
    def check(self, kind): return self.peek().kind == kind
    def advance(self):
        if not self.check("EOF"): self.current += 1
        return self.previous()
    def match(self, *kinds):
        if self.peek().kind in kinds:
            self.advance(); return True
        return False
    def consume(self, kind, message):
        if self.check(kind): return self.advance()
        t = self.peek()
        raise ParseError(f"{message} at {t.line}:{t.column}")
    def separators(self):
        while self.match("NEWLINE", "SEMI"): pass

    def parse(self):
        statements = []
        self.separators()
        while not self.check("EOF"):
            statements.append(self.statement())
            if not self.check("EOF") and not self.check("RBRACE") and not self.check("NEWLINE") and not self.check("SEMI"):
                t = self.peek()
                raise ParseError(f"Expected end of statement at {t.line}:{t.column}")
            self.separators()
        return Program(statements)

    def statement(self):
        if self.match("STORE"):
            name = self.consume("IDENT", "Expected variable name").value
            self.consume("EQUAL", "Expected '=' after variable name")
            return Store(name, self.expression())
        if self.match("SHOW"):
            values = [self.expression()]
            while self.match("COMMA"): values.append(self.expression())
            return Show(values)
        if self.match("WHEN"):
            condition = self.expression()
            yes = self.block()
            self.separators()
            no = self.block() if self.match("OTHERWISE") else []
            return When(condition, yes, no)
        if self.match("LOOP"):
            condition = self.expression()
            return Loop(condition, self.block())
        if self.check("LBRACE"):
            return Program(self.block())
        t = self.peek()
        raise ParseError(f"Expected statement at {t.line}:{t.column}")

    def block(self):
        self.consume("LBRACE", "Expected '{' to start block")
        self.separators()
        statements = []
        while not self.check("RBRACE") and not self.check("EOF"):
            statements.append(self.statement())
            if not self.check("RBRACE") and not self.check("NEWLINE") and not self.check("SEMI"):
                t = self.peek()
                raise ParseError(f"Expected end of statement in block at {t.line}:{t.column}")
            self.separators()
        self.consume("RBRACE", "Expected '}' after block")
        return statements

    def expression(self): return self.or_expr()
    def left_assoc(self, sub, kinds):
        expr = sub()
        while self.peek().kind in kinds:
            op = self.advance().kind
            expr = Binary(expr, op, sub())
        return expr
    def or_expr(self): return self.left_assoc(self.and_expr, {"OR"})
    def and_expr(self): return self.left_assoc(self.equality, {"AND"})
    def equality(self): return self.left_assoc(self.comparison, {"EQEQ", "BANGEQ"})
    def comparison(self): return self.left_assoc(self.term, {"LESS", "LESSEQ", "GREATER", "GREATEREQ"})
    def term(self): return self.left_assoc(self.factor, {"PLUS", "MINUS"})
    def factor(self): return self.left_assoc(self.unary, {"STAR", "SLASH", "PERCENT"})

    def unary(self):
        if self.match("NOT", "MINUS"):
            return Unary(self.previous().kind, self.unary())
        return self.primary()

    def primary(self):
        if self.match("NUMBER", "STRING"): return Literal(self.previous().value)
        if self.match("TRUE"): return Literal(True)
        if self.match("FALSE"): return Literal(False)
        if self.match("NULL"): return Literal(None)
        if self.match("IDENT"): return Variable(self.previous().value)
        if self.match("LPAREN"):
            expr = self.expression()
            self.consume("RPAREN", "Expected ')' after expression")
            return expr
        t = self.peek()
        raise ParseError(f"Expected expression at {t.line}:{t.column}")

def parse(source):
    return Parser(tokenize(source)).parse()
