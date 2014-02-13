node_types = ['+', '-', '*', '/', 
              'num', 'name', 
              'stmt-seq', 'arg-list', 'arg',
              'expr-stmt', 'if-stmt', 'and', 'or', '==', '=', 'var-def', 
              'func-def', 'return', 'func-call', 'call-args']
node_code = {n:i for (i,n) in enumerate(node_types)}

def infix(tree):
    head = tree[0]
    if head in ('+', '-', '*', '/', '%', '=', 'and', 'or', '=='):
        return '(%s %s %s)' % (infix(tree[2]), head, infix(tree[3]))
    elif head in ('name', 'num'):
        return tree[1]
    else:
        return '%s(%s)' % (head, ', '.join(infix(sub) for sub in tree[1:]))

def ptree(tree, lvl=0):
    head = tree[0]
    if head in ('name', 'num'):
        print '%s%s:%r' % ('  '*lvl, head, tree[1])
    elif head in ('+', '-', '*', '/', '%', '=', 'and', 'or', '=='):
        print '%s%s:' % ('  '*lvl, head)
        for sub in tree[2:]:
            ptree(sub, lvl+1)
    else:
        print '%s%s:' % ('  '*lvl, head)
        for sub in tree[1:]:
            ptree(sub, lvl+1)
        
    
def stree(tree):
    head = tree[0]
    if head in ('+', '-', '*', '/', '%', '=', 'and', 'or', '=='):
        return '(%s %s %s)' % (head, stree(tree[2]), stree(tree[3]))
    elif head in ('name', 'num'):
        return '(%s %r)' % (tree[0], tree[1])
    else:
        return '(' + ' '.join([head] + map(stree, tree[1:])) + ')'
         
from itertools import count
label = count(100)              
def stack_code(ast):
    operators = {'+': 'add', '-': 'sub', '*': 'mul', '/': 'div', '%': 'mod', 'and': 'and', 'or': 'or', '==': 'eq'}
    if ast[0] in operators:
        stack_code(ast[2])
        stack_code(ast[3])
        print operators[ast[0]]
    elif ast[0] == 'name':
        print 'load_name', ast[1]
    elif ast[0] == 'num':
        print 'load_const', ast[1]
    elif ast[0] == 'stmt-seq':
        for sub in ast[1:]:
            stack_code(sub)
    elif ast[0] == 'expr-stmt':
        stack_code(ast[1])
        print 'pop'
    elif ast[0] == 'return':
        stack_code(ast[1])
        print 'ret'
    elif ast[0] == 'if-stmt':
        stack_code(ast[1])
        else_label = next(label)
        endif_label = next(label)
        print 'jump-if-false label%d' % else_label
        stack_code(ast[2])
        print 'jump label%d' % endif_label
        print 'label%d:  # else' % else_label
        stack_code(ast[3])
        print 'label%d:  # end if' % endif_label
    elif ast[0] == '=':
        stack_code(ast[3])
        if ast[2][0] == 'name':
            print 'store_name', ast[2][1]
        else:
            raise 'Can not assign to this expression'
    elif ast[0] == 'var-def':
        #print 'load_type', ast[2][1]
        #print 'make_var', ast[1][1]
        stack_code(ast[3])
        print 'store_name', ast[1][1]
    elif ast[0] == 'func-def':
        func_begin_label = next(label)
        func_end_label = next(label)
        print 'jump label%d' % func_end_label
        print 'label%d:  # begin func %s' % (func_begin_label, ast[1][1]) 
        for arg in reversed(ast[3][1:]):
            assert arg[0] == 'arg'
            print 'store_name', arg[1][1]
        stack_code(ast[4])
        print 'label%d: # end func %s' % (func_end_label, ast[1][1])
    elif ast[0] == 'func-call':
        args = ast[2]
        assert args[0] == 'call-args'
        for arg in ast[2][1:]:
            stack_code(arg)
        stack_code(ast[1])
        print 'call_func'
    else:
        raise Exception('Error producing stack code for %r' % ast[0])

