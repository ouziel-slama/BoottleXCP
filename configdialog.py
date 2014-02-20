from tkinter import *
from tkinter import messagebox
import os

class ConfigDialog(Toplevel):

    def __init__(self, parent, title = None, configfile = None, defaultvalues = None, allkeys = None, configsection="Default", configpath=None):

        Toplevel.__init__(self, parent)
        self.transient(parent)

        if title:
            self.title(title)

        self.parent = parent
        self.configfile = configfile
        self.allkeys = allkeys
        self.defaultvalues = defaultvalues
        self.configsection = configsection
        self.configpath = configpath
        self.config_vars = {}

        self.changed = False

        body = Frame(self)
        self.initial_focus = self.body(body)
        body.pack(padx=5, pady=5)

        self.buttonbox()

        self.grab_set()

        if not self.initial_focus:
            self.initial_focus = self

        self.protocol("WM_DELETE_WINDOW", self.cancel)

        self.geometry("+%d+%d" % (parent.winfo_rootx()+50,
                                  parent.winfo_rooty()+50))

        self.initial_focus.focus_set()

        self.wait_window(self)


    def body(self, master):

        fields_list = None
        config_fields = []       

        if self.configfile is not None and self.allkeys is not None:
            fields_list = self.allkeys
        elif self.configfile is not None:
            fields_list = self.configfile[self.configsection]

        if fields_list is not None:
            row = 0
            for key in fields_list:
                Label(master, text=key+":").grid(row=row, sticky=W)
                self.config_vars[key] = StringVar()
                if key in self.configfile[self.configsection]:
                    self.config_vars[key].set(self.configfile[self.configsection][key])
                else:
                    self.config_vars[key].set(self.defaultvalues[key])
                inputfield = Entry(master, textvariable=self.config_vars[key])
                inputfield.grid(row=row, column=1)
                config_fields.append(inputfield)
                row = row + 1

            return config_fields[0] # initial focus

        return master


    def buttonbox(self):
        box = Frame(self)

        w = Button(box, text="OK", width=10, command=self.ok)
        w.pack(side=LEFT, padx=5, pady=5)

        w = Button(box, text="Cancel", width=10, command=self.cancel)
        w.pack(side=LEFT, padx=5, pady=5)

        self.bind("<Return>", self.ok)
        self.bind("<Escape>", self.cancel)

        box.pack()


    def ok(self, event=None):       
        try:
            for key in self.config_vars:
                self.configfile[self.configsection][key] = self.config_vars[key].get().strip()

            with open(self.configpath, 'w+') as fileconf:
                self.configfile.write(fileconf)
                fileconf.close()

            self.changed = True
            self.cancel()

        except Exception as e:
            messagebox.showwarning(
                "Bad input",
                "Illegal values, please try again"
            )
        

    def cancel(self, event=None):
        self.parent.focus_set()
        self.destroy()

    #




