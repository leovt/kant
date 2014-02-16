import lexer
import parser
import ast
import scopes
import sys

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
    code = scopes.build(tree)
    print
    for c in code:
        print '\t'.join(map(str,c))      
            
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
    fib(10);
    return 0;
}

'''
    
compile(source, '<source>')