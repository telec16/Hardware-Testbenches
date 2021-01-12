from tkinter import ttk
import tkinter as tk
import tkinter.simpledialog


class NextCldDialog(tkinter.simpledialog.Dialog):

    @staticmethod
    def new_dialog_with_results(**kwargs):
        """Create a new dialog window with default values
        The tk root must be unused ! (please close your plot, etc)

        :param name=''
        :param implanted=True
        :param size=6
        :param csv=True
        :param png=True
        :param show=False
        """

        root = tk.Tk()
        root.withdraw()

        r = NextCldDialog(root, **kwargs).results

        root.destroy()
        del root

        return r

    def __init__(self, parent, *, name='', implanted=True, size=6, csv=True, png=True, show=False):
        self.name = tk.StringVar(value=name)
        self.implanted = tk.BooleanVar(value=implanted)
        self.size = tk.IntVar(value=size)
        self.csv = tk.BooleanVar(value=csv)
        self.png = tk.BooleanVar(value=png)
        self.show = tk.BooleanVar(value=show)

        self.continue_exec = False

        super().__init__(parent)

    def body(self, master):
        master.winfo_toplevel().title("Next CLD")
        master.winfo_toplevel().iconbitmap("cld.ico")

        ttk.Label(master, text="Name:") \
            .grid(row=0, sticky=tk.E)

        ttk.Entry(master, textvariable=self.name) \
            .grid(row=0, column=1, columnspan=2)

        ttk.Radiobutton(master, text="Implanted", variable=self.implanted, value=True) \
            .grid(row=1, column=0, sticky=tk.W)
        ttk.Radiobutton(master, text="Not Implanted", variable=self.implanted, value=False) \
            .grid(row=2, column=0, sticky=tk.W)

        ttk.Radiobutton(master, text="6 um", variable=self.size, value=6) \
            .grid(row=1, column=2, sticky=tk.E)
        ttk.Radiobutton(master, text="4 um", variable=self.size, value=4) \
            .grid(row=2, column=2, sticky=tk.E)

        ttk.Checkbutton(master, text="Save csv", variable=self.csv, onvalue=True, offvalue=False) \
            .grid(row=3, column=0)
        ttk.Checkbutton(master, text="Save png", variable=self.png, onvalue=True, offvalue=False) \
            .grid(row=3, column=1)
        ttk.Checkbutton(master, text="Show png", variable=self.show, onvalue=True, offvalue=False) \
            .grid(row=3, column=2)

    def buttonbox(self):

        box = tk.Frame(self)

        w = tk.Button(box, text="Stop tests", width=10, command=self.cancel)
        w.pack(side=tk.LEFT, padx=5, pady=5)
        w = tk.Button(box, text="Test next CLD", width=10, command=self.ok, default=tk.ACTIVE)
        w.pack(side=tk.LEFT, padx=5, pady=5)

        self.bind("<Return>", self.ok)
        self.bind("<Escape>", self.cancel)

        box.pack()

    def apply(self):
        self.continue_exec = True

    @property
    def results(self):
        if not self.continue_exec:
            return None
        else:
            return dict(name=self.name.get(),
                        implanted=self.implanted.get(),
                        size=self.size.get(),
                        csv=self.csv.get(),
                        png=self.png.get(),
                        show=self.show.get())


class StartCldDialog(tkinter.simpledialog.Dialog):

    @staticmethod
    def new_dialog_with_results(**kwargs):
        """Create a new dialog window with default values
        The tk root must be unused ! (please close your plot, etc)

        :param voltage=50
        :param max_current=12
        :param shunt=0.0256
        :param pw=None
        """

        root = tk.Tk()
        root.withdraw()

        r = StartCldDialog(root, **kwargs).results

        root.destroy()
        del root

        return r

    def __init__(self, parent, *, voltage=50, max_current=12, shunt=0.0256, pw=None):
        pw = pw or [10, 30, 100, 300, 1000]
        pw = ','.join([str(p) for p in pw])

        self.voltage = tk.StringVar(value=str(voltage))
        self.max_current = tk.StringVar(value=str(max_current))
        self.shunt = tk.StringVar(value=str(shunt))
        self.pw = tk.StringVar(value=pw)

        self.start_exec = False

        super().__init__(parent)

    def body(self, master):
        master.winfo_toplevel().title("Experiment parameters")
        master.winfo_toplevel().iconbitmap("cld.ico")

        ttk.Label(master, text="Voltage:") \
            .grid(row=0, sticky=tk.E)
        ttk.Entry(master, textvariable=self.voltage) \
            .grid(row=0, column=1, columnspan=2)

        ttk.Label(master, text="Max current:") \
            .grid(row=1, sticky=tk.E)
        ttk.Entry(master, textvariable=self.max_current) \
            .grid(row=1, column=1, columnspan=2)

        ttk.Label(master, text="Shunt:") \
            .grid(row=2, sticky=tk.E)
        ttk.Entry(master, textvariable=self.shunt) \
            .grid(row=2, column=1, columnspan=2)

        ttk.Label(master, text="Pulse list:") \
            .grid(row=3, sticky=tk.E)
        ttk.Entry(master, textvariable=self.pw) \
            .grid(row=3, column=1, columnspan=2)

    def buttonbox(self):

        box = tk.Frame(self)

        w = tk.Button(box, text="Abort...", width=10, command=self.cancel)
        w.pack(side=tk.LEFT, padx=5, pady=5)
        w = tk.Button(box, text="Start !", width=10, command=self.ok, default=tk.ACTIVE)
        w.pack(side=tk.LEFT, padx=5, pady=5)

        self.bind("<Return>", self.ok)
        self.bind("<Escape>", self.cancel)

        box.pack()

    def apply(self):
        self.start_exec = True

    @property
    def results(self):
        if not self.start_exec:
            return None
        else:
            try:
                return dict(voltage=float(self.voltage.get()),
                            max_current=float(self.max_current.get()),
                            shunt=float(self.shunt.get()),
                            pw=[int(p) for p in self.pw.get().split(',')])
            except ValueError:
                return None


if __name__ == "__main__":

    cld_info = dict(name="CLD_",
                    implanted=True,
                    size=6,
                    csv=True,
                    png=True,
                    show=False)
    parameters = dict(voltage=50,
                      max_current=12,
                      shunt=0.025600,
                      pw=[10, 30, 30, 30, 30, 100, 300])

    parameters = StartCldDialog.new_dialog_with_results(**parameters)
    print(parameters)

    while True:
        cld_info = NextCldDialog.new_dialog_with_results(**cld_info)
        print(cld_info)

        if cld_info is None:
            break
