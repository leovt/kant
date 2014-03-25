import scopes

LOAD_CONST = 1    #const
LOAD_LOCAL = 2    #name
STORE_LOCAL = 3   #name
CALL = 4          #ip
RETURN = 5        #type
EQUALS = 6        #type
JUMP_IF_FALSE = 7 #ip
JUMP = 8          #ip
SUBTRACT = 9     #type
ADD = 10          #type



class Bytecode:
    def __init__(self, code, start_label):
        code = [('jump', start_label)] + code
        label_definitions = {}

        self.label_uses = label_uses = []
        self.constants = constants = []
        self.code = bytecode = []
        self.names = names = []
        self.types = types = []
        
        def add(item, bucket):
            if item in bucket:
                return bucket.index(item)
            else:
                bucket.append(item)
                return len(bucket)-1
        
        for instr in code:
            if instr[0] == '#':
                pass
            elif instr[0] == 'label':
                label_definitions[instr[1]] = len(bytecode)
            elif instr[0] == 'load_const':
                bytecode.append(LOAD_CONST)
                c = add((instr[2], instr[1]), constants)
                bytecode.append(c % 256)
                bytecode.append(c // 256)
            elif instr[0] == 'load_local':
                bytecode.append(LOAD_LOCAL)
                c = add((instr[1], instr[2], instr[3]), names)
                bytecode.append(c % 256)
                bytecode.append(c // 256)
            elif instr[0] == 'store_local':
                bytecode.append(STORE_LOCAL)
                c = add((instr[1], instr[2], instr[3]), names)
                bytecode.append(c % 256)
                bytecode.append(c // 256)
            elif instr[0] == 'call':
                bytecode.append(CALL)
                label_uses.append((instr[1], len(bytecode)))
                bytecode.append(0)
                bytecode.append(0)
            elif instr[0] == 'ret':
                bytecode.append(RETURN)
                c = add(instr[1], types)
                bytecode.append(c % 256)
                bytecode.append(c // 256)
            elif instr[0] == 'eq':
                bytecode.append(EQUALS)
                c = add(instr[1], types)
                bytecode.append(c % 256)
                bytecode.append(c // 256)
            elif instr[0] == 'jump_if_false':
                bytecode.append(JUMP_IF_FALSE)
                label_uses.append((instr[1], len(bytecode)))
                bytecode.append(0)
                bytecode.append(0)
            elif instr[0] == 'jump':
                bytecode.append(JUMP)
                label_uses.append((instr[1], len(bytecode)))
                bytecode.append(0)
                bytecode.append(0)
            elif instr[0] == 'sub':
                bytecode.append(SUBTRACT)
                c = add(instr[1], types)
                bytecode.append(c % 256)
                bytecode.append(c // 256)
            elif instr[0] == 'add':
                bytecode.append(ADD)
                c = add(instr[1], types)
                bytecode.append(c % 256)
                bytecode.append(c // 256)
            else:
                assert False, 'instruction %r not implemented' % instr[0]
        for label, use in label_uses:
            target = label_definitions[label]
            bytecode[use] = target % 256
            bytecode[use+1] = target // 256    

class VM:
    def __init__(self, code, start_label):
        self.bytecode = Bytecode(code, start_label)
        self.ip = 0 
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
            instr = self.bytecode.code[self.ip]
            arg = self.bytecode.code[self.ip+1] + self.bytecode.code[self.ip+2]*256
            #raw_input('%d %s %s' % ( self.ip, instr, arg ))
            self.ip += 3
            if instr == LOAD_CONST:
                type, value = self.bytecode.constants[arg]
                self.push(type, value)
            elif instr == LOAD_LOCAL:
                name, type, varid = self.bytecode.names[arg]
                self.push(type, self.frame[varid])
            elif instr == STORE_LOCAL:
                name, type, varid = self.bytecode.names[arg]
                self.frame[varid] = self.pop(type)
                print '%s = %s' % (name, self.frame[varid])
            elif instr == CALL:
                #print 'before calling', self.fstack, self.ip
                self.fstack.append((self.ip, self.frame))
                self.frame = {}
                self.ip = arg
                #print 'after calling', self.fstack, self.ip
            elif instr == RETURN:
                #print 'before returning', self.fstack, self.ip
                self.ip, self.frame = self.fstack.pop()
                #print 'after returning', self.fstack, self.ip
            elif instr == EQUALS:
                type = self.bytecode.types[arg]
                a = self.pop(type)
                b = self.pop(type)
                self.push(scopes.BUILTIN_TYPE_BOOL, a==b)
            elif instr == JUMP_IF_FALSE:
                cond = self.pop(scopes.BUILTIN_TYPE_BOOL)
                if not cond:
                    self.ip = arg
            elif instr == JUMP:
                self.ip = arg
            elif instr == SUBTRACT:
                type = self.bytecode.types[arg]
                a = self.pop(type)
                b = self.pop(type)
                self.push(type, b-a)
            elif instr == ADD:
                type = self.bytecode.types[arg]
                a = self.pop(type)
                b = self.pop(type)
                self.push(type, b+a)
            else:
                assert False, 'instruction %r not implemented' % instr