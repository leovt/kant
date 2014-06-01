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

    def translate_instr(self, instr):
        '''translate an AST instruction into TAC'''
        if instr[0] == 'input':
            prompt = self.translate_expr(instr[1])
            self.code.append(('print' + instr[1][1][0], prompt))
            self.code.append(('input' + instr[2][0], 'var_%s_%d' % (instr[2], instr[3])))
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
                self.code.append(('print' + ex[1][0], sym))
            self.code.append(('prints', 'newline'))
        elif instr[0] == 'end':
            self.code.append(('end',))
        else:
            assert False, instr

    def translate_expr(self, expr, name=None):
        '''translate an expression AST into TAC'''
        if expr[0] in operations:
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
        while True:
            line = self.code[pc]
            #print pc, line, symbols
            pc += 1
            if line[0] == 'prints':
                sys.stdout.write(symbols[line[1]])
            elif line[0] == 'inputs':
                symbols[line[1]] = raw_input()
            elif line[0] == 'printi':
                sys.stdout.write(str(symbols[line[1]]))
            elif line[0] == 'inputi':
                symbols[line[1]] = int(raw_input())
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
        str_ref = set()
        int_var = set()
    
        for sym, val in self.consts.items():
            if isinstance(val, str):
                str_ref.add(sym)
            else:
                int_var.add(sym)
    
        for line in self.code:
            if line[0] == 'prints':
                assert line[1] in str_ref
            elif line[0] == 'inputs':
                str_ref.add(line[1])
            elif line[0] == 'printi':
                assert line[1] in int_var
            elif line[0] == 'inputi':
                int_var.add(line[1])
            elif line[0] in ('add_int', 'sub_int', 'eq_int'):
                assert line[2] in int_var
                assert line[3] in int_var
                int_var.add(line[1])
            elif line[0] == 'cat_str':
                assert line[2] in str_ref
                assert line[3] in str_ref
                str_ref.add(line[1])
            elif line[0] == 'eq_str':
                assert line[2] in str_ref
                assert line[3] in str_ref
                int_var.add(line[1])
            elif line[0] == 'end':
                pass
            elif line[0] in ('jmpT', 'jmpz'):
                assert line[2] in int_var
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
        
        asm.data()
        
        for sym, val in self.consts.items():
            if isinstance(val, str):
                asm.label(asm.local('_const_'+sym))
                asm.bytes([ord(x) for x in val+'\0'])
                
        for sym, val in self.consts.items():
            if not isinstance(val, str):
                asm.label(asm.local(sym))
                asm.dword(val)
                
        for sym in int_var:
            if sym not in self.consts:
                asm.label(asm.local(sym))
                asm.dword(0)
                
        for sym, val in self.consts.items():
            if isinstance(val, str):
                asm.label(asm.local(sym))
                asm.dword(asm.local('_const_'+sym))
                
        for sym in str_ref:
            if sym not in self.consts:
                asm.label(asm.local(sym))
                asm.dword(0)
    
        asm.code()
        asm.label(asm.cname('main'))
    
        for line in self.code:
            if line[0] == 'prints':
                asm.mov(asm.eax, asm.local(line[1]))
                asm.push(asm.eax)
                asm.call(asm.cname('prints'))
                asm.pop(asm.eax)
            elif line[0] == 'inputs':
                asm.call(asm.cname('inputs'))
                asm.mov(asm.local(line[1]), asm.eax)
            elif line[0] == 'printi':
                asm.mov(asm.eax, asm.local(line[1]))
                asm.push(asm.eax)
                asm.call(asm.cname('printi'))
                asm.pop(asm.eax)
            elif line[0] == 'cat_str':
                asm.mov(asm.eax, asm.local(line[3]))
                asm.push(asm.eax)
                asm.mov(asm.eax, asm.local(line[2]))
                asm.push(asm.eax)
                asm.call(asm.cname('cat_str'))
                asm.mov(asm.local(line[1]), asm.eax)
                asm.pop(asm.eax)
                asm.pop(asm.eax)
            elif line[0] == 'eq_str':
                asm.mov(asm.eax, asm.local(line[3]))
                asm.push(asm.eax)
                asm.mov(asm.eax, asm.local(line[2]))
                asm.push(asm.eax)
                asm.call(asm.cname('eq_str'))
                asm.mov(asm.local(line[1]), asm.eax)
                asm.pop(asm.eax)
                asm.pop(asm.eax)
            elif line[0] == 'inputi':
                asm.call(asm.cname('inputi'))
                asm.mov(asm.local(line[1]), asm.eax)
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


