import fcntl
import os
import subprocess, codecs
import logging
from tkinter import *
from tkinter import messagebox
import webbrowser
from helpers import set_options, check_config
from counterpartyd.lib import config
from configdialog import ConfigDialog

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

        self.configfile = set_options()
        self.defaultvalues = {
            "gui-host": config.GUI_HOST,
            "gui-port": config.GUI_PORT,
            "gui-user": config.GUI_USER,
            "gui-password": config.GUI_PASSWORD,

            "bitcoind-rpc-connect": config.BITCOIND_RPC_CONNECT,
            "bitcoind-rpc-port": config.BITCOIND_RPC_PORT,
            "bitcoind-rpc-user": config.BITCOIND_RPC_USER,
            "bitcoind-rpc-password": config.BITCOIND_RPC_PASSWORD
        }

        self.allkeys = [
            "gui-host", "gui-port", "gui-user", "gui-password", 
            "bitcoind-rpc-connect", "bitcoind-rpc-port", "bitcoind-rpc-user", "bitcoind-rpc-password"
        ]
        self.configpath = os.path.join(config.DATA_DIR, 'counterpartyd.conf')       

        self.title("Counterparty Wallet Manager")
        self.protocol("WM_DELETE_WINDOW", self.quit) 

        menu = Frame(self)     

        self.switch_button = Button(menu, text='START PARTY!', command=self.switch_party)
        self.switch_button.pack(side=LEFT)
        self.party_started = False

        open_button = Button(menu, text='OPEN WALLET', command=self.open_wallet)
        open_button.pack(side=LEFT)

        quit_button = Button(menu, text='QUIT', command=self.quit)
        quit_button.pack(side=RIGHT)

        quit_button = Button(menu, text='CONFIG', command=self.open_config)
        quit_button.pack(side=RIGHT)

        menu.pack(fill=X, padx=15, pady=5)

        text_widget = Text(self, borderwidth=2, relief=GROOVE, highlightcolor="white")
        
        text_widget.pack(fill=BOTH, expand=1, padx=15, pady=5)

        sys.stdout = TextWidgetOut(text_widget, sys.stdout)
        sys.stderr = TextWidgetOut(text_widget, sys.stderr)

        self.after(500, self.update_logs)
        self.ws_subprocess = None
        self.xcpd_subprocess = None


    def start_party(self):     
        if (not check_config()):
            self.open_config()  
        else:
            if self.ws_subprocess is None:
                print(b"Webserver starting...\n")
                self.ws_subprocess = subprocess.Popen("./counterpartyws.py", stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            if self.xcpd_subprocess is None:
                print(b"Following blocks starting...\n")
                self.xcpd_subprocess = subprocess.Popen("./followblocks.py", stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            self.party_started = True
            self.switch_button.config(text='STOP PARTY!')


    def update_logs(self):
        if self.ws_subprocess is not None:
            print(non_block_read(self.ws_subprocess.stdout))
            print(non_block_read(self.ws_subprocess.stderr))
        if self.xcpd_subprocess is not None:
            print(non_block_read(self.xcpd_subprocess.stdout))
            print(non_block_read(self.xcpd_subprocess.stderr))       
        self.after(500, self.update_logs)

    def open_wallet(self):

        if self.party_started:
            webbrowser.open_new(config.GUI_HOME)
        else:
            messagebox.showwarning(
                "Oops!",
                "you did not start the party!"
            )

    def stop_party(self):
        if self.ws_subprocess is not None:
            print(b"Webserver stopping..\n")
            self.ws_subprocess.kill()
            self.ws_subprocess = None
        if self.xcpd_subprocess is not None:
            print(b"Following blocks stopping..\n")
            self.xcpd_subprocess.kill()
            self.xcpd_subprocess = None
        self.party_started = False
        self.switch_button.config(text='START PARTY!')

    def switch_party(self):
        if self.party_started:
            self.stop_party()
        else:
            self.start_party()
            

    def quit(self):
        self.stop_party()
        self.destroy()

    def open_config(self):
        config_dialog = ConfigDialog(self, title="Configuration", configfile=self.configfile, 
                                    defaultvalues=self.defaultvalues, allkeys=self.allkeys, configpath=self.configpath)
        if config_dialog.changed:
            self.configfile = set_options()
            print(b"Configuration saved.\n")
            if self.party_started:
                print(b"Restarting Party!\n")       
                self.stop_party()
                self.start_party()
        else:
            print(b"Configuration does not changed.\n")

if __name__ == '__main__':
    
    root = XCPManager() 
    root.mainloop()




