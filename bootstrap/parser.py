import sys

def init(token_stream, filename_ = '<filename>'):
    global tokens
    global filename
    filename = filename_
    tokens = iter(token_stream)
    consume()

def consume():
    global next_token
    next_token = next(tokens)
    
def error(msg, token):
    sys.stderr.write('%s:%d:%d: %s\n' % (token.filename, token.line_no, token.col_no, msg))
    return ('error', token, msg)
    
def expect(token_type):
    if next_token.type == token_type:
        ret = next_token
        consume()
        return ret
    else:
        return error('Expected %r, got %r' % (token_type, next_token.lexeme), next_token)

def program():
    result = statement_seq()
    if next_token.type == 'end':
        return result
    else:
        return error('expected end of file, got %r' % (next_token,))

def name():
    n = expect('name')
    return n

def number():
    n = expect('num')
    return n

def definition():
    expect('def')
    n = name()
    if next_token.type == '(':
        p = argument_list()
        expect(':')
        t = type_expression()
        b = block()
        return ('func-def', n, t, p, b)
    else:
        expect(':')
        t = type_expression()
        expect('=')
        e = expression()
        expect(';')
        return ('var-def', n, t, e)

def argument_list():
    expect('(')
    args = []
    while next_token.type != ')':
        n = name()
        expect(':')
        t = type_expression()
        args.append(('arg', n, t))
        if next_token.type == ',':
            consume()
        else:
            break
    expect(')')
    return ('arg-list',) + tuple(args)

def type_expression():
    # for now the only way to specify a type is by its name
    return name()

def block():
    expect('{')
    result = statement_seq()
    expect('}')
    return result

def statement_seq():
    result = []
    while next_token.type not in ('}', 'end'):
        result.append(statement())
    return ('stmt-seq',) + tuple(result)

def statement():
    if next_token.type == ';':
        consume()
        return ('nop',)
    elif next_token.type == 'if':
        consume()
        condition = expression()
        if_block = block()
        if next_token.type == 'else':
            consume()
            else_block = block()
        else:
            else_block = ('stmt-seq',)
        return ('if-stmt', condition, if_block, else_block)
    elif next_token.type == 'def':
        return definition()
    elif next_token.type == 'return':
        tok = next_token
        consume()
        expr = expression()
        expect(';')
        return ('return', tok, expr)
    else:
        result = ('expr-stmt', expression())
        expect(';')
        return result

def expression():
    result = disjunction()
    if next_token.type in ('=', '+=', '*=', '/=', '%='):
        op = next_token
        consume()
        return (op.type, op, result, disjunction())
    else:
        return result
    
def disjunction():
    result = conjunction()
    while next_token.type == 'or':
        op = next_token
        consume()
        result = (op.type, op, result, conjunction())
    return result
     
def conjunction():
    result = comparison()
    while next_token.type == 'and':
        op = next_token
        consume()
        result = (op.type, op, result, comparison())
    return result
     
def comparison():
    result = factor()
    if next_token.type == '==':
        op = next_token
        consume()
        return (op.type, op, result, factor())
    return result

def factor():
    result = term()
    while next_token.type in ('+', '-'):
        op = next_token
        consume()
        result = (op.type, op, result, term())
    return result

def term():
    result = function_call()
    assert result
    while next_token.type in ('*', '/', '%'):
        op = next_token
        consume()
        result = (op.type, op, result, function_call())
        assert result
    assert result
    return result

def call_args():
    expect('(')
    params = []
    while next_token.type != ')':
        params.append(expression())
        if next_token.type == ',':
            consume()
        else:
            expect(')')
            break
    return ('call-args',) + tuple(params)

def function_call():
    result = primary()
    while next_token.type == '(':
        result = ('func-call', result, call_args())
    return result

def primary():
    if next_token.type == 'name':
        return name()
    elif next_token.type == 'num':
        return number()
    elif next_token.type == '(':
        consume()
        result = expression()
        expect(')')
        return result
    else:
        return error('Expected a name, number, or (, got %r' % (next_token.lexeme,), next_token)

        
