from collections import namedtuple
from itertools import count
import operator

Symbol = namedtuple('Symbol', 'token, type, alloc, value, varid, scope')

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

variable = count(10000)

class Scope:
    def __init__(self, parent, frame):
        self.names = {}
        self.parent = parent
        self.frame = frame
        
    def new_child(self):
        return Scope(self, self.frame)
    
    def new_function(self):
        return Scope(self, [])
    
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
                varid = next(variable)
                self.names[name] = symb = Symbol(token, typ, allocate, value, varid, self)
                self.frame.append((varid, typ))
            else:
                self.names[name] = symb = Symbol(token, typ, allocate, value, None, self)
            return symb
    
    
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
    builtins = Scope(None, [])
    builtins.add_name('int',   None, BUILTIN_TYPE_TYPE, 0, BUILTIN_TYPE_INT)
    builtins.add_name('float', None, BUILTIN_TYPE_TYPE, 0, BUILTIN_TYPE_FLOAT)
    builtins.add_name('type',  None, BUILTIN_TYPE_TYPE, 0, BUILTIN_TYPE_TYPE)
    builtins.add_name('bool',  None, BUILTIN_TYPE_TYPE, 0, BUILTIN_TYPE_BOOL)
    builtins.add_name('byte',  None, BUILTIN_TYPE_TYPE, 0, BUILTIN_TYPE_BOOL)
    builtins.add_name('true',  None, BUILTIN_TYPE_BOOL, 0, True)
    builtins.add_name('false', None, BUILTIN_TYPE_BOOL, 0, False)
    
    code_blocks = []
    globals = builtins.new_function()
    walk(ast, globals, None, None, code_blocks)
    code = [x for block in code_blocks for x in block]
    return code, globals
    

label = count(100)

def walk(ast, scope, current_function, current_code_block, code_blocks):
    def emit(*args):
        current_code_block.append(args)

    if ast[0] == 'expr-stmt':
        expr = walk_expression(ast[1], scope)
        current_code_block.extend(expr.code)
        emit('pop', expr.type)
    elif ast[0] == 'return':
        expr = walk_expression(ast[2], scope)
        func = scope.resolve(current_function)
        if func.type[1] != expr.type:
            error('function %r is declared as returning %r, but returns %r.' % (current_function, func.type[1], expr.type), 
                  ast[1])
        current_code_block.extend(expr.code)
        emit('ret', expr.type)
    elif ast[0] == 'stmt-seq':
        for stmt in ast[1:]:
            walk(stmt, scope, current_function, current_code_block, code_blocks)
    elif ast[0] == 'if-stmt':
        else_label = next(label)
        end_label = next(label)
        condition = walk_expression(ast[1], scope)
        if condition.type != BUILTIN_TYPE_BOOL:
            error('if-condition must be boolean')
        current_code_block.extend(condition.code)
        emit('jump_if_false', else_label)
        walk(ast[2], scope, current_function, current_code_block, code_blocks)
        emit('jump', end_label)
        emit('label', else_label)
        walk(ast[3], scope, current_function, current_code_block, code_blocks)
        emit('label', end_label)
    elif ast[0] == '=':
        walk(ast[3], scope, current_code_block, code_blocks)
        if ast[2][0] == 'name':
            symb = scope.resolve(ast[2][1])
            emit('type-check', symb)
            if symb.scope.frame is scope.frame:
                op = 'store_local'
            else:
                op = 'store_name'
            emit(op, ast[2][1], symb.type, symb.varid)
    elif ast[0] == 'var-def':
        # find the type
        declared_type = get_type(ast[2], scope)
        # evaluate the expression before adding the name to the scope
        expression = walk_expression(ast[3], scope)
        if expression.type != declared_type:
            error('Declared type %r does not match expression type %r' % (declared_type, expression.type), ast[1])

        # add the name to the scope and store the result
        symb = scope.add_name(ast[1][1], ast[1], declared_type, 1, None)
        current_code_block.extend(expression.code)
        emit('store_local', ast[1][1], symb.type, symb.varid)
    elif ast[0] == 'func-def':
        func_label = next(label)
        scope.add_name(ast[1][1], ast[1], get_function_type(ast, scope), 0, func_label)
        child = scope.new_function()
        child_code = []

        child_code.append(('#', 'begin of function %s' % ast[1][1]))
        child_code.append(('label', func_label))

        for arg in ast[3][:0:-1]:
            symb = child.add_name(arg[1][1], arg[1], get_type(arg[2], scope), 1, None)
            child_code.append(('store_local', arg[1][1], symb.type, symb.varid))
        
        walk(ast[4], child, ast[1][1], child_code, code_blocks)
        
        if child_code[-1][0] != 'ret':
            error('Function %r does not end in a return statement' % ast[1][1], ast[1])
        
        child_code.append(('#', 'end of function %s' % ast[1][1]))
        code_blocks.append(child_code)
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
            symbol = Symbol(ast, None, None, None, None, scope)
        if symbol.value is not None:
            return ExpressionType(True, symbol.type, symbol.value, [])
        if symbol.scope.frame == scope.frame:
            op = 'load_local'
        else:
            op = 'load_name'
        return ExpressionType(False, symbol.type, None, [(op, ast[1], symbol.type, symbol.varid)])
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
            return ExpressionType(False, ret_type, None, op1.code + op2.code + [(opcode, op1.type)])
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
            
        
    