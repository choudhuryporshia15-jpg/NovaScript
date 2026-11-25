import unittest
from novascript.lexer import tokenize
from novascript.compiler import compile_source
from novascript.vm import VirtualMachine, VMError
from novascript.disassembler import disassemble
from novascript.transpiler import transpile

class NovaScriptTests(unittest.TestCase):
    def run_code(self, source):
        output=[]
        vm=VirtualMachine(output=output.append)
        vm.run(compile_source(source))
        return output, vm.globals

    def test_lexer_keywords_and_strings(self):
        tokens=tokenize('store x = "when show"; # comment\nshow x')
        self.assertEqual(tokens[0].kind, "STORE")
        self.assertEqual(tokens[3].value, "when show")

    def test_arithmetic_and_variables(self):
        out, env=self.run_code("store x = 5 + 3 * 2\nshow x")
        self.assertEqual(out, ["11"])
        self.assertEqual(env["x"], 11)

    def test_condition(self):
        out,_=self.run_code('when 4 > 2 { show "yes" } otherwise { show "no" }')
        self.assertEqual(out, ["yes"])

    def test_loop(self):
        out,_=self.run_code("store n = 3\nloop n > 0 { show n\nstore n = n - 1 }")
        self.assertEqual(out, ["3","2","1"])

    def test_disassembler(self):
        text=disassemble(compile_source("show 7"))
        self.assertIn("CONST", text)
        self.assertIn("PRINT", text)

    def test_transpiler_keeps_keyword_inside_string(self):
        result=transpile('show "when store"\nstore x = true')
        self.assertIn("'when store'", result)
        self.assertIn("x = True", result)

    def test_undefined_variable(self):
        with self.assertRaises(VMError):
            self.run_code("show missing")

if __name__ == "__main__":
    unittest.main()
