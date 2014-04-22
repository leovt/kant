import struct

src = '''
10 DIM I AS INTEGER
20 DIM NAME AS STRING
30 INPUT "WHATS YOUR NAME? " ; NAME
40 INPUT "WHATS YOUR AGE? " ; I
50 I = I - 1
60 IF I = 0 THEN GOTO 90
70 PRINT "HELLO," ; NAME ; I
80 GOTO 50
90 NAME = NAME + ""
95 I = I = 1
96 I = NAME = "NAME"
100 END
'''

keywords = ['DIM', 'AS', 'INTEGER', 'STRING', 'INPUT', 'IF', 'THEN', 'GOTO', 'PRINT', 'END']
types = {'INTEGER': 'int', 'STRING': 'str'}



def error(msg):
    print msg
    raise Exception(msg)

def variable(x, lineno):
    x = x.upper()
    if not x.isalpha() or x in keywords:
        error('line %d: expected a variable name instead of %s' % (lineno, x))
    return x

def tokenize(line):
    state = ''
    start = 0
    for i, c in enumerate(line):
        if state == '':
            if c == '"':
                state = '"'
                yield line[start:i]
                start = i
            elif c in (' ', '\t'):
                state = ' '
                yield line[start:i]
            elif c in ';+-*/=()':
                state = ' '
                yield line[start:i]
                yield c
        elif state == '"':
            if c == '"':
                state = '""'
        elif state == '""':
            if c == '"':
                state = '"'
            else:
                state = ''
                yield line[start:i]
                start = i
        elif state == ' ':
            if c == '"':
                state = '"'
                start = i
            elif c in (' ', '\t'):
                pass
            elif c in ';+-*/=()':
                yield c
            else:
                state = ''
                start = i
        else:
            assert False
    if state == '':
        yield line[start:]
    elif state == '"':
        error('unmatched "', 0)
    elif state == '""':
        yield line[start:]
    elif state == ' ':
        pass
    else:
        assert False

def stmt(tokens, lineno, context):
    if tokens[0] == 'DIM':
        if tokens[2] != 'AS':
            error('line %d "AS" expected' % (lineno, ))
        var = variable(tokens[1], lineno)
        v_type = types[tokens[3]]
        if tokens[3] == 'INTEGER':
            v_id = context.nb_int
            context.nb_int += 1
        elif tokens[3] == 'STRING':
            v_id = context.nb_str
            context.nb_str += 1
        else:
            error('line %d: unknown type %s' %( lineno, tokens[3]))
        context.symbols[var] = v_type, v_id
        return ()

    elif tokens[0] == 'INPUT':
        t = tokens.index(';')
        v_type, v_id = context.symbols[variable(tokens[t+1], lineno)]
        return ('input', expr(tokens[1:t], lineno, context), v_type, v_id)

    elif tokens[0] == 'IF':
        t = tokens.index('THEN')
        cond = expr(tokens[1:t], lineno, context)
        return ('if', cond, stmt(tokens[t+1:], lineno, context))

    elif tokens[0] == 'PRINT':
        rest = tokens[1:]
        result = ['print']
        while rest:
            if ';' in rest:
                t = rest.index(';')
            else:
                t = len(rest)
            result.append(expr(rest[:t], lineno, context))
            rest = rest[t+1:]
        return tuple(result)

    elif tokens[0] == 'GOTO':
        return ('goto', int(tokens[1]))

    elif tokens[0] == 'END':
        return ('end',)

    elif tokens[1] == '=':
        v_type, v_id = context.symbols[variable(tokens[0], lineno)]
        return ('assign', v_type, v_id, expr(tokens[2:], lineno, context))

    else:
        error('unrecognized statement %s on line %d' % (' '.join(tokens), lineno))

def expr(tokens, lineno, context):
    symbols = context.symbols
    result = []
    stack = []

    op = {'+':1, '-':1,
          '*':2, '/':2,
          '=':3,
          '(':4,}

    def operation(op, a, b):
        type_a = a[1]
        type_b = b[1]
        ops = {('int', '+', 'int'): ('int', 'add_int'),
               ('int', '-', 'int'): ('int', 'sub_int'),
               ('int', '*', 'int'): ('int', 'mul_int'),
               ('int', '/', 'int'): ('int', 'div_int'),
               ('str', '+', 'str'): ('str', 'cat_str'),
               ('int', '=', 'int'): ('int', 'eq_int'),
               ('str', '=', 'str'): ('int', 'eq_str')}
        type_r, typed_op = ops.get((type_a, op, type_b), None)
        if type_r is None:
            error('invalid use of operator types %s %s %s on line %d' % (type_a, op, type_b, lineno))
        else:
            return (typed_op, type_r, a, b)

    for t in tokens:
        if t.isdigit():
            result.append(('cst', 'int', context.add_const('int', int(t))))
        elif t[0] == '"':
            assert t[-1] == '"'
            result.append(('cst', 'str', context.add_const('str', t[1:-1].replace('""', '"'))))
        elif t.isalpha():
            if t in symbols:
                v_type, v_id = symbols[t]
            result.append(('var', v_type, v_id))
        elif t in '+-*/=':
            while stack and op[stack[-1]] > op[t]:
                s = stack.pop()
                b = result.pop()
                a = result.pop()
                
                result.append(operation(s, a, b))
            stack.append(t)
        elif t == '(':
            stack.push(t)
        elif t == ')':
            s = stack.pop()
            while s != '(':
                b = result.pop()
                a = result.pop()
                result.append(operation(s, a, b))
                s = stack.pop()
        else:
            assert False
    while stack:
        s = stack.pop()
        b = result.pop()
        a = result.pop()
        result.append(operation(s, a, b))

    assert len(result) == 1

    return result.pop()

