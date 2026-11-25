"""Stack-based NovaScript virtual machine."""
from .compiler import compile_source

class VMError(Exception): pass

class VirtualMachine:
    def __init__(self, output=print, max_steps=1_000_000):
        self.output = output
        self.max_steps = max_steps
        self.globals = {}
        self.stack = []
        self.ip = 0
        self.code = []

    def pop(self):
        if not self.stack: raise VMError("Stack underflow")
        return self.stack.pop()

    def run(self, code):
        self.code = code
        self.stack = []
        self.ip = 0
        steps = 0
        while self.ip < len(self.code):
            steps += 1
            if steps > self.max_steps:
                raise VMError("Execution step limit exceeded")
            ins = self.code[self.ip]
            self.ip += 1
            op, arg = ins.op, ins.arg
            try:
                if op == "CONST": self.stack.append(arg)
                elif op == "LOAD":
                    if arg not in self.globals: raise VMError(f"Undefined variable '{arg}'")
                    self.stack.append(self.globals[arg])
                elif op == "STORE": self.globals[arg] = self.pop()
                elif op == "PRINT":
                    count = arg
                    values = self.stack[-count:] if count else []
                    if count: del self.stack[-count:]
                    self.output(" ".join(str(v) for v in values))
                elif op == "JUMP": self.ip = arg
                elif op == "JUMP_IF_FALSE":
                    if not self.pop(): self.ip = arg
                elif op == "NEG": self.stack.append(-self.pop())
                elif op == "NOT": self.stack.append(not self.pop())
                elif op in ("ADD","SUB","MUL","DIV","MOD","EQ","NE","LT","LE","GT","GE","AND","OR"):
                    right, left = self.pop(), self.pop()
                    result = {
                        "ADD": lambda: left + right, "SUB": lambda: left - right,
                        "MUL": lambda: left * right, "DIV": lambda: left / right,
                        "MOD": lambda: left % right, "EQ": lambda: left == right,
                        "NE": lambda: left != right, "LT": lambda: left < right,
                        "LE": lambda: left <= right, "GT": lambda: left > right,
                        "GE": lambda: left >= right, "AND": lambda: bool(left and right),
                        "OR": lambda: bool(left or right),
                    }[op]()
                    self.stack.append(result)
                elif op == "HALT": break
                else: raise VMError(f"Unknown opcode '{op}'")
            except VMError:
                raise
            except Exception as exc:
                raise VMError(f"{op} failed: {exc}") from exc
        return self.globals

def execute(source, output=print, globals_=None):
    vm = VirtualMachine(output=output)
    if globals_: vm.globals.update(globals_)
    vm.run(compile_source(source))
    return vm.globals
