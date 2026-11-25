"""Human-readable bytecode disassembly."""
def disassemble(code):
    lines = []
    for index, ins in enumerate(code):
        arg = "" if ins.arg is None else repr(ins.arg)
        lines.append(f"{index:04d}  {ins.op:<14} {arg}".rstrip())
    return "\n".join(lines)
