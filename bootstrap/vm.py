import scopes

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