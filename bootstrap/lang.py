import lexer
import parser
import ast
import scopes
import sys
from pprint import pprint

tokens = lexer.tokenize('''
(a=b)(c=d);
a = (b = c);
a(b(c));
a(b)(c)(d);
f(1,2,3, 4);
def a:int = 4;
b = 4 + a;
if 6-5 == 4 and a == b {
hallo;
}
else
{
hello;
a + b-c*2;
/* kommentar */
}
def foo(a:int, b:int):int {
    return a + b;
}
7*8;
if 1 {
// kommentar
hello;}

''')


parser.init(tokens)

tree = parser.program()
print
ast.ptree(tree)

def compile(source, filename):  # @ReservedAssignment
    tokens = lexer.tokenize(source)
    parser.init(tokens)
    tree = parser.program()
    def error(message, token, level='Error'):
        if token is None:
            # should be avoided for good error messages
            sys.stderr.write('%s %s\n' % (level, message))
        else:
            lines = source.splitlines()
            sys.stderr.write('%s\n%s^\n' % (lines[token.line_no-1], ' '*(token.col_no-1)))
            sys.stderr.write('%s:%d:%d: %s %s\n' % (filename, token.line_no, token.col_no, level, message))
    scopes.error = error
    
    print 'S-expr:', ast.stree(tree)
    print
    ast.ptree(tree)
    print
    code, globls = scopes.build(tree)
    for name, symbol in globls.names.items():
        print name, symbol
    print
    for line in code:
        print '\t'.join(map(str, line))
    return code, globls


source = '''

def fib(n:int):int
{
    def b:int = 1;
    def c:float = 1.0;
    if n==0 { return 0; }
    if n==1 { return 1; }
    return fib(n-1) + fib(n-2);
}

def main():int
{
    def result:int = fib(10);
    return 0;
}

'''
    
code, names = compile(source, '<source>')

class VM:
    def __init__(self, code, start_label):
        self.code = code
        self.labels = {}
        for i,c in enumerate(code):
            if c[0] == 'label':
                self.labels[c[1]] = i
        self.ip = self.labels[start_label]
        self.estack = []
        self.fstack = [(None, None)]
        self.frame = {}
        
        
    def pop(self, expected_type):
        type, value = self.estack.pop()
        assert type == expected_type
        return value
    
    def push(self, type, value):
        self.estack.append((type, value))
        
    def execute(self):
        while self.ip is not None:
            instr = self.code[self.ip]
            #raw_input('%d %s' % ( self.ip, instr ))
            self.ip += 1
            if instr[0] == '#' or instr[0] == 'label':
                pass
            elif instr[0] == 'load_const':
                self.push(instr[2], instr[1])
            elif instr[0] == 'load_local':
                self.push(instr[2], self.frame[instr[3]])
            elif instr[0] == 'store_local':
                self.frame[instr[3]] = self.pop(instr[2])
                print '%s = %s' % (instr[1], self.frame[instr[3]])
            elif instr[0] == 'call':
                #print 'before calling', self.fstack, self.ip
                self.fstack.append((self.ip, self.frame))
                self.frame = {}
                self.ip = self.labels[instr[1]]
                #print 'after calling', self.fstack, self.ip
            elif instr[0] == 'ret':
                #print 'before returning', self.fstack, self.ip
                self.ip, self.frame = self.fstack.pop()
                #print 'after returning', self.fstack, self.ip
            elif instr[0] == 'eq':
                a = self.pop(instr[1])
                b = self.pop(instr[1])
                self.push(scopes.BUILTIN_TYPE_BOOL, a==b)
            elif instr[0] == 'jump_if_false':
                cond = self.pop(scopes.BUILTIN_TYPE_BOOL)
                if not cond:
                    self.ip = self.labels[instr[1]]
            elif instr[0] == 'sub':
                a = self.pop(instr[1])
                b = self.pop(instr[1])
                self.push(instr[1], b-a)
            elif instr[0] == 'add':
                a = self.pop(instr[1])
                b = self.pop(instr[1])
                self.push(instr[1], b+a)
            else:
                assert False, 'instruction %r not implemented' % instr[0]

vm = VM(code, names.names['main'].value)
print vm.labels
vm.execute() 
print vm.frame, vm.estack      