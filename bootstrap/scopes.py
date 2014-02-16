from collections import namedtuple
import operator

Symbol = namedtuple('Symbol', 'token, type, alloc, value, adress')

BUILTIN_TYPE_INT =   '[builtin type integer]'
BUILTIN_TYPE_FLOAT = '[builtin type float]'
BUILTIN_TYPE_TYPE =  '[builtin type type]'
BUILTIN_TYPE_BOOL =  '[builtin type bool]'
BUILTIN_TYPE_BYTE =  '[builtin type byte]'
BUILTIN_TYPE_ASSIGNMENT = '[builtin type assignment]'

def error(*args):
    raise NotImplementedError

def sizeof(typ):
    return {BUILTIN_TYPE_INT: 4,
            BUILTIN_TYPE_FLOAT: 8,
            BUILTIN_TYPE_BOOL: 1,
            BUILTIN_TYPE_BYTE: 1}[typ]

class Scope:
    def __init__(self, parent):
        self.names = {}
        self.parent = parent
        self._size = None
        
    @property
    def size(self):
        if self._size is not None:
            return self._size
        else:
            return self.parent.size
        
    @size.setter
    def size(self, val):
        if self._size is not None:
            self._size = val
        else:
            self.parent.size = val
        
    def new_child(self):
        return Scope(self)
    
    def new_function(self):
        child = Scope(self)
        child._size = 0
        return child
    
    def resolve(self, name):
        scope = self
        while scope:
            if name in scope.names:
                return scope.names[name]
            scope = scope.parent
                
    def add_name(self, name, token, typ, allocate, value):
        #print 'registering name %r of type %r' % (name, typ)
        if self.resolve(name):
            error('Redefining name %s is not permitted' % name, token)
        else:
            if allocate:
                self.names[name] = Symbol(token, typ, allocate, value, self.size)
                self.size += sizeof(typ)
            else:
                self.names[name] = Symbol(token, typ, allocate, value, None)
    
    
class CodeConstants():
    def __init__(self):
        self.constants = OrderedDict()
        self.const_ptr = 0
    
    def rel_adress(self, value, size):
        if value not in self.constants:
            self.constants[value] = (self.const_ptr, size)
            self.const_ptr += size
        return self.constants[value][0]

def build(ast):
    builtins = Scope(None)
    builtins.add_name('int',   None, BUILTIN_TYPE_TYPE, 0, BUILTIN_TYPE_INT)
    builtins.add_name('float', None, BUILTIN_TYPE_TYPE, 0, BUILTIN_TYPE_FLOAT)
    builtins.add_name('type',  None, BUILTIN_TYPE_TYPE, 0, BUILTIN_TYPE_TYPE)
    builtins.add_name('bool',  None, BUILTIN_TYPE_TYPE, 0, BUILTIN_TYPE_BOOL)
    builtins.add_name('byte',  None, BUILTIN_TYPE_TYPE, 0, BUILTIN_TYPE_BOOL)
    builtins.add_name('true',  None, BUILTIN_TYPE_BOOL, 0, True)
    builtins.add_name('false', None, BUILTIN_TYPE_BOOL, 0, False)
    
    code = []
    walk(ast, builtins.new_function(), None, code)
    return code
    

from itertools import count
label = count(100)

def walk(ast, scope, current_function, code):
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
        assert False, 'num must be visited by walk_expression'
        emit('load_const', ast[1])
    elif ast[0] == 'stmt-seq':
        child = scope.new_child()
        for sub in ast[1:]:
            walk(sub, child, current_function, code)
    elif ast[0] == 'call-args':
        assert False, 'call-args must be visited by walk_expression'
        for sub in ast[1:]:
            walk(sub, scope, current_function, code)
    elif ast[0] == 'expr-stmt':
        expr = walk_expression(ast[1], scope)
        code.extend(expr.code)
        emit('pop')
    elif ast[0] == 'return':
        expr = walk_expression(ast[2], scope)
        func = scope.resolve(current_function)
        if func.type[1] != expr.type:
            error('function %r is declared as returning %r, but returns %r.' % (current_function, func.type[1], expr.type), 
                  ast[1])
        code.extend(expr.code)
        emit('ret')
    elif ast[0] == 'if-stmt':
        else_label = next(label)
        end_label = next(label)
        condition = walk_expression(ast[1], scope)
        if condition.type != BUILTIN_TYPE_BOOL:
            error('if-condition must be boolean')
        code.extend(condition.code)
        emit('jump_if_false', else_label)
        walk(ast[2], scope, current_function, code)
        emit('jump', end_label)
        emit('label', else_label)
        walk(ast[3], scope, current_function, code)
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
        
        expr = walk_expression(ast[3], scope)
        # add the name to the scope and store the result
        scope.add_name(ast[1][1], ast[1], declared_type, 1, None)
        code.extend(expr.code)
        emit('store_name', ast[1][1])
    elif ast[0] == 'func-def':
        func_label = next(label)
        scope.add_name(ast[1][1], ast[1], get_function_type(ast, scope), 0, func_label)
        child = scope.new_function()

        for arg in ast[3][1:]:
            child.add_name(arg[1][1], arg[1], get_type(arg[2], scope), 1, None)
            
        emit('label', func_label)

        walk(ast[4], child, ast[1][1], code)
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
            #pprint ((get_type, ast, symbol))
            return symbol.value
    else:
        error('Expected a type, got %s' % ast[0], None)
        
def get_function_type(ast, scope):
    # ast must be a funciton definition
    argtypes = []
    for arg in ast[3][1:]:
        argtypes.append(get_type(arg[2], scope))
    ret_type = get_type(ast[2], scope)
    #pprint (argtypes)
    return ('func-type', ret_type, tuple(argtypes))   

ExpressionType = namedtuple('ExpressionType', 'compile_time, type, value, code')

def walk_expression(ast, scope):
    def const_code(val, typ):
        return [('load_const', val, typ)]
    
    if ast[0] == 'name':
        symbol = scope.resolve(ast[1])
        if symbol is None:
            error('Name %r is not defined' % ast[1], ast)
            symbol = Symbol(ast, None, None)
        if symbol.value is not None:
            return ExpressionType(True, symbol.type, symbol.value, [])
        return ExpressionType(False, symbol.type, None, [('load_name', ast[1], scope)])
    elif ast[0] == 'num':
        if '.' in ast.lexeme:
            try:
                val = float(ast.lexeme)
            except ValueError:
                error('illegal float point literal %r' % ast.lexeme, ast)
                val = 0.0
            return ExpressionType(True, BUILTIN_TYPE_FLOAT, val, const_code(val, BUILTIN_TYPE_FLOAT))
        else:
            try:
                val = int(ast.lexeme, 10)
            except ValueError:
                error('illegal integer literal %r' % ast.lexeme, ast)
                val = 0
            return ExpressionType(True, BUILTIN_TYPE_INT, val, const_code(val, BUILTIN_TYPE_INT))
    elif ast[0] in ('+', '-', '*', '/', '%', '=='):
        op1 = walk_expression(ast[2], scope)
        op2 = walk_expression(ast[3], scope)
        if op1.type != op2.type:
            error('Operands must be of the same types', ast[1])

        if ast[0] == '==':
            ret_type = BUILTIN_TYPE_BOOL
        else:
            ret_type = op1.type    
            if op1.type not in (BUILTIN_TYPE_INT, BUILTIN_TYPE_FLOAT, BUILTIN_TYPE_BYTE):
                error('Operands must be of type int, byte or float', ast[1])
        
        if op1.compile_time and op2.compile_time:
            val = {'+': operator.add,
                   '-': operator.sub,
                   '*': operator.mul,
                   '/': operator.div,
                   '%': operator.mod,
                   '==': operator.eq}[ast[0]](op1.value, op2.value)
            return ExpressionType(True, ret_type, val, const_code(val, ret_type))
        else:
            opcode = {'+': 'add',
                      '-': 'sub',
                      '*': 'mul',
                      '/': 'div',
                      '%': 'mod',
                      '==': 'eq'}[ast[0]]
            opcode += {BUILTIN_TYPE_INT: 'i',
                       BUILTIN_TYPE_FLOAT: 'f',
                       BUILTIN_TYPE_BOOL: 'B',
                       BUILTIN_TYPE_BYTE: 'b'}[op1.type]
            return ExpressionType(False, ret_type, None, op1.code + op2.code + [(opcode,)])
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
        
         
from collections import OrderedDict  
            
        
    