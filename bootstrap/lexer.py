import sys
from collections import namedtuple

Token = namedtuple('Token', 'type, lexeme, filename, line_no, col_no')

keywords = set(['if', 'else', 'and', 'or', 'def', 'return'])

operators = set(['+', '-', '*', '/', '%', '<', '>', '=',
                 '+=', '-=', '*=', '/=', '%=',
                 '==', '<=', '>=', '!='])

def tokenize(chars, filename='<filename>'):
    s = None
    chars = iter(chars)
    
    class char_pos:
        line_no = 1
        col_no = 0
        char = None
        
    class start:
        line_no = 0
        col_no = 0
            
    def error(msg):
        sys.stderr.write('%s:%d:%d: %s\n' % (filename, start.line_no, start.col_no, msg))

    def advance():
        c = next(chars, '')
        char_pos.char = c
        if c == '\n':
            char_pos.line_no += 1
            char_pos.col_no = 0
        elif c:
            char_pos.col_no += 1
            
    advance()
            
    while True:
        c = char_pos.char
        if s==None:
            t = c
            start.line_no = char_pos.line_no
            start.col_no = char_pos.col_no
            
            if c == '':
                yield Token('end', '', filename, char_pos.line_no, char_pos.col_no)
            elif c in ' \t\n':
                pass
            elif c in '+-*/%<>=!':
                s = 'op'
            elif c in '_abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ':
                s = 'name'
            elif c in '(){}[];:,':
                yield Token(t, t, filename, start.line_no, start.col_no)
            elif c in '0123456789':
                s = 'num'
            elif c == '.':
                s = '.num'
            else:
                error('Illegal character %r' % c)
            advance()
        elif s=='op':
            if c in '+-*/%<>=':
                t += c
                advance()
                if t[-2:] == '/*':
                    s = 'comment'
                elif t[-2:] == '//':
                    s = 'line_comment'
            elif t in operators:
                yield Token(t, t, filename, start.line_no, start.col_no)
                s = None
            else:
                error('illegal operator %r' % t) 
                s = None
        elif s=='name':
            if c in '_abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789':
                t += c
                advance()
            else:
                if t in keywords:
                    yield Token(t, t, filename, start.line_no, start.col_no)
                else:
                    yield Token('name', t, filename, start.line_no, start.col_no)
                s = None
        elif s=='num':
            if c in '0123456789':
                t += c
                advance()
            elif c in 'eE':
                t += c
                s = 'nume'
                advance()
            elif c in '.':
                t += c
                s = 'num.'
                advance()
            else:
                yield Token('num', t, filename, start.line_no, start.col_no)
                s = None
        elif s=='num.':
            if c in '0123456789':
                t += c
                advance()
            elif c in 'eE':
                t += c
                s = 'nume'
                advance()
            elif c in '.':
                error('invalid number, two decimal points')
                s = None
                advance()
            else:
                yield Token('num', t, filename, start.line_no, start.col_no)
                s = None
            
        elif s=='nume':
            if c in '+-':
                t += c
                s = 'numex'
                advance()
            elif c in '0123456789':
                t += c
                s = 'numexp'
                advance()
            else:
                error('invalid number, missing exponent after "E"')
                s = None
                advance()
                
        elif s=='numex':
            if c in '0123456789':
                t += c
                s = 'numexp'
                advance()
            else:
                error('invalid number, missing exponent after "E"')
                s = None
                advance()

        elif s=='numexp':
            if c in '0123456789':
                t += c
                s = 'numexp'
                advance()
            else:
                yield Token('num', t, filename, start.line_no, start.col_no)
                s = None

        elif s=='.num':
            if c in '0123456789':
                t += c
                s = 'num.'
                advance()
            else:
                error('invalid token . (not part of a number)')
                s = None
                advance()

        elif s=='comment':
            if c == '*':
                s = 'comment*'
                advance()
            else:
                advance()

        elif s=='comment*':
            if c == '/':
                s = None
                advance()
            elif c == '*':
                advance()
            else:
                s = 'comment'
                advance()

        elif s=='line_comment':
            if c == '\n':
                s = None
            advance()

        else:
            assert False, 'Illegal State %r' % s
