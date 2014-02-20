import fcntl
import os
import subprocess, codecs
import logging
from tkinter import *
from tkinter import messagebox
import webbrowser
from helpers import set_options
from counterpartyd.lib import config

def non_block_read(output):
    fd = output.fileno()
    fl = fcntl.fcntl(fd, fcntl.F_GETFL)
    fcntl.fcntl(fd, fcntl.F_SETFL, fl | os.O_NONBLOCK)
    try:
        return output.read()
    except:
        return ""


class TextWidgetOut(object):
    def __init__(self, text_widget, stream):
        self.text_widget = text_widget
        self.stream = stream
        self.buffer = "";
        self.buffer_size = 150

    def write(self, txt):
        clean_txt = TextWidgetOut.clean_out(txt)
        if clean_txt is not None:

            if self.buffer!="":
                self.text_widget.delete("1.0", END)

            self.buffer += clean_txt           
            if len(self.buffer.split("\n"))>self.buffer_size:
                self.buffer = "\n".join(self.buffer.split("\n")[-self.buffer_size:]) 

            self.text_widget.insert(END, self.buffer)
            self.text_widget.see('end')

    @staticmethod
    def clean_out(txt):
        if txt is not None and txt!="b''" and txt!='' and txt!="\n" and txt!="None":
            if txt[:2]=="b'":
                clean_txt = txt[2:-1]
                clean_txt = clean_txt.replace('\\n', "\n")
            return clean_txt
        else:
            return None

    def __getattr__(self, attr):
       return getattr(self.stream, attr)

    

class XCPManager(Tk):
    def __init__(self):
        Tk.__init__(self)

        set_options()

        self.title("Counterparty Wallet Manager")
        self.protocol("WM_DELETE_WINDOW", self.ask_quit) 

        menu = Frame(self)     

        start_button = Button(menu, text='START PARTY!', command=self.run_webserver)
        start_button.pack(side=LEFT)

        open_button = Button(menu, text='OPEN WALLET', command=self.open_wallet)
        open_button.pack(side=LEFT)

        quit_button = Button(menu, text='QUIT', command=self.ask_quit)
        quit_button.pack(side=RIGHT)

        menu.pack(fill=X, padx=15, pady=5)

        text_widget = Text(self, borderwidth=2, relief=GROOVE, highlightcolor="white")
        
        text_widget.pack(fill=BOTH, expand=1, padx=15, pady=5)

        sys.stdout = TextWidgetOut(text_widget, sys.stdout)
        sys.stderr = TextWidgetOut(text_widget, sys.stderr)

        self.after(500, self.update_logs)
        self.ws_subprocess = None
        self.xcpd_subprocess = None

    def run_webserver(self):
        print(b"starting...\n")
        self.ws_subprocess = subprocess.Popen("./counterpartyws.py", stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.xcpd_subprocess = subprocess.Popen("./followblocks.py", stdout=subprocess.PIPE, stderr=subprocess.PIPE)


    def update_logs(self):
        if self.ws_subprocess is not None:
            print(non_block_read(self.ws_subprocess.stdout))
            print(non_block_read(self.ws_subprocess.stderr))
        if self.xcpd_subprocess is not None:
            print(non_block_read(self.xcpd_subprocess.stdout))
            print(non_block_read(self.xcpd_subprocess.stderr))       
        self.after(500, self.update_logs)

    def open_wallet(self):
        webbrowser.open_new("http://"+config.GUI_USER+":"+config.GUI_PASSWORD+"@"+config.GUI_HOST+":"+config.GUI_PORT+"/")


    def ask_quit(self):
        self.ws_subprocess.kill()
        self.xcpd_subprocess.kill()
        self.destroy()



if __name__ == '__main__':
    
    root = XCPManager() 
    root.mainloop()




