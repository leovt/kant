class RegMixin(object):
    @property
    def eax(self):
        return self.reg('eax')
    @property
    def ebx(self):
        return self.reg('ebx')
    @property
    def ecx(self):
        return self.reg('ecx')
    @property
    def edx(self):
        return self.reg('edx')
    @property
    def esp(self):
        return self.reg('esp')
    @property
    def ebp(self):
        return self.reg('ebp')


class GASM(RegMixin):
    def __init__(self, fname):
        self.f = open(fname, 'w')
        
    def close(self):
        self.f.close()
        
    def emit(self, line):
        self.f.write(line + '\n')
    
    def cname(self, name):
        return name
    
    def reg(self, name):
        return '%%%s' % name
    
    def label(self, name):
        return '$%s' % name
    
    def imm(self, value):
        return '$%s' % value
    
    def local(self, name):
        return '.L%s' % name
    
    def bytes(self, values):
        self.emit('.byte %s' % ', '.join(str(c) for c in values))
    
    def dword(self, value):
        self.emit('.long %s' % value)
    
    def extproc(self, name):
        pass
    
    def prologue(self):
        self.emit('.global %s' % self.cname('main'))
        
    def epilogue(self):
        pass
    
    def code(self):
        self.emit('.text')
    
    def data(self):
        self.emit('.data')
    
    def label(self, name):
        self.emit('%s:' % name)
        
    def call(self, name):
        self.emit('call %s' % name)
        
    def mov(self, dst, src):
        self.emit('mov %s, %s' % (src, dst))
        
    def sub(self, dst, src):
        self.emit('sub %s, %s' % (src, dst))
        
    def cmp(self, dst, src):
        self.emit('sub %s, %s' % (src, dst))

    def push(self, src):
        self.emit('push %s' % src)
        
    def pop(self, dst):
        self.emit('pop %s' % dst)
        
    def sete(self, dst):
        self.emit('sete %s' % dst)
        
    def jmp(self, label):
        self.emit('jmp %s' % label)

    def jne(self, label):
        self.emit('jnz %s' % label)
        
    def jmpz(self, label):
        self.emit('jz %s' % label)
        
    def ret(self):
        self.emit('ret')
        