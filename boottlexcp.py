import os
import subprocess, codecs
import logging
from tkinter import *
from tkinter import messagebox
import webbrowser
from helpers import set_options, check_config
from counterpartyd.lib import config
from configdialog import ConfigDialog
from threading  import Thread
#import _thread

def forward_stream(proc, stream_in, stream_out):
    try:
        for line in iter(stream_in.readline, b''):
            if proc.poll() is None:
                stream_out.write(line.decode(encoding='UTF-8'))
            else:
                #_thread.exit()
                pass
    except Exception as e:
        #_thread.exit()
        pass
        

class TextWidgetOut(object):
    def __init__(self, text_widget, stream):
        self.text_widget = text_widget
        self.stream = stream

    def write(self, txt):
        self.text_widget.insert(END, txt)
        self.text_widget.see('end')

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

        self.text_widget = Text(self, borderwidth=2, relief=GROOVE, highlightcolor="white")
        
        self.text_widget.pack(fill=BOTH, expand=1, padx=15, pady=5)

        sys.stdout = TextWidgetOut(self.text_widget, sys.stdout)
        sys.stderr = TextWidgetOut(self.text_widget, sys.stderr)

        self.ws_subprocess = None
        self.xcpd_subprocess = None
        self.logthread = []

        self.python_path = "python"; #TODO: find another way to know i we are in .app
        if 'Contents/Resources/' in os.path.abspath(os.path.dirname(__file__)):
            self.python_path = "../MacOS/python"


    def start_party(self):     
        if (not check_config()):
            self.open_config()  
        else:
            if self.ws_subprocess is None:
                print("Webserver starting...")
                try:
                    self.ws_subprocess = subprocess.Popen([self.python_path, 'counterpartyws.py'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=False)
                except Exception as e:
                    print(e)
            if self.xcpd_subprocess is None:
                print("Following blocks starting...")
                try:
                    self.xcpd_subprocess = subprocess.Popen([self.python_path, 'followblocks.py'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=False)
                except Exception as e:
                    print(e)
                        
            self.party_started = True
            self.switch_button.config(text='STOP PARTY!')
            self.watch_logs()


    def watch_stream(self, proc, stream):
        thr = Thread(target=forward_stream, args=(proc, stream, sys.stdout))
        thr.daemon = True # thread dies with the program
        thr.start()
        self.logthread.append(thr)


    def watch_logs(self):       
        procs = [self.xcpd_subprocess, self.ws_subprocess]
        for proc in procs:
            if proc is not None:
                self.watch_stream(proc, proc.stdout)
                self.watch_stream(proc, proc.stderr)


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
            print("Webserver stopping..")
            try:
                self.ws_subprocess.kill()
            except Exception as e:
                print(e)
            self.ws_subprocess = None
        if self.xcpd_subprocess is not None:
            print("Following blocks stopping..")
            try:
                self.xcpd_subprocess.kill()
            except Exception as e:
                print(e)
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
            print("Configuration saved.")
            if self.party_started:
                print("Restarting Party!")       
                self.stop_party()
                self.start_party()
        else:
            print("Configuration does not changed.")

if __name__ == '__main__':
    
    root = XCPManager() 
    root.mainloop()




