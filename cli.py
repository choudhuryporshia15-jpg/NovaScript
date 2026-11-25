"""Command-line interface and REPL."""
import argparse
import sys
from pathlib import Path
from .compiler import compile_source
from .vm import VirtualMachine, VMError
from .disassembler import disassemble
from .transpiler import transpile

def run_source(source):
    code = compile_source(source)
    vm = VirtualMachine()
    vm.run(code)

def repl():
    print("NovaScript REPL 1.0 — type 'exit' to quit")
    vm = VirtualMachine()
    while True:
        try:
            line = input("nova> ")
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if line.strip() in ("exit", "quit"): break
        if not line.strip(): continue
        try:
            code = compile_source(line)
            vm.run(code)
        except Exception as exc:
            print(f"Error: {exc}", file=sys.stderr)

def main(argv=None):
    parser = argparse.ArgumentParser(prog="nova", description="NovaScript language tools")
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("run","compile","dis","transpile"):
        p=sub.add_parser(name); p.add_argument("file")
    sub.add_parser("repl")
    args=parser.parse_args(argv)
    try:
        if args.command == "repl":
            repl(); return 0
        source=Path(args.file).read_text(encoding="utf-8")
        if args.command == "run": run_source(source)
        elif args.command == "compile": print(compile_source(source))
        elif args.command == "dis": print(disassemble(compile_source(source)))
        elif args.command == "transpile": print(transpile(source), end="")
        return 0
    except (OSError, Exception) as exc:
        print(f"nova: {exc}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    raise SystemExit(main())