class Enumerator(list):
    def get(self, name):
        try:
            i = self.index(name)
        except ValueError:
            i = len(self)
            self.append(name)
        return i

def store_ast(tree, nodes=None, consts=None, names=None):
    if nodes is None:
        nodes = []
        consts = Enumerator()
        names = Enumerator()

    head = tree[0]
    nodes.append(node_code[head])
    if head in ('+', '-', '*', '/', '%', 'and', 'or', '==', '=', 'arg', 'func-call'):
        store_ast(tree[1], nodes, consts, names)
        store_ast(tree[2], nodes, consts, names)
    elif head == 'name':
        nodes.append(names.get(tree[1]))
    elif head == 'num':
        nodes.append(consts.get(tree[1]))
    elif head in ('stmt-seq', 'arg-list', 'call-args'):
        nodes.append(len(tree[1:]))
        for sub in tree[1:]:
            store_ast(sub, nodes, consts, names)
    elif head == 'expr-stmt':
        store_ast(tree[1], nodes, consts, names)
    elif head == 'if-stmt':
        store_ast(tree[1], nodes, consts, names)
        store_ast(tree[2], nodes, consts, names)
        store_ast(tree[3], nodes, consts, names)
    elif head == 'var-def':
        store_ast(tree[1], nodes, consts, names)
        store_ast(tree[2], nodes, consts, names)
        store_ast(tree[3], nodes, consts, names)
    elif head == 'func-def':
        store_ast(tree[1], nodes, consts, names)
        store_ast(tree[2], nodes, consts, names)
        store_ast(tree[3], nodes, consts, names)                
        store_ast(tree[4], nodes, consts, names)  
    elif head == 'return':
        store_ast(tree[1], nodes, consts, names)              
    else:
        raise Exception('Serializer does not understand %r' % head)

    return nodes, consts, names
        
def load_ast(nodes, consts, names, pos=None):
    if pos is None:
        pos = [0]

    head = node_types[nodes[pos[0]]]
    pos[0] += 1
    if head in ('+', '-', '*', '/', '%', 'and', 'or', '==', '=', 'arg', 'func-call'):
        left = load_ast(nodes, consts, names, pos)
        right = load_ast(nodes, consts, names, pos)
        return (head, left, right)
    elif head == 'name':
        name = names[nodes[pos[0]]]
        pos[0] += 1
        return (head, name)
    elif head == 'num':
        num = consts[nodes[pos[0]]]
        pos[0] += 1
        return (head, num)
    elif head in ('stmt-seq', 'arg-list', 'call-args'):
        length = nodes[pos[0]]
        pos[0] += 1
        return (head,) + tuple([load_ast(nodes, consts, names, pos) for _ in xrange(length)])
    elif head == 'expr-stmt':
        return (head, load_ast(nodes, consts, names, pos))
    elif head == 'if-stmt':
        cond = load_ast(nodes, consts, names, pos)
        then_block = load_ast(nodes, consts, names, pos)
        else_block = load_ast(nodes, consts, names, pos)
        return (head, cond, then_block, else_block)
    elif head == 'var-def':
        name = load_ast(nodes, consts, names, pos)
        typ_ = load_ast(nodes, consts, names, pos)
        init = load_ast(nodes, consts, names, pos)
        return (head, name, typ_, init)
    elif head == 'func-def':
        name = load_ast(nodes, consts, names, pos)
        ret_type = load_ast(nodes, consts, names, pos)
        params = load_ast(nodes, consts, names, pos)
        block = load_ast(nodes, consts, names, pos)
        return (head, name, ret_type, params, block)
    elif head == 'return':
        return (head, load_ast(nodes, consts, names, pos))
    else:
        raise Exception('Deserializer does not understand %r' % head)
