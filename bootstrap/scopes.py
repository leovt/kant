from collections import namedtuple
import operator
from pprint import pprint

Symbol = namedtuple('Symbol', 'token, type, value')

BUILTIN_TYPE_INT =   '[builtin type integer]'
BUILTIN_TYPE_FLOAT = '[builtin type float]'
BUILTIN_TYPE_TYPE =  '[builtin type type]'
BUILTIN_TYPE_BOOL =  '[builtin type bool]'
BUILTIN_TYPE_ASSIGNMENT = '[builtin type assignment]'

def error(*args):
    raise NotImplementedError

class Scope:
    def __init__(self, parent):
        self.names = {}
        self.parent = parent
        
    def new_child(self):
        return Scope(parent=self)
    
    def resolve(self, name):
        scope = self
        while scope:
            if name in scope.names:
                return scope.names[name]
            scope = scope.parent
                
    def add_name(self, name, token, typ, value=None):
        print 'registering name %r of type %r' % (name, typ)
        if self.resolve(name):
            error('Redefining name %s is not permitted' % name, token)
        else:
            self.names[name] = Symbol(token, typ, value)

def build(ast):
    builtins = Scope(None)
    builtins.add_name('int',   None, BUILTIN_TYPE_TYPE, BUILTIN_TYPE_INT)
    builtins.add_name('float', None, BUILTIN_TYPE_TYPE, BUILTIN_TYPE_FLOAT)
    builtins.add_name('type',  None, BUILTIN_TYPE_TYPE, BUILTIN_TYPE_TYPE)
    builtins.add_name('bool',  None, BUILTIN_TYPE_TYPE, BUILTIN_TYPE_BOOL)
    builtins.add_name('true',  None, BUILTIN_TYPE_BOOL, True)
    builtins.add_name('false', None, BUILTIN_TYPE_BOOL, False)
    code = []
    walk(ast, builtins, code)
    return code
    

from itertools import count
label = count(100)

def walk(ast, scope, code):
    operators = {'+': 'add', '-': 'sub', 
                 '*': 'mul', '/': 'div', '%': 'mod', 
                 'and': 'and', 'or': 'or', 
                 '==': 'eq'}
    def emit(*args):
        code.append(args)
        
    if ast[0] in operators:
        assert False, 'operators must be visited by walk_expression %r' % ast[0]
        walk(ast[2], scope, code)
        walk(ast[3], scope, code)
        emit(operators[ast[0]])
        
    elif ast[0] == 'func-call':
        assert False, 'function calls must be visited by walk_expression %r' % ast[0]
        if ast[1][0] == 'name':
            symbol = scope.resolve(ast[2])
        else:
            error('currently only named funcitons can be called', ast)
        
        #walk(ast[2], scope, code)
        emit('call', symbol.value)
        
    elif ast[0] == 'name':
        assert False, 'name must be visited by walk_expression'
        typ = scope.resolve(ast[1])
        if typ is None:
            error('using undeclared name %r' % ast[1], ast)
        else:
            emit('load_name', ast[1])
    elif ast[0] == 'num':
        emit('load_const', ast[1])
    elif ast[0] == 'stmt-seq':
        child = scope.new_child()
        for sub in ast[1:]:
            walk(sub, child, code)
    elif ast[0] == 'call-args':
        for sub in ast[1:]:
            walk(sub, scope, code)
    elif ast[0] == 'expr-stmt':
        code.extend(walk_expression(ast[1], scope).code)
        emit('pop')
    elif ast[0] == 'return':
        # TODO: check return type
        code.extend(walk_expression(ast[1], scope).code)
        emit('ret')
    elif ast[0] == 'if-stmt':
        else_label = next(label)
        end_label = next(label)
        condition = walk_expression(ast[1], scope)
        if condition.type != BUILTIN_TYPE_BOOL:
            error('if-condition must be boolean')
        code.extend(condition.code)
        emit('jump_if_false', else_label)
        walk(ast[2], scope, code)
        emit('jump', end_label)
        emit('label', else_label)
        walk(ast[3], scope, code)
        emit('label', end_label)
    elif ast[0] == '=':
        walk(ast[3], scope, code)
        if ast[2][0] == 'name':
            typ = scope.resolve(ast[2][1])
            emit('type-check', typ)
            emit('store_name', ast[2][1])
    elif ast[0] == 'var-def':
        # find the type
        declared_type = get_type(ast[2], scope)
        expression = walk_expression(ast[3], scope)
        code.extend(expression.code)
        if expression.type != declared_type:
            error('Declared type %r does not match expression type %r' % (declared_type, expression.type), ast[1])
        # create the variable
        emit('make_var', ast[1][1], declared_type)
        # evaluate the expression before adding the name to the scope
        
        walk(ast[3], scope, code)
        # add the name to the scope and store the result
        scope.add_name(ast[1][1], ast[1], declared_type)
        emit('store_name', ast[1][1])
    elif ast[0] == 'func-def':
        func_label = next(label)
        scope.add_name(ast[1][1], ast[1], get_function_type(ast, scope), func_label)
        child = scope.new_child()
        for arg in ast[3][1:]:
            child.add_name(arg[1][1], arg[1], get_type(arg[2], scope))
            
        emit('label', func_label)

        walk(ast[4], child, code)
        if code[-1][0] != 'ret':
            error('Function %r does not end in a return statement' % ast[1][1], ast[1])
    else:
        assert False, 'unhandled node %r' % ast[0]

