import sys
import struct
import parser

operations = {'add_int', 'sub_int', 'mul_int', 'div_int', 'eq_int', 'eq_str', 'cat_str'}
opnames = [
 'end',
 'add_int',
 'sub_int',
 'mul_int',
 'div_int',
 'eq_int',
 'cat_str',
 'eq_str',
 'print_int',
 'print_str',
 'println',
 'hasarg',
 'load_const_int',
 'load_int',
 'input_int',
 'save_int',
 'load_const_str',
 'load_str',
 'input_str',
 'save_str',
 'jmp',
 'jmpz'
 ]
opcodes = {name:i for i,name in enumerate(opnames)}

class BCContext():
    @classmethod
    def from_ast(cls, ast_context):
        self = cls()
        self.code = []
        self.jmps = []

        jpos = {}
    
        for ln, instr in enumerate(ast_context.code):
            jpos[ln] = len(self.code)
            self.translate_instr(instr)
            #code.append(('dbg',))
        for codepos, label in self.jmps:
            ah, al = divmod(jpos[ast_context.labels[label]], 256)
            self.code[codepos+1] = al
            self.code[codepos+2] = ah
            
        del self.jmps
        self.nb_int = ast_context.nb_int
        self.nb_str = ast_context.nb_str
        self.const_int = ast_context.const_int
        self.const_str = ast_context.const_str        
        return self    

    @classmethod
    def from_file(cls, infile):
        self = cls()
        code_length, self.nb_int, self.nb_str, nb_const_int, nb_const_str = struct.unpack('<HHHHH', infile.read(10))
        self.const_int = [
            struct.unpack('<l', infile.read(4))[0] for _ in xrange(nb_const_int)]
        self.const_str = []
        for _ in xrange(nb_const_str):
            length = struct.unpack('<L', infile.read(4))[0]
            self.const_str.append(infile.read(length))
        self.code = []
        for _ in xrange(code_length):
            self.code.append(struct.unpack('<B', infile.read(1))[0])
        return self

    
    def translate_expr(self, expr):
        if expr[0] in operations:
            self.translate_expr(expr[2])
            self.translate_expr(expr[3])
            self.emit(expr[0])
        elif expr[0] == 'var':
            self.emit('load_'+expr[1], expr[2])
        elif expr[0] == 'cst':
            self.emit('load_const_'+expr[1], expr[2])
        else:
            assert False, expr

        
    def translate_instr(self, instr):
        if instr[0] == 'input':
            self.translate_expr(instr[1])
            self.emit('print_' + instr[1][1])
            self.emit('input_' + instr[2], instr[3])
        elif instr[0] == 'assign':
            self.translate_expr(instr[3])
            self.emit('save_' + instr[1], instr[2])
        elif instr[0] == 'if':
            self.translate_expr(instr[1])
            jmp_instr = len(self.code)
            self.emit('jmpz', 0xdead)
            self.translate_instr(instr[2])
            ah, al = divmod(len(self.code), 256)
            self.code[jmp_instr+1] = al
            self.code[jmp_instr+2] = ah
        elif instr[0] == 'goto':
            self.jmps.append((len(self.code), instr[1]))
            self.emit('jmp', 0xdead)
        elif instr[0] == 'print':
            for ex in instr[1:]:
                self.translate_expr(ex)
                self.emit('print_' + ex[1])
            self.emit('println')
        elif instr[0] == 'end':
            self.emit('end')
        else:
            assert False, instr
            
    def emit(self, mnemonic, arg=None):
        self.code.append(opcodes[mnemonic])
        if arg is not None:
            ah, al = divmod(arg, 256)
            self.code.append(al)
            self.code.append(ah)

    
    def disassemble(self):
        ip = 0
        while ip<len(self.code):
            bytecode = self.code[ip]
            mnemonic = opnames[bytecode]
            ip += 1
            if bytecode > opcodes['hasarg']:
                arg = self.code[ip] + 256 * self.code[ip+1]
                ip += 2
                print '%3d: %s %d' % (ip, mnemonic, arg)
            else:
                print '%3d: %s' % (ip, mnemonic)
                
    def serialize(self, outfile):
        outfile.write(struct.pack('<HHHHH', len(self.code), self.nb_int, self.nb_str, len(self.const_int), len(self.const_str)))
        for i in self.const_int:
            outfile.write(struct.pack('<l', i))
        for s in self.const_str:
            outfile.write(struct.pack('<L', len(s)))
            outfile.write(s)
        for c in self.code:
            outfile.write(struct.pack('<B', c))
            
            
def run_bytecode(bc_context):
    ip = 0
    istack = []
    sstack = []
    ipush = istack.append
    ipop = istack.pop
    spush = sstack.append
    spop = sstack.pop
    integers = [0] * bc_context.nb_int
    strings = [''] * bc_context.nb_str

    while True:
        bytecode = bc_context.code[ip]
        mnemonic = opnames[bytecode]
        ip += 1
        arg = None
        if bytecode > opcodes['hasarg']:
            arg = bc_context.code[ip] + 256 * bc_context.code[ip+1]
            ip += 2
        if mnemonic == 'load_int':
            ipush(integers[arg])
        elif mnemonic == 'load_str':
            spush(strings[arg])
            
        elif mnemonic == 'load_const_int':
            ipush(bc_context.const_int[arg])
        elif mnemonic == 'load_const_str':
            spush(bc_context.const_str[arg])

        elif mnemonic == 'input_int':
            integers[arg] = int(raw_input())
        elif mnemonic == 'input_str':
            strings[arg] = raw_input()
            
        elif mnemonic == 'save_int':
            integers[arg] = ipop()
        elif mnemonic == 'save_str':
            strings[arg] = spop()
            
        elif mnemonic == 'print_str':
            sys.stdout.write(spop())
        elif mnemonic == 'print_int':
            sys.stdout.write(str(ipop()))
        elif mnemonic == 'println':
            print

        elif mnemonic == 'add_int':
            tmp = ipop()
            ipush(ipop() + tmp)
            
        elif mnemonic == 'sub_int':
            tmp = ipop()
            ipush(ipop() - tmp)
            
        elif mnemonic == 'eq_int':
            ipush(int(ipop() == ipop()))

        elif mnemonic == 'cat_str':
            tmp = spop()
            spush(spop() + tmp)
        elif mnemonic == 'eq_str':
            ipush(int(spop() == spop()))

        elif mnemonic == 'jmp':
            ip = arg
        elif mnemonic == 'jmpz':
            if not ipop():
                ip = arg

        elif mnemonic == 'end':
            break

        elif mnemonic == 'dbg':
            print len(istack), len(sstack)

        else:
            assert False, mnemonic


def write_opcodes_h():     
    with open('opcodes.h', 'w') as f:
        f.write('static const char* opnames[] = {\n' + 
                ',\n'.join('"%s"' % name for name in opnames) + 
                '\n};\n')
        f.write('enum opcodes{')
        for i, name in enumerate(opnames):
            f.write('    op_%s = %d,\n' % (name, i))
        f.write('};\n')
write_opcodes_h()

def main(fname):
    if fname.endswith('.bac'):
        with open(fname, 'rb') as infile:
            bc_ctx = BCContext.from_file(infile)
    else:
        with open(fname, 'r') as infile:
            ast_ctx = parser.parse(infile)
        bc_ctx = BCContext.from_ast(ast_ctx)
        with open('test.bac', 'wb') as outfile:
            bc_ctx.serialize(outfile)        
    run_bytecode(bc_ctx)

if __name__ == '__main__':
    main(sys.argv[1])