class ASTContext:
    def __init__(self):
        self.symbols = {}
        self.nb_int = 0
        self.nb_str = 0

        self.code = []
        self.labels = {}
        self.const_int = []
        self.const_str = []

    def add_const(self, typ, val):
        array = {'int': self.const_int,
                 'str': self.const_str}[typ]
        if val in array:
            return array.index(val)
        else:
            array.append(val)
            return len(array) -1
        

def parse():
    context = ASTContext()

    lastno = 0
    
    from itertools import count
    symbols = {}

    for line in src.splitlines():
        tokens = [t for t in tokenize(line) if t.strip()]
        if not tokens:
            continue
        lineno = int(tokens[0])
        if lineno <= lastno:
            error('line numbers not strictly increasing: %d follows %d' % (lineno, lastno))
        context.labels[lineno] = len(context.code)
        statement = stmt(tokens[1:], lineno, context)
        if statement:
            context.code.append(statement)

        lastno = lineno

    return context

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
    def __init__(self, ast_context):
        self.const_int = ast_context.const_int
        self.const_str = ast_context.const_str
        self.integers = [0] * ast_context.nb_int
        self.strings = [''] * ast_context.nb_str
        self.code = ast_context.code
        self.labels = ast_context.labels

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
            result = raw_input(prompt)
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
            print ' '.join(str(self.evaluate(ex)) for ex in instr[1:])
        elif instr[0] == 'end':
            return 'end'
        else:
            assert False, instr


class BCContext():
    @classmethod
    def fromast(cls, ast_context):
        self = cls()
        self.code = []
        self.jmps = []

        jpos = {}
    
        for ln, instr in enumerate(ast_context.code):
            jpos[ln] = len(self.code)
            self.translate_instr(instr)
            #code.append(('dbg',))
        for codepos, label in self.jmps:
            ah, al = divmod(jpos[ast_context.labels[label]], 256)
            self.code[codepos+1] = al
            self.code[codepos+2] = ah
            
        del self.jmps
        self.nb_int = ast_ctx.nb_int
        self.nb_str = ast_ctx.nb_str
        self.const_int = ast_ctx.const_int
        self.const_str = ast_ctx.const_str        
        return self    

    
    def translate_expr(self, expr):
        if expr[0] in operations:
            self.translate_expr(expr[2])
            self.translate_expr(expr[3])
            self.emit(expr[0])
        elif expr[0] == 'var':
            self.emit('load_'+expr[1], expr[2])
        elif expr[0] == 'cst':
            self.emit('load_const_'+expr[1], expr[2])
        else:
            assert False, expr

        
    def translate_instr(self, instr):
        if instr[0] == 'input':
            self.translate_expr(instr[1])
            self.emit('print_' + instr[1][1])
            self.emit('input_' + instr[2], instr[3])
        elif instr[0] == 'assign':
            self.translate_expr(instr[3])
            self.emit('save_' + instr[1], instr[2])
        elif instr[0] == 'if':
            self.translate_expr(instr[1])
            jmp_instr = len(self.code)
            self.emit('jmpz', 0xdead)
            self.translate_instr(instr[2])
            ah, al = divmod(len(self.code), 256)
            self.code[jmp_instr+1] = al
            self.code[jmp_instr+2] = ah
        elif instr[0] == 'goto':
            self.jmps.append((len(self.code), instr[1]))
            self.emit('jmp', 0xdead)
        elif instr[0] == 'print':
            for ex in instr[1:]:
                self.translate_expr(ex)
                self.emit('print_' + ex[1])
            self.emit('println')
        elif instr[0] == 'end':
            self.emit('end')
        else:
            assert False, instr
            
    def emit(self, mnemonic, arg=None):
        self.code.append(opcodes[mnemonic])
        if arg is not None:
            ah, al = divmod(arg, 256)
            self.code.append(al)
            self.code.append(ah)

    
    def disassemble(self):
        ip = 0
        while ip<len(self.code):
            bytecode = self.code[ip]
            mnemonic = opnames[bytecode]
            ip += 1
            if bytecode > opcodes['hasarg']:
                arg = self.code[ip] + 256 * self.code[ip+1]
                ip += 2
                print '%3d: %s %d' % (ip, mnemonic, arg)
            else:
                print '%3d: %s' % (ip, mnemonic)
                
    def serialize(self, outfile):
        outfile.write(struct.pack('HHHHH', len(self.code), self.nb_int, self.nb_str, len(self.const_int), len(self.const_str)))
        for i in self.const_int:
            outfile.write(struct.pack('l', i))
        for s in self.const_str:
            outfile.write(struct.pack('L', len(s)))
            outfile.write(s)
        for c in self.code:
            outfile.write(struct.pack('B', c))
            
    @classmethod
    def fromfile(cls, infile):
        self = cls()
        code_length, self.nb_int, self.nb_str, nb_const_int, nb_const_str = struct.unpack('HHHHH', infile.read(10))
        self.const_int = [
            struct.unpack('l', infile.read(4))[0] for _ in xrange(nb_const_int)]
        self.const_str = []
        for _ in xrange(nb_const_str):
            length = struct.unpack('L', infile.read(4))[0]
            self.const_str.append(infile.read(length))
        self.code = []
        for _ in xrange(code_length):
            self.code.append(struct.unpack('B', infile.read(1))[0])
        return self
            
