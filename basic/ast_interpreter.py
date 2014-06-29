import sys
from operator import add, sub, mul, div, eq

operations = {
    'add_int': add,
    'sub_int': sub,
    'mul_int': mul,
    'div_int': div,
    'eq_int': eq,
    'eq_str': eq,
    'cat_str': add}

class ASTInterpreter:
    def __init__(self, ast_context, write=sys.stdout.write, read=sys.stdin.readline):
        self.const_int = ast_context.const_int
        self.const_str = ast_context.const_str
        self.integers = [0] * ast_context.nb_int
        self.strings = [''] * ast_context.nb_str
        self.code = ast_context.code
        self.labels = ast_context.labels
        self.read = read
        self.write = write

    def evaluate(self, expr):
        if expr[0] in operations:
            a = self.evaluate(expr[2])
            b = self.evaluate(expr[3])
            return operations[expr[0]](a, b)
        elif expr[0] == 'var':
            if expr[1] == 'int':
                return self.integers[expr[2]]
            elif expr[1] == 'str':
                return self.strings[expr[2]]
            else:
                assert False
        elif expr[0] == 'cst':
            if expr[1] == 'int':
                return self.const_int[expr[2]]
            elif expr[1] == 'str':
                return self.const_str[expr[2]]
            else:
                assert False
        else:
            assert False, expr

    def execute(self):
        ip = 0
        while True:
            instr = self.code[ip]
            ip += 1
            jump = self.exec_one_instr(instr)
            if jump is 'end':
                return
            elif jump is not None:
                ip = self.labels[jump]

    def exec_one_instr(self, instr):
        if instr[0] == 'input':
            prompt = self.evaluate(instr[1])
            self.write(prompt)
            result = self.read().rstrip('\n')
            if instr[2] == 'int':
                self.integers[instr[3]] = int(result)
            else:
                self.strings[instr[3]] = result
        elif instr[0] == 'assign':
            if instr[1] == 'int':
                self.integers[instr[2]] = self.evaluate(instr[3])
            elif instr[1] == 'str':
                self.strings[instr[2]] = self.evaluate(instr[3])
        elif instr[0] == 'if':
            cond = self.evaluate(instr[1])
            if cond:
                return self.exec_one_instr(instr[2])
        elif instr[0] == 'goto':
            return instr[1]
        elif instr[0] == 'print':
            self.write(' '.join(str(self.evaluate(ex)) for ex in instr[1:])+'\n')
        elif instr[0] == 'end':
            return 'end'
        else:
            assert False, instr