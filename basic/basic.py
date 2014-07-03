import parser
import subprocess
import asmw
import tac
import bytecode

if __name__ == '__main__':
    with open('test.bas', 'r') as infile:
        ast_ctx = parser.parse(infile)
        
    
    tac_ctx = tac.TAC.fromast(ast_ctx)
    
    #tac_ctx.dump()
    tac_ctx.interpreter()
    
    asm = asmw.GASM('test.s')
    tac_ctx.compile(asm)
    asm.close()
    #pprint.pprint(ast_ctx.code)
    subprocess.call(['gcc', '-m32', 'test.s', 'lib.c', '-o', 'test'])
    subprocess.call(['test'], executable='./test')
    
    bc_ctx = bytecode.BCContext.from_ast(ast_ctx)
    #interpreter = ASTInterpreter(ast_ctx)
    #interpreter.execute()
    
    #print bc_ctx.code
    #bc_ctx.disassemble()
    
    with open('test.bac', 'wb') as outfile:
        bc_ctx.serialize(outfile)
        
    with open('test.bac', 'rb') as infile:
        bc_ctx = bytecode.BCContext.from_file(infile)
    
    bytecode.run_bytecode(bc_ctx)
    