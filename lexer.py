"""Tokenizer for NovaScript."""
from dataclasses import dataclass

KEYWORDS = {
    "store": "STORE", "show": "SHOW", "when": "WHEN",
    "otherwise": "OTHERWISE", "loop": "LOOP",
    "and": "AND", "or": "OR", "not": "NOT",
    "true": "TRUE", "false": "FALSE", "null": "NULL",
}

@dataclass(frozen=True)
class Token:
    kind: str
    value: object
    line: int
    column: int

class LexError(Exception):
    pass

class Lexer:
    def __init__(self, source):
        self.source = source
        self.i = 0
        self.line = 1
        self.col = 1
        self.tokens = []

    def peek(self, offset=0):
        pos = self.i + offset
        return self.source[pos] if pos < len(self.source) else "\0"

    def advance(self):
        ch = self.peek()
        if ch != "\0":
            self.i += 1
            if ch == "\n":
                self.line += 1
                self.col = 1
            else:
                self.col += 1
        return ch

    def add(self, kind, value=None, line=None, col=None):
        self.tokens.append(Token(kind, value, line or self.line, col or self.col))

    def scan_string(self, quote, line, col):
        self.advance()
        chars = []
        while self.peek() not in (quote, "\0"):
            ch = self.advance()
            if ch == "\\":
                esc = self.advance()
                mapping = {"n": "\n", "t": "\t", "r": "\r", "\\": "\\", '"': '"', "'": "'"}
                if esc not in mapping:
                    raise LexError(f"Unknown escape '\\{esc}' at {line}:{col}")
                chars.append(mapping[esc])
            else:
                chars.append(ch)
        if self.peek() == "\0":
            raise LexError(f"Unterminated string at {line}:{col}")
        self.advance()
        self.add("STRING", "".join(chars), line, col)

    def tokenize(self):
        two_char = {"==", "!=", "<=", ">="}
        singles = {
            "+": "PLUS", "-": "MINUS", "*": "STAR", "/": "SLASH",
            "%": "PERCENT", "(": "LPAREN", ")": "RPAREN",
            "{": "LBRACE", "}": "RBRACE", "=": "EQUAL",
            "<": "LESS", ">": "GREATER", ",": "COMMA", ";": "SEMI",
        }
        while self.peek() != "\0":
            ch = self.peek()
            if ch in " \t\r":
                self.advance()
                continue
            if ch == "\n":
                line, col = self.line, self.col
                self.advance()
                self.add("NEWLINE", None, line, col)
                continue
            if ch == "#":
                while self.peek() not in ("\n", "\0"):
                    self.advance()
                continue
            line, col = self.line, self.col
            if ch in ('"', "'"):
                self.scan_string(ch, line, col)
                continue
            if ch.isdigit():
                start = self.i
                while self.peek().isdigit():
                    self.advance()
                if self.peek() == "." and self.peek(1).isdigit():
                    self.advance()
                    while self.peek().isdigit():
                        self.advance()
                    value = float(self.source[start:self.i])
                else:
                    value = int(self.source[start:self.i])
                self.add("NUMBER", value, line, col)
                continue
            if ch.isalpha() or ch == "_":
                start = self.i
                while self.peek().isalnum() or self.peek() == "_":
                    self.advance()
                word = self.source[start:self.i]
                self.add(KEYWORDS.get(word, "IDENT"), word, line, col)
                continue
            pair = ch + self.peek(1)
            if pair in two_char:
                self.advance(); self.advance()
                self.add({"==": "EQEQ", "!=": "BANGEQ", "<=": "LESSEQ", ">=": "GREATEREQ"}[pair], pair, line, col)
                continue
            if ch in singles:
                self.advance()
                self.add(singles[ch], ch, line, col)
                continue
            raise LexError(f"Unexpected character {ch!r} at {line}:{col}")
        self.add("EOF", None, self.line, self.col)
        return self.tokens

def tokenize(source):
    return Lexer(source).tokenize()