opnames = [
 'end',
 'add_int',
 'sub_int',
 'mul_int',
 'div_int',
 'eq_int',
 'cat_str',
 'eq_str',
 'print_int',
 'print_str',
 'println',
 'hasarg',
 'load_const_int',
 'load_int',
 'input_int',
 'save_int',
 'load_const_str',
 'load_str',
 'input_str',
 'save_str',
 'jmp',
 'jmpz'
 ]
opcodes = {name:i for i,name in enumerate(opnames)}
        

def execute_trans(bc_context):
    ip = 0
    istack = []
    sstack = istack # does not need to be seperate in python
    ipush = istack.append
    ipop = istack.pop
    spush = sstack.append
    spop = sstack.pop
    integers = [0] * bc_context.nb_int
    strings = [''] * bc_context.nb_str

    while True:
        bytecode = bc_context.code[ip]
        mnemonic = opnames[bytecode]
        ip += 1
        arg = None
        if bytecode > opcodes['hasarg']:
            arg = bc_context.code[ip] + 256 * bc_context.code[ip+1]
            ip += 2
        if mnemonic == 'load_int':
            ipush(integers[arg])
        elif mnemonic == 'load_str':
            spush(strings[arg])
            
        elif mnemonic == 'load_const_int':
            ipush(bc_context.const_int[arg])
        elif mnemonic == 'load_const_str':
            spush(bc_context.const_str[arg])

        elif mnemonic == 'input_int':
            integers[arg] = int(raw_input())
        elif mnemonic == 'input_str':
            strings[arg] = raw_input()
            
        elif mnemonic == 'save_int':
            integers[arg] = ipop()
        elif mnemonic == 'save_str':
            strings[arg] = spop()
            
        elif mnemonic == 'print_str':
            print spop(),
        elif mnemonic == 'print_int':
            print ipop(),
        elif mnemonic == 'println':
            print

        elif mnemonic == 'add_int':
            ipush(ipop() + ipop())
        elif mnemonic == 'sub_int':
            ipush(- ipop() + ipop())
        elif mnemonic == 'eq_int':
            ipush(ipop() == ipop())

        elif mnemonic == 'cat_str':
            spush(spop() + spop())
        elif mnemonic == 'eq_str':
            ipush(spop() + spop())

        elif mnemonic == 'jmp':
            ip = arg
        elif mnemonic == 'jmpz':
            if not ipop():
                ip = arg

        elif mnemonic == 'end':
            break

        elif mnemonic == 'dbg':
            print len(istack), len(sstack)

        else:
            assert False, instr

        
        

if __name__ == '__main__':
    ast_ctx = parse()
    import pprint
    pprint.pprint(ast_ctx.code)
    bc_ctx = BCContext.fromast(ast_ctx)
    
    interpreter = ASTInterpreter(ast_ctx)
    #interpreter.execute()
    
    print bc_ctx.code
    bc_ctx.disassemble()
    
    with open('test.bac', 'wb') as outfile:
        bc_ctx.serialize(outfile)
        
    with open('test.bac', 'rb') as infile:
        bc_ctx = BCContext.fromfile(infile)
    
    execute_trans(bc_ctx)
    