'''This module implements the three-adress-code intermediate representation'''

import sys
import itertools

operations = {
    'add_int',
    'sub_int',
    'mul_int',
    'div_int',
    'eq_int',
    'eq_str',
    'cat_str'}

class TAC:
    def __init__(self):
        self.code = []
        self.consts = {}
        self.gen_temp_symbol = ('tmp%d' % i for i in itertools.count(1))
        self.gen_const_symbol = ('const%d' % i for i in itertools.count(1))
        self.gen_label = ('label%d' % i for i in itertools.count(1))

    @classmethod
    def fromast(cls, ast_context):
        '''create a TAC representation of the AST given'''
        self = cls()
        self.consts.update(('const_int_%d' % i, v) for i,v in enumerate(ast_context.const_int))
        self.consts.update(('const_str_%d' % i, v) for i,v in enumerate(ast_context.const_str))
        self.consts['newline'] = "\n"

        lines = {value:key for key,value in ast_context.labels.items()}

        for ln, instr in enumerate(ast_context.code):
            if ln in lines:
                self.code.append(('label', 'line%d' % lines[ln]))
            self.translate_instr(instr)
        return self
    
    def dump(self):
        for name, value in self.consts.items():
            print '%s = %r' % (name, value)
        print
        for number, line in enumerate(self.code):
            print '\t'.join([str(number)] + [str(item) for item in line])

    def translate_instr(self, instr):
        '''translate an AST instruction into TAC'''
        if instr[0] == 'input':
            prompt = self.translate_expr(instr[1])
            self.code.append(('libcall', 1, None, 'print' + instr[1][1][0], prompt))
            self.code.append(('libcall', 0, 'var_%s_%d' % (instr[2], instr[3]), 'input' + instr[2][0]))
        elif instr[0] == 'assign':
            self.translate_expr(instr[3], 'var_%s_%d' % (instr[1], instr[2]))
        elif instr[0] == 'if':
            cond = self.translate_expr(instr[1])
            endif = next(self.gen_label)
            self.code.append(('jmpz', endif, cond))
            self.translate_instr(instr[2])
            self.code.append(('label', endif))
        elif instr[0] == 'goto':
            self.code.append(('jmp', 'line%d' % instr[1]))
        elif instr[0] == 'print':
            for ex in instr[1:]:
                sym = self.translate_expr(ex)
                self.code.append(('libcall', 1, None, 'print' + ex[1][0], sym))
            self.code.append(('libcall', 1, None, 'prints', 'newline'))
        elif instr[0] == 'end':
            self.code.append(('end',))
        else:
            assert False, instr

    def translate_expr(self, expr, name=None):
        '''translate an expression AST into TAC'''
        if expr[0] in ('eq_str', 'cat_str'):
            op1 = self.translate_expr(expr[2])
            op2 = self.translate_expr(expr[3])
            if name is None:
                name = next(self.gen_temp_symbol)
            self.code.append(('libcall', 2, name, expr[0], op1, op2))
            return name
        elif expr[0] in operations:
            op1 = self.translate_expr(expr[2])
            op2 = self.translate_expr(expr[3])
            if name is None:
                name = next(self.gen_temp_symbol)
            self.code.append((expr[0], name, op1, op2))
            return name
        elif expr[0] == 'var':
            return 'var_%s_%d' % (expr[1], expr[2])
        elif expr[0] == 'cst':
            return 'const_%s_%d' % (expr[1], expr[2])
        else:
            assert False, expr

    def interpreter(self):
        '''an interpreter for the TAC'''
        labels = { line[1]:index for index, line in enumerate(self.code) if line[0] == 'label' }
        symbols = dict(self.consts)
        pc = 0
        
        lib = {
            'prints': sys.stdout.write,
            'printi': lambda i: sys.stdout.write(str(i)),
            'inputs': raw_input,
            'inputi': lambda: int(raw_input()),
            'cat_str': lambda a,b: a+b,
            'eq_str': lambda a,b: int(a==b)}
        
        while True:
            line = self.code[pc]
            #print pc, line, symbols
            pc += 1
            if line[0] == 'libcall':
                nb_arg = line[1]
                ret_var = line[2]
                libfunc = line[3]
                args = [symbols[x] for x in line[4:4+nb_arg]]
                ret = lib[libfunc](*args)
                symbols[ret_var] = ret
            elif line[0] == 'eq_int':
                symbols[line[1]] = int(symbols[line[2]] == symbols[line[3]])
            elif line[0] == 'sub_int':
                symbols[line[1]] = symbols[line[2]] - symbols[line[3]]
            elif line[0] == 'cat_str':
                symbols[line[1]] = symbols[line[2]] + symbols[line[3]]
            elif line[0] == 'eq_str':
                symbols[line[1]] = symbols[line[2]] == symbols[line[3]]
            elif line[0] == 'end':
                break
            elif line[0] == 'jmpT':
                if symbols[line[2]]:
                    pc = labels[line[1]]
            elif line[0] == 'jmpz':
                if not symbols[line[2]]:
                    pc = labels[line[1]]
            elif line[0] == 'jmp':
                pc = labels[line[1]]
            elif line[0] == 'label':
                pass
            else:
                assert False, line

    def compile(self, asm):
        '''compile the TAC to x86 assemply language.
        
        the assembly output is written by an ASM class which knows about assembler syntax'''

        symbols = set()

        for sym, val in self.consts.items():
            symbols.add(sym)
    
        for line in self.code:
            if line[0] == 'libcall':
                for arg in line[4:]:
                    assert arg in symbols
                if line[2] is not None:
                    symbols.add(line[2])
            elif line[0] in operations:
                assert line[2] in symbols
                assert line[3] in symbols
                symbols.add(line[1])
            elif line[0] == 'end':
                pass
            elif line[0] in ('jmpT', 'jmpz'):
                assert line[2] in symbols
            elif line[0] == 'jmp':
                pass
            elif line[0] == 'label':
                pass
            else:
                assert False, line
    
        asm.prologue()
        
    
        asm.extproc('printi')
        asm.extproc('prints')
        asm.extproc('inputi')
        asm.extproc('inputs')
        
        asm.rodata()
        for sym, val in self.consts.items():
            if isinstance(val, str):
                asm.label(asm.local('_const_'+sym))
                asm.bytes([ord(x) for x in val+'\0'])
                
        asm.data()
        for sym, val in self.consts.items():
            if not isinstance(val, str):
                asm.label(asm.local(sym))
                asm.dword(val)
            else:
                asm.label(asm.local(sym))
                asm.dword(asm.local('_const_'+sym))
             
        for sym in symbols:
            if sym not in self.consts:
                asm.label(asm.local(sym))
                asm.dword(0)
   
        asm.code()
        asm.label(asm.cname('main'))
    
        for line in self.code:
            if line[0] == 'libcall':
                nb_arg = line[1]
                ret_var = line[2]
                libfunc = line[3]
                for arg in reversed(line[4:4+nb_arg]):
                    asm.push(asm.local(arg))
                asm.call(asm.cname(libfunc))
                if ret_var is not None:
                    asm.mov(asm.local(ret_var), asm.eax)
                for arg in line[4:4+nb_arg]:
                    asm.pop(asm.eax)
            elif line[0] == 'eq_int':
                asm.mov(asm.eax, asm.local(line[2]))
                asm.mov(asm.ecx, asm.imm(0))
                asm.cmp(asm.eax, asm.local(line[3]))
                asm.sete(asm.reg('cl')) #cl = 1 if zero_flag else 0
                asm.mov(asm.local(line[1]), asm.ecx)
            elif line[0] == 'sub_int':
                asm.mov(asm.eax, asm.local(line[2]))
                asm.sub(asm.eax, asm.local(line[3]))
                asm.mov(asm.local(line[1]), asm.eax)
            elif line[0] == 'end':
                pass
            elif line[0] == 'jmpT':
                asm.mov(asm.eax, asm.imm(0))
                asm.cmp(asm.eax, asm.local(line[2]))
                asm.jne(asm.local(line[1]))
            elif line[0] == 'jmpz':
                asm.mov(asm.eax, asm.imm(0))
                asm.cmp(asm.eax, asm.local(line[2]))
                asm.jmpz(asm.local(line[1]))
            elif line[0] == 'jmp':
                asm.jmp(asm.local(line[1]))
            elif line[0] == 'label':
                asm.label(asm.local(line[1]))       
            else:
                assert False, line
        asm.ret()
        asm.epilogue()


