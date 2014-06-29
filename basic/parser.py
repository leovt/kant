import scanner

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

def parse(lines):
    context = ASTContext()

    lastno = 0
    
    for line in lines:
        if not line.endswith('\n'):
            line += '\n'
        tokens = [t for t in scanner.scan(line) if t.type != 'whitespace']
        if tokens[0].type == 'end_of_line':
            continue
        if tokens[0].type != 'integer':
            error('line must start with an integer line number')
        lineno = int(tokens[0].text)
        if lineno <= lastno:
            error('line numbers not strictly increasing: %d follows %d' % (lineno, lastno))
        context.labels[lineno] = len(context.code)
        statement = stmt(tokens[1:], lineno, context)
        if statement:
            context.code.append(statement)
        lastno = lineno
    return context

def error(msg):
    print msg
    raise Exception(msg)

def stmt(tokens, lineno, context):
    if tokens[0].type == 'DIM':
        if tokens[1].type != 'identifier':
            error('line %d identifier expected' % (lineno, ))
        if tokens[2].type != 'AS':
            error('line %d "AS" expected' % (lineno, ))
        if tokens[3].type == 'INTEGER':
            v_id = context.nb_int
            context.nb_int += 1
            v_type = 'int'
        elif tokens[3].type == 'STRING':
            v_id = context.nb_str
            context.nb_str += 1
            v_type = 'str'
        else:
            error('line %d: unknown type %s' %( lineno, tokens[3]))
        if tokens[4].type != 'end_of_line':
            error('expecting end of line')
        context.symbols[tokens[1].text] = v_type, v_id
        return ()

    elif tokens[0].type == 'INPUT':
        expression, t = expr(tokens, 1, lineno, context)
        if tokens[t].type != ';':
            error('INPUT expecting ; after message')
        if tokens[t+1].type != 'identifier':
            error('INPUT expecting variable name after ";"')
        if tokens[t+1].text not in context.symbols:
            error('Undefined variable %r for INPUT' % tokens[t+1].text)
        if tokens[t+2].type != 'end_of_line':
            error('expecting end of line')
        v_type, v_id = context.symbols[tokens[t+1].text]
        return ('input', expression, v_type, v_id)

    elif tokens[0].type == 'IF':
        cond, t = expr(tokens, 1, lineno, context)
        if tokens[t].type != 'THEN':
            error('IF expecting THEN after the condition expression')
        return ('if', cond, stmt(tokens[t+1:], lineno, context))

    elif tokens[0].type == 'PRINT':
        result = ['print']
        pos = 1
        while True:
            expression, pos = expr(tokens, pos, lineno, context)
            result.append(expression)
            if tokens[pos].type == ';':
                pos += 1
            elif tokens[pos].type == 'end_of_line':
                break
            else:
                error('PRINT expecting expressions separated by ";"')
        return tuple(result)

    elif tokens[0].type == 'GOTO':
        if tokens[1].type != 'integer':
            error('GOTO: expecting integer line number.')
        if tokens[2].type != 'end_of_line':
            error('expecting end of line')
        return ('goto', int(tokens[1].text))

    elif tokens[0].type == 'END':
        return ('end',)

    elif tokens[0].type == 'LET':
        if tokens[1].type != 'identifier':
            error('LET expecting a variable name')
        if tokens[1].text not in context.symbols:
            error('Assigning to undefined variable %r' % tokens[1].text)
        v_type, v_id = context.symbols[tokens[1].text]
        if tokens[2].type != 'operator' or tokens[2].text != '=':
            error('LET expected = sign for assignment')
        expression, pos = expr(tokens, 3, lineno, context)
        if tokens[pos].type != 'end_of_line':
            error('expecting end of line')
        return ('assign', v_type, v_id, expression)

    else:
        error('unrecognized statement %s on line %d' % (' '.join(t.text for t in tokens), lineno))

def expr(tokens, position, lineno, context):
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
        type_r, typed_op = ops.get((type_a, op, type_b), (None, None))
        if type_r is None:
            error('invalid use of operator types %s %s %s on line %d' % (type_a, op, type_b, lineno))
        else:
            return (typed_op, type_r, a, b)

    while tokens[position].type not in (';', 'THEN', 'end_of_line'):
        t = tokens[position]
        if t.type == 'integer':
            result.append(('cst', 'int', context.add_const('int', int(t.text))))
        elif t.type == 'string':
            assert t.text[-1] == '"'
            result.append(('cst', 'str', context.add_const('str', t.text[1:-1].replace('""', '"'))))
        elif t.type == 'identifier':
            if t.text in symbols:
                v_type, v_id = symbols[t.text]
            else:
                error('Undefined variable %r' % t.text)
            result.append(('var', v_type, v_id))
        elif t.type == 'operator':
            while stack and op[stack[-1]] > op[t.text]:
                s = stack.pop()
                b = result.pop()
                a = result.pop()
                
                result.append(operation(s, a, b))
            stack.append(t.text)
        elif t.type == '(':
            stack.append('(')
        elif t.type == ')':
            s = stack.pop()
            while s != '(':
                b = result.pop()
                a = result.pop()
                result.append(operation(s, a, b))
                s = stack.pop()
        else:
            error('invalid token in expression %r' % t.text)
        position = position + 1
        
    while stack:
        s = stack.pop()
        b = result.pop()
        a = result.pop()
        result.append(operation(s, a, b))

    if len(result) != 1:
        error('incomplete expression')

    return result.pop(), position

