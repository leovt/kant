from collections import namedtuple

keywords = ['DIM', 'AS', 'INTEGER', 'STRING', 'INPUT', 'IF', 'THEN', 'GOTO', 'PRINT', 'END', 'FLOAT', 'LET']

Token = namedtuple('Token', 'type, start, end, message')

def scan(source):
    pos = 0
    while pos < len(source):
        token = anytoken(pos, source)
        yield token
        pos = token.end

def anytoken(pos, source):
    if source[pos] in '0123456789':
        return number(pos, pos+1, source)
    elif source[pos] == '.':
        return decimal_point(pos, pos+1, source)
    elif source[pos] in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ_':
        return identifier_or_keyword(pos, pos+1, source)
    elif source[pos] == '"':
        return string(pos, pos+1, source)
    elif source[pos] == '\n':
        return Token('end_of_line', pos, pos+1, '')
    elif source[pos] in ' \t':
        return whitespace(pos, pos+1, source)
    elif source[pos] in '+-*/=<>':
        return Token('operator', pos, pos+1, '')
    elif source[pos] in '();:':
        return Token(source[pos], pos, pos+1, '')
    else:
        return Token('error', pos, pos+1, 'illegal character')
        
def number(start, pos, source):
    while source[pos] in '0123456789':
        pos += 1
    if source[pos] == '.':
        return decimal_number(start, pos+1, source)
    elif source[pos] == 'E':
        return e_number(start, pos+1, source)
    else:
        return Token('integer', start, pos, '')

def decimal_point(start, pos, source):
    if source[pos] in '0123456789':
        return decimal_number(start, pos+1, source)
    else:
        return Token('error', start, pos, 'unexpected decimal point (not part of a number)')

def decimal_number(start, pos, source):
    while source[pos] in '0123456789':
        pos += 1
    if source[pos] == 'E':
        return e_number(start, pos+1, source)
    else:
        return Token('float', start, pos, '')
    
def e_number(start, pos, source):
    if source[pos] in '+-':
        pos += 1
    # not an elif, formally we change to state e_number_after_sign
    if source[pos] in '0123456789':
        return exponent_number(start, pos+1, source)
    else:
        return Token('error', start, pos, 'illegal number literal')
    
def exponent_number(start, pos, source):
    while source[pos] in '0123456789':
        pos += 1
    return Token('float', start, pos, '')
        
def identifier_or_keyword(start, pos, source):
    while source[pos] in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ_0123456789':
        pos += 1
    if source[start:pos] in keywords:
        return Token(source[start:pos], start, pos, '')
    else:
        return Token('identifier', start, pos, '')
    
def string(start, pos, source):
    while source[pos] not in '\n"':
        pos += 1
    if source[pos] == '\n':
        return Token('error', start, pos, 'end of line in a string literal')
    elif source[pos] == '"':
        return string_quote(start, pos+1, source)
    else:
        assert False, 'impossible to reach this point! source[pos] = %r' % source[pos]
    
def string_quote(start, pos, source):
    if source[pos] == '"':
        return string(start, pos+1, source)
    else:
        return Token('string', start, pos, '')
    
def whitespace(start, pos, source):
    while source[pos] in ' \t':
        pos += 1
    return Token('whitespace', start, pos, '')
    
def test_numbers():
    token = anytoken(0, '1\n')
    assert token.type == 'integer'
    assert token.end == 1
    
    token = anytoken(0, '2.\n')
    assert token.type == 'float'
    assert token.end == 2
    
    token = anytoken(0, '.3E-4\n')
    assert token.type == 'float'
    assert token.end == 5
    
    token = anytoken(4, 'abcd4E3\n')
    assert token.type == 'float'
    assert token.end == 7
    
    token = anytoken(0, '.b\n')
    assert token.type == 'error'
    
    token = anytoken(0, '4E-end')
    assert token.type == 'error', token

    # the scanner should find a float here. 
    # the error of multiple decimal points will need to be 
    # found by the parser which will not allow float tokens 
    # repeating.
    token = anytoken(0, '0.1.2.3.4\n')
    assert token.type == 'float'
    assert token.end == 3
    
def test_strings():
    token = anytoken(0, '"hello"\n')
    assert token.type == 'string'
    assert token.end == 7
    
    token = anytoken(0, '"text in ""quotes""."\n')
    assert token.type == 'string'
    assert token.end == 21
    
    token = anytoken(0, '""""\n')
    assert token.type == 'string'
    assert token.end == 4
    
    token = anytoken(0, '"""quote"""\n')
    assert token.type == 'string'
    assert token.end == 11
    
    token = anytoken(0, '"he\nllo"\n')
    assert token.type == 'error'
    
    token = anytoken(0, '"hello""\n')
    assert token.type == 'error'
    
def test_identifiers():
    token = anytoken(0, 'IF\n')
    assert token.type == 'IF'
    
    token = anytoken(0, '_IF\n')
    assert token.type == 'identifier'
    
    token = anytoken(0, 'AB0_9C_\n')
    assert token.type == 'identifier'
    assert token.end == 7
    
def test_scanner():
    result = [token.type for token in scan('10 PRINT  "Hello World"\n')]
    assert result == ['integer', 'whitespace', 'PRINT', 'whitespace', 'string', 'end_of_line'], result
    
    result = [token.type for token in scan('10 LET I=10\n20 PRINT I -1\n')]
    assert result == ['integer', 'whitespace', 'LET', 'whitespace', 'identifier', 'operator', 'integer', 'end_of_line',
                      'integer', 'whitespace', 'PRINT', 'whitespace', 'identifier', 'whitespace', 'operator', 'integer', 'end_of_line'], result
    
if __name__ == '__main__':
    test_numbers()
    test_strings()
    test_identifiers()
    test_scanner()