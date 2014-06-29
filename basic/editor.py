import Tkinter as tk
import tkFileDialog
import tkMessageBox
import basic
import scanner
import parser
import sys
import Queue as queue
import threading

class Editor(tk.Text):
    def __init__(self, master, source='', **conf):
        tk.Text.__init__(self, master, font=('Courier', 12), wrap='none', **conf)
        self.tag_config('keyword', foreground='blue', font=('Courier', 12, 'bold'))
        self.tag_config('error', foreground='red', font=('Courier', 12, 'underline'))
        self.tag_config('string', foreground='forestgreen', font=('Courier', 12, 'italic'))
        self.bind('<<modified>>', self.modified)
        self.bind('<KeyRelease>', self.modified)
        self.set_text(source)
        self.dirty = False
        
    def highlight(self, line):
        line_txt = self.get('%d.0' % line, '%d.end' % line)
        self.tag_remove('keyword', '%d.0' % line, '%d.end' % line)
        self.tag_remove('string', '%d.0' % line, '%d.end' % line)
        self.tag_remove('error', '%d.0' % line, '%d.end' % line)
        for token in scanner.scan(line_txt+'\n'):
            if token.type in scanner.keywords:
                self.tag_add('keyword', '%d.%d' % (line, token.start), '%d.%d' % (line, token.end))
            elif token.type == 'string':
                self.tag_add('string', '%d.%d' % (line, token.start), '%d.%d' % (line, token.end))
            elif token.type == 'error':
                self.tag_add('error', '%d.%d' % (line, token.start), '%d.%d' % (line, token.end))
                
    def highlight_all(self):
        for line in range(int(self.index('end').split('.')[0])):
            self.highlight(line)
            
    def modified(self, event):
        line = int(self.index('insert').split('.')[0])
        self.highlight(line)
        self.dirty = True
        
    def set_text(self, text):
        self.delete('1.0', 'end')
        self.insert('1.0', text)
        self.highlight_all()

    def get_text(self):
        return self.get('1.0', 'end')
    
class Console(tk.Frame):
    def __init__(self, master, **conf):
        tk.Frame.__init__(self, master, **conf)
        self.read_queue = queue.Queue()
        self.write_queue = queue.Queue()
        self.textvar = tk.StringVar()
        
        self.label = tk.Label(self, fg='white', bg='black', height=10, anchor='sw', justify='left', font=('Courier', 12))
        self.label.grid(row=1, column=1, sticky='nswe')
        self.entry = tk.Entry(self, textvariable=self.textvar, fg='white', bg='black', font=('Courier', 12))
        self.entry.grid(row=2, column=1, sticky='nswe')
        self.entry.bind('<Return>', self.on_return)
        
        self.rowconfigure(1, weight=1)
        self.columnconfigure(1, weight=1)

        self.after(300, self.check_queue)
    
    def read(self):
        return self.read_queue.get()
    
    def write(self, text):
        self.write_queue.put(text)
        
    def check_queue(self):
        while True:
            try:
                text = self.write_queue.get_nowait()
            except queue.Empty:
                break
            else:
                self.label['text'] += text
        self.after(20, self.check_queue)
            
    def on_return(self, event):
        text = self.textvar.get()+'\n'
        self.write_queue.put(text)
        self.read_queue.put(text)
        self.textvar.set('')
        
    def clear(self):
        try:
            while True:
                self.read_queue.get_nowait()
        except queue.Empty:
            pass
        try:
            while True:
                self.write_queue.get_nowait()
        except queue.Empty:
            pass
        self.label['text'] = ''
        self.textvar.set('')
                
class IDE:
    def __init__(self, root):
        self.root = root
        self.root.title('LBasic')

        menubar = tk.Menu(root)
        filemenu = tk.Menu(menubar)
        menubar.add_cascade(label='File', menu=filemenu)
        filemenu.add_command(label='New', command=self.on_file_new)
        filemenu.add_command(label='Open', command=self.on_file_open)
        filemenu.add_command(label='Save', command=self.on_file_save)
        filemenu.add_command(label='Save As', command=self.on_file_save_as)
        
        progmenu = tk.Menu(menubar)
        menubar.add_cascade(label='Program', menu=progmenu)
        progmenu.add_command(label='Run', command=self.on_run_program)
        
        self.root.config(menu=menubar)
        
        self.editor = Editor(self.root, border=0)
        
        vscroll = tk.Scrollbar(self.root, command=self.editor.yview)
        vscroll.grid(column=2, row=1, sticky='ns')
        self.editor.config(yscrollcommand=vscroll.set)
        
        hscroll = tk.Scrollbar(self.root, orient='horizontal', command=self.editor.xview)
        hscroll.grid(column=1, row=2, sticky='ew')
        self.editor.config(xscrollcommand=hscroll.set)

        self.editor.grid(column=1, row=1, sticky='nswe')
        
        self.console = Console(self.root, border=0, bg='red')
        self.console.grid(column=1, row=2, sticky='nswe')
        
        self.root.rowconfigure(1, weight=1)
        self.root.columnconfigure(1, weight=1)
        
        self.on_file_new()
        
    def check_need_save(self):
        if not self.editor.dirty:
            return True
        response = tkMessageBox.askquestion('Do you want to save changes?', 
                                            type=tkMessageBox.YESNOCANCEL, 
                                            icon=tkMessageBox.QUESTION)
        if response == tkMessageBox.YES:
            return self.on_file_save()
        elif response == tkMessageBox.NO:
            return True
        elif response == tkMessageBox.CANCEL:
            return False
        else:
            assert False

        
    def on_file_new(self):
        if not self.check_need_save():
            return
        self.filename = None
        self.root.title('LBasic - unnamed')
        self.editor.dirty = False
        self.editor.set_text('')
        
    def on_file_open(self):
        if not self.check_need_save():
            return
        filename = tkFileDialog.askopenfilename(filetypes=[('Basic File', '*.bas'), ('All Files', '*')],
                                                     parent=self.root)
        if filename:
            self.open(filename)
            
    def open(self, filename):
        with open(filename, 'r') as f:
            self.editor.set_text(f.read())
        self.editor.dirty = False
        self.filename = filename
        self.root.title('LBasic - %s' % filename)
            
    def on_file_save_as(self):
        filename = tkFileDialog.asksaveasfilename(filetypes=[('Basic File', '*.bas'), ('All Files', '*')],
                                                     parent=self.root,
                                                     initialfile=self.filename)
        if filename:
            self.save(filename)
            return True
        else:
            return False
        
    def save(self, filename):
        with open(filename, 'w') as f:
            f.write(self.editor.get_text())
        self.filename = filename
        self.editor.dirty = False
        self.root.title('LBasic - %s' % filename)
            
    def on_file_save(self):
        if not self.filename:
            return self.on_file_save_as()
        else:
            self.save(self.filename)
            return True
        
    def on_run_program(self):
        ast = parser.parse(self.editor.get_text().splitlines())
        self.console.clear()
        interp = basic.ASTInterpreter(ast, self.console.write, self.console.read)
        threading.Thread(target=interp.execute).start()    
        
def main():
    root = tk.Tk()
    ide = IDE(root)
    if len(sys.argv) == 2:
        ide.open(sys.argv[1])
    root.mainloop()
             
if __name__ == '__main__':
    main()