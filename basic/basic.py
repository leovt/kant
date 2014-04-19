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
        ops = {('int', '+', 'int'): 'int',
               ('int', '-', 'int'): 'int',
               ('int', '*', 'int'): 'int',
               ('int', '/', 'int'): 'int',
               ('str', '+', 'str'): 'str',
               ('int', '=', 'int'): 'int',
               ('str', '=', 'str'): 'int'}
        type_r = ops.get((type_a, op, type_b), None)
        if type_r is None:
            error('invalid use of operator types %s %s %s on line %d' % (type_a, op, type_b, lineno))
        else:
            return (op, type_r, a, b)

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

class Context:
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
    context = Context()

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

def evaluate(expr, integers, strings, const_int, const_str):
    if expr[0] in '+-*/=':
        a = evaluate(expr[2], integers, strings, const_int, const_str)
        b = evaluate(expr[3], integers, strings, const_int, const_str)
        return {'+': add, '-': sub, '*': mul, '/': div, '=': eq}[expr[0]](a, b)
    elif expr[0] == 'var':
        if expr[1] == 'int':
            return integers[expr[2]]
        elif expr[1] == 'str':
            return strings[expr[2]]
        else:
            assert False
    elif expr[0] == 'cst':
        if expr[1] == 'int':
            return const_int[expr[2]]
        elif expr[1] == 'str':
            return const_str[expr[2]]
        else:
            assert False
    else:
        assert False, expr

def execute(context):
    integers = [0] * ctx.nb_int
    strings = [''] * ctx.nb_str
    ip = 0
    while True:
        instr = context.code[ip]
        ip += 1
        jump = exec_one_instr(instr, integers, strings, context.const_int, context.const_str)
        if jump is 'end':
            return
        elif jump is not None:
            ip = context.labels[jump]

def exec_one_instr(instr, integers, strings, const_int, const_str):
    if instr[0] == 'input':
        prompt = evaluate(instr[1], integers, strings, const_int, const_str)
        result = raw_input(prompt)
        if instr[2] == 'int':
            integers[instr[3]] = int(result)
        else:
            strings[instr[3]] = result
    elif instr[0] == 'assign':
        if instr[1] == 'int':
            integers[instr[2]] = evaluate(instr[3], integers, strings, const_int, const_str)
        elif instr[1] == 'str':
            strings[instr[2]] = evaluate(instr[3], integers, strings, const_int, const_str)
    elif instr[0] == 'if':
        cond = evaluate(instr[1], integers, strings, const_int, const_str)
        if cond:
            return exec_one_instr(instr[2], integers, strings, const_int, const_str)
    elif instr[0] == 'goto':
        return instr[1]
    elif instr[0] == 'print':
        print ' '.join(str(evaluate(ex, integers, strings, const_int, const_str)) for ex in instr[1:])
    elif instr[0] == 'end':
        return 'end'
    else:
        assert False, instr

def translate_expr(expr, context, code):
    if expr[0] in '+-*/=':
        translate_expr(expr[2], context, code)
        translate_expr(expr[3], context, code)
        code.append(({'+': 'add', '-': 'sub', '*': 'mul', '/': 'div', '=': 'eq'}[expr[0]]+'_'+expr[1],))
    elif expr[0] == 'var':
        code.append(('load_'+expr[1], expr[2]))
    elif expr[0] == 'cst':
        code.append(('load_const_'+expr[1], expr[2]))
    else:
        assert False, expr

        
def translate_instr(instr, context, code, jmps):
    if instr[0] == 'input':
        translate_expr(instr[1], context, code)
        code.append(('print_' + instr[1][1], ))
        code.append(('input_' + instr[2], instr[3]))
    elif instr[0] == 'assign':
        translate_expr(instr[3], context, code)
        code.append(('save_' + instr[1], instr[2]))
    elif instr[0] == 'if':
        translate_expr(instr[1], context, code)
        jmp_instr = len(code)
        code.append(None)
        translate_instr(instr[2], context, code, jmps)
        code[jmp_instr] = ('jmpz', len(code))
    elif instr[0] == 'goto':
        jmps.append((len(code), instr[1]))
        code.append(None)
    elif instr[0] == 'print':
        for ex in instr[1:]:
            translate_expr(ex, context, code)
            code.append(('print_' + ex[1], ))
        code.append(('println',))
    elif instr[0] == 'end':
        code.append(('end',))
    else:
        assert False, instr
        
def translate(context):
    code = []
    jmps = []

    jpos = {}
    
    for ln, instr in enumerate(context.code):
        jpos[ln] = len(code)
        translate_instr(instr, context, code, jmps)
        #code.append(('dbg',))
    for codepos, label in jmps:
        code[codepos] = ('jmp', jpos[context.labels[label]])
    return code

def execute_trans(context, code):
    ip = 0
    istack = []
    sstack = istack # does not need to be seperate in python
    ipush = istack.append
    ipop = istack.pop
    spush = sstack.append
    spop = sstack.pop
    integers = [0] * context.nb_int
    strings = [''] * context.nb_str
    while True:
        instr = code[ip]

        #print
        #print integers, istack
        #print strings, sstack
        #print ip, instr
        
        ip += 1
        if instr[0] == 'load_int':
            ipush(integers[instr[1]])
        elif instr[0] == 'load_str':
            spush(strings[instr[1]])
            
        elif instr[0] == 'load_const_int':
            ipush(context.const_int[instr[1]])
        elif instr[0] == 'load_const_str':
            spush(context.const_str[instr[1]])

        elif instr[0] == 'input_int':
            integers[instr[1]] = int(raw_input())
        elif instr[0] == 'input_str':
            strings[instr[1]] = raw_input()
            
        elif instr[0] == 'save_int':
            integers[instr[1]] = ipop()
        elif instr[0] == 'save_str':
            strings[instr[1]] = spop()
            
        elif instr[0] == 'print_str':
            print spop(),
        elif instr[0] == 'print_int':
            print ipop(),
        elif instr[0] == 'println':
            print

        elif instr[0] == 'add_int':
            ipush(ipop() + ipop())
        elif instr[0] == 'sub_int':
            ipush(- ipop() + ipop())
        elif instr[0] == 'eq_int':
            ipush(ipop() == ipop())

        elif instr[0] == 'add_str':
            spush(spop() + spop())
        elif instr[0] == 'eq_str':
            spush(spop() + spop())

        elif instr[0] == 'jmp':
            ip = instr[1]
        elif instr[0] == 'jmpz':
            if not ipop():
                ip = instr[1]

        elif instr[0] == 'end':
            break

        elif instr[0] == 'dbg':
            print len(istack), len(sstack)

        else:
            assert False, instr

if __name__ == '__main__':
    ctx = parse()
    import pprint
    pprint.pprint(ctx.code)
    pprint.pprint(ctx.labels)
    for i, instr in enumerate(translate(ctx)):
        print i, instr
    print
    #execute(ctx)
    execute_trans(ctx, translate(ctx))
    
