"""AST to stack-bytecode compiler."""
from dataclasses import dataclass
from .parser import Literal, Variable, Unary, Binary, Store, Show, When, Loop, Program, parse

@dataclass
class Instruction:
    op: str
    arg: object = None

class CompileError(Exception): pass

class Compiler:
    def __init__(self): self.code = []

    def emit(self, op, arg=None):
        self.code.append(Instruction(op, arg))
        return len(self.code) - 1

    def patch(self, index, target):
        self.code[index].arg = target

    def compile(self, program):
        self.code = []
        for stmt in program.statements: self.statement(stmt)
        self.emit("HALT")
        return self.code

    def statement(self, node):
        if isinstance(node, Store):
            self.expression(node.value); self.emit("STORE", node.name)
        elif isinstance(node, Show):
            for value in node.values: self.expression(value)
            self.emit("PRINT", len(node.values))
        elif isinstance(node, When):
            self.expression(node.condition)
            false_jump = self.emit("JUMP_IF_FALSE", None)
            for stmt in node.yes: self.statement(stmt)
            if node.no:
                end_jump = self.emit("JUMP", None)
                self.patch(false_jump, len(self.code))
                for stmt in node.no: self.statement(stmt)
                self.patch(end_jump, len(self.code))
            else:
                self.patch(false_jump, len(self.code))
        elif isinstance(node, Loop):
            start = len(self.code)
            self.expression(node.condition)
            exit_jump = self.emit("JUMP_IF_FALSE", None)
            for stmt in node.body: self.statement(stmt)
            self.emit("JUMP", start)
            self.patch(exit_jump, len(self.code))
        elif isinstance(node, Program):
            for stmt in node.statements: self.statement(stmt)
        else:
            raise CompileError(f"Unsupported statement: {type(node).__name__}")

    def expression(self, node):
        if isinstance(node, Literal): self.emit("CONST", node.value)
        elif isinstance(node, Variable): self.emit("LOAD", node.name)
        elif isinstance(node, Unary):
            self.expression(node.right)
            self.emit("NOT" if node.op == "NOT" else "NEG")
        elif isinstance(node, Binary):
            self.expression(node.left); self.expression(node.right)
            ops = {
                "PLUS":"ADD", "MINUS":"SUB", "STAR":"MUL", "SLASH":"DIV",
                "PERCENT":"MOD", "EQEQ":"EQ", "BANGEQ":"NE",
                "LESS":"LT", "LESSEQ":"LE", "GREATER":"GT", "GREATEREQ":"GE",
                "AND":"AND", "OR":"OR",
            }
            self.emit(ops[node.op])
        else: raise CompileError(f"Unsupported expression: {type(node).__name__}")

def compile_source(source):
    return Compiler().compile(parse(source))