def get_type(ast, scope):
    # ast must be a type-expression
    if ast[0] == 'name':
        symbol = scope.resolve(ast[1])
        if symbol is None:
            error('Type %r is not defined' % ast[1], ast)
        elif symbol.type != BUILTIN_TYPE_TYPE:
            error('Expected a type, got %r' % symbol.name, ast)
        else:
            pprint ((get_type, ast, symbol))
            return symbol.value
    else:
        error('Expected a type, got %s' % ast[0], None)
        
def get_function_type(ast, scope):
    # ast must be a funciton definition
    argtypes = []
    for arg in ast[3][1:]:
        argtypes.append(get_type(arg[2], scope))
    ret_type = get_type(ast[2], scope)
    pprint (argtypes)
    return ('func-type', ret_type, tuple(argtypes))   

ExpressionType = namedtuple('ExpressionType', 'compile_time, type, value, code')

def walk_expression(ast, scope):
    def const_code(val):
        return [('load_const', val)]
    
    if ast[0] == 'name':
        symbol = scope.resolve(ast[1])
        if symbol is None:
            error('Name %r is not defined' % ast[1], ast)
            symbol = Symbol(ast, None, None)
        return ExpressionType(False, symbol.type, None, [('load_name', ast[1])])
    elif ast[0] == 'num':
        if '.' in ast.lexeme:
            try:
                val = float(ast.lexeme)
            except ValueError:
                error('illegal float point literal %r' % ast.lexeme, ast)
                val = 0.0
            return ExpressionType(True, BUILTIN_TYPE_FLOAT, val, const_code(val))
        else:
            try:
                val = int(ast.lexeme, 10)
            except ValueError:
                error('illegal integer literal %r' % ast.lexeme, ast)
                val = 0
            return ExpressionType(True, BUILTIN_TYPE_INT, val, const_code(val))
    elif ast[0] in ('+', '-', '*', '/', '%', '=='):
        op1 = walk_expression(ast[2], scope)
        op2 = walk_expression(ast[3], scope)
        if op1.type != op2.type:
            error('Operands must be of the same types', ast[1])

        if ast[0] == '==':
            ret_type = BUILTIN_TYPE_BOOL
        else:
            ret_type = op1.type    
            if op1.type not in (BUILTIN_TYPE_INT, BUILTIN_TYPE_FLOAT):
                error('Operands must be of type int or float', ast[1])
        
        if op1.compile_time and op2.compile_time:
            val = {'+': operator.add,
                   '-': operator.sub,
                   '*': operator.mul,
                   '/': operator.div,
                   '%': operator.mod,
                   '==': operator.eq}[ast[0]](op1.value, op2.value)
            return ExpressionType(True, ret_type, val, const_code(val))
        else:
            opcode = {'+': 'add',
                      '-': 'sub',
                      '*': 'mul',
                      '/': 'div',
                      '%': 'mod',
                      '==': 'eq'}[ast[0]]
                      
            return ExpressionType(False, ret_type, None, op1.code + op2.code + [opcode])
    elif ast[0] == '=':
        op1 = walk_expression(ast[2], scope)
        op2 = walk_expression(ast[3], scope)
        if op1.type != op2.type:
            error('Can not assign expression of type %r to type %r' % (op1.type, op2.type), ast[1])
        # must be generalized to lvalues instead of names
        if ast[2][0] == 'name':
            return ExpressionType(False, BUILTIN_TYPE_ASSIGNMENT, None, op1.code + [('load_name', ast[2][1])])
        else:
            error('Illegal target of assignment', ast[2])

    elif ast[0] == 'func-call':
        func = walk_expression(ast[1], scope)
        code = []
        ast_args = ast[2][1:]
        arg_types = func.type[2]
        if len(ast_args) != len(arg_types):
            error('number of arguments mismatch in function call, expected %d but got %d arguments' 
                  % (len(arg_types), len(ast_args)), ast[1])            
        for arg_ast, arg_type in zip(ast_args, arg_types):
            arg = walk_expression(arg_ast, scope)
            if arg.type != arg_type:
                error('type mismatch in function call, expected %r but got %r'
                      % (arg_type, arg.type), ast[1])
            code.extend(arg.code)        
        if not func.compile_time:
            error('can not call expression', ast[1])
        code.append(('call', func.value))
        return ExpressionType(False, func.type[1], None, code)
    else:
        assert False, 'unhandled expression node %r' % ast[0]
        
         
    
def interprete(code):
    pass
    