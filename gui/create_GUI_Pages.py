
from tkinter import *
import tkinter.ttk as ttk
import matplotlib
matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import NavigationToolbar2Tk, FigureCanvasTkAgg
from matplotlib.figure import Figure
import numpy as np
import GUI_Vars
import GenerateChirp

class GUI_Pages:

    def __init__(self, root):
        self.createPages(root)

    def createPages(self, mainWindow):
        mainWindow.title('Chirp Generator')
        mainWindow.config(bg='black')
        mainWindow.geometry('1300x800')

            # ******* PAGE LAYOUT *******
        # Create tabs (separate pages)
        rows = 0
        while (rows < 100):
            mainWindow.rowconfigure(rows, weight=1)
            mainWindow.columnconfigure(rows, weight=1)
            rows += 1

        nb = ttk.Notebook(mainWindow)
        nb.grid(row=4,column=4, columnspan=90, rowspan=90, sticky='NEWS')

        rows = 0
        while (rows < 6):
            # Column/Row weight affect how they expand with the window size
            nb.rowconfigure(rows, weight=1)
            nb.columnconfigure(rows, weight=1)
            rows += 1

        self.page1 = ttk.Frame(mainWindow)
        nb.add(self.page1, text='SETUP')

        self.page2 = ttk.Frame(mainWindow)
        nb.add(self.page2, text='SEND IT')

        rows = 0
        while (rows <= 28):
            # Column/Row weight affect how they expand with the window size
            if (rows > 24 and rows <= 26):
                self.page1.rowconfigure(rows, weight=1, minsize=200)
            elif (rows == 24):
                self.page1.rowconfigure(rows, weight=1, minsize=15)
            elif (rows <= 3):
                self.page1.rowconfigure(rows, weight=1, minsize=35)
            elif (rows >= 0 and rows < 20):
                self.page1.rowconfigure(rows, weight=1, minsize=15)
            elif (rows > 26):
                self.page1.rowconfigure(rows, weight=20)    
            rows += 1

        col = 0
        while (col < 10):
            # Column/Row weight affect how they expand with the window size
            if  (col == 0):
                self.page1.columnconfigure(col, weight = 1, minsize=100)
            elif (col == 3):
                self.page1.columnconfigure(col, weight = 1, minsize=100)
            elif (col < 3):
                self.page1.columnconfigure(col, weight = 1, minsize=160)
            elif (col == 4):
                self.page1.columnconfigure(col, weight = 1)
            elif (col > 4 and col <= 6):
                self.page1.columnconfigure(col, weight = 10, minsize=350)
            else:
                self.page1.columnconfigure(col, weight = 1)
            col += 1
        

    def createPage1(self):
        #UA Represent "Comic-Sans-MS 25 bold italic"
        msgObj = Message(self.page1, text = 'University of Arizona\nVervet', 
                    font=("Verdana", 25, 'bold'), relief=GROOVE, justify=CENTER, bd=8, fg='darkred') #'Comic 25 bold'
        msgObj.config(bg='lightblue', width = 450)
        msgObj.grid(row=0,column=0, padx=20, pady=30, rowspan=4, columnspan=4, sticky='WE')


        # Top Label and Entries
        Label(self.page1, text='Sampling Frequency: ', font="Comic 12 bold italic"
                ).grid(row=5, column=0, columnspan=2, sticky="SWE")
        sfValue = Label(self.page1, text= str(GUI_Vars.GUI_Vars.sampFreq) + ' MHz', relief=SUNKEN, bg='White',
                    font='Comic 12 bold italic')
        sfValue.grid(row=5, column=2, sticky='SW')

        Label(self.page1, text='Trace Length (us): ', font="Comic 12 bold italic"
                ).grid(row=6, column=0, columnspan=2, sticky='SWE')
        traceLenBox = Entry(self.page1, bg='pink', textvariable=GUI_Vars.GUI_Vars.traceLength, 
                    width=7, font='Comic 12 bold italic')
        traceLenBox.grid(row=6, column=2, sticky='SW') 

        Label(self.page1, text='Stack Size: ', font="Comic 12 bold italic"
                ).grid(row=7, column=0, columnspan=2, sticky='SWE')
        stackBox = Entry(self.page1, bg='pink', textvariable=GUI_Vars.GUI_Vars.stack, 
                    width=7, font='Comic 12 bold italic')
        stackBox.grid(row=7, column=2, sticky='SW')

        # traceLenBox.bind('<FocusOut>', setTraceLen)
        # traceLenBox.bind('<Return>', setTraceLen)
        # traceLenBox.bind('<KeyRelease>', verifyTraceEntry)
        # stackBox.bind('<FocusOut>', setStack)
        # stackBox.bind('<Return>', setStack)
        # stackBox.bind('<KeyRelease>', verifyStackEntry)
        # /end Top Label and Entries
        
        #Create widget housing blocks
        sliderFrame = Frame(self.page1)
        sliderFrame.grid(row=25, rowspan=2, column=0, columnspan=4)

        #Vervet image
        vervetDisplay = Canvas(self.page1, width=200, height=360)
        vervetDisplay.grid(row=0,column=5, rowspan=20, columnspan=2, padx=(30,0), 
                        pady=30, sticky='NEW')
        img = PhotoImage(file="vervet_monkey.png")
        vervetDisplay.create_image(60,400, image=img)

        #Generate Chirp display
        cDisplayLabel = Label(self.page1, text='Chirp Preview', 
                    font="Arial 10 bold italic")

        f = Figure(figsize=(5,4), dpi=100)
        f.set_facecolor('green')
        a = f.add_subplot(111)
        a.set_facecolor('black')
        t = np.arange(0, 9, 1)
        a.plot(t, [1,2,3,4,5,6,7,8,9], 'g')


        chirpCanvas = FigureCanvasTkAgg(f, master=self.page1)
        chirpCanvas.draw()
        chirpCanvas.get_tk_widget().config(relief=RAISED, bd=8)
        chirpCanvas.get_tk_widget().grid(row=25, column=5, rowspan=2, 
                            columnspan=2, padx=30, pady=30, sticky='NSEW')

        cDisplayLabel.grid(row=24, column=5, columnspan=2, sticky='NEW')
        f.text(.512, .06, 'Time (us)', ha='center', va='center')
        f.text(0.06, 0.5, 'Voltage (mV)', ha='center', va='center', rotation='vertical')

        #*************************************************************************************
        #Create all sliders and labels

        #Create Slider Labels
        bwLabel = Label(sliderFrame, text='Bandwidth\n(%)', 
                    font="Arial 10 bold italic")
        cfLabel = Label(sliderFrame, text='Center\nFrequency\n(MHz)', 
                    font="Arial 10 bold italic")
        lenLabel = Label(sliderFrame, text='Time Length\n(\u03BCs)', 
                    font="Arial 10 bold italic")
        ampLabel = Label(sliderFrame, text='Amplitude\n(dBm)', 
                    font="Arial 10 bold italic")
        prfLabel = Label(sliderFrame, text='PRF (KHz)', font="Arial 10 bold italic")

        bwLabel.grid(row=0,column=0)
        cfLabel.grid(row=0,column=1)
        lenLabel.grid(row=0,column=2)
        ampLabel.grid(row=0,column=3)
        prfLabel.grid(row=0,column=4)

        #Create Sliders
        bwScale = Scale(sliderFrame, from_=200, to=-200, troughcolor='cyan', 
                    resolution=10, variable=GUI_Vars.GUI_Vars.bw, width=35, length=250, 
                    activebackground='lightpink', command=GenerateChirp.scaleGenChirp,
                    tickinterval=50, showvalue=FALSE) #chirp bandwidth (%)
        bwScale.set(100)
        cfScale = Scale(sliderFrame, from_=10, to=1, troughcolor='cyan',
                    variable=GUI_Vars.GUI_Vars.cf, width=35, length=250, 
                    activebackground='lightpink', command=scaleGenChirp,
                    tickinterval=1, showvalue=FALSE) #center frequency (MHz)
        lenScale = Scale(sliderFrame, from_=10, to=1, troughcolor='cyan',
                    variable=GUI_Vars.GUI_Vars.length, width=35, length=250,
                    activebackground='lightpink', command=scaleGenChirp,
                    tickinterval=1, showvalue=FALSE) #chirp length (microseconds)
        ampScale = Scale(sliderFrame, from_=10, to=-10, troughcolor='cyan',
                    variable=GUI_Vars.GUI_Vars.amp, width=35, length=250,
                    activebackground='lightpink', command=scaleGenChirp,
                    tickinterval=2, showvalue=FALSE) #amplitude (dBm)
        prfScale = Scale(sliderFrame, from_=3, to=1, troughcolor='cyan',
                    resolution=.1, variable=GUI_Vars.GUI_Vars.prf, width=35, length=250,
                    activebackground='lightpink', command=leaveprfSbox,
                    tickinterval=.5, showvalue=FALSE) #Pulse repitition frequency (KHz)

        bwScale.grid(row=4,column=0, padx=10)
        cfScale.grid(row=4,column=1, padx=10)
        lenScale.grid(row=4,column=2, padx=10)
        ampScale.grid(row=4,column=3, padx=10)
        prfScale.grid(row=4,column=4, padx=10)


        #create slider value boxes
        bwSbox = Spinbox(sliderFrame, from_=-200, to=200, bg='pink', textvariable=GUI_Vars.GUI_Vars.bw, 
                    justify=CENTER, validate='all', increment=10, width=5,
                    highlightthickness=2, borderwidth=4, font='Helvetica 15 bold',
                    command=generateChirp)
        cfSbox = Spinbox(sliderFrame, from_=1, to=10, bg='pink', textvariable=GUI_Vars.GUI_Vars.cf, 
                    justify=CENTER, width=5, highlightthickness=2, borderwidth=4,
                    font='Helvetica 15 bold', command=generateChirp)
        lenSbox = Spinbox(sliderFrame, from_=1, to=10, bg='pink', textvariable=GUI_Vars.GUI_Vars.length, 
                    justify=CENTER, width=5, highlightthickness=2, borderwidth=4,
                    font='Helvetica 15 bold', command=generateChirp)
        ampSbox = Spinbox(sliderFrame, from_=-10, to=10, bg='pink', textvariable=GUI_Vars.GUI_Vars.amp, 
                    justify=CENTER, width=5, highlightthickness=2, borderwidth=4,
                    font='Helvetica 15 bold', command=generateChirp)
        prfSbox = Spinbox(sliderFrame, from_=1, to=3, bg='pink', textvariable=GUI_Vars.GUI_Vars.prf, 
                    justify=CENTER, increment=.1, width=5, highlightthickness=2, 
                    borderwidth=4, font='Helvetica 15 bold', command=lambda: leaveprfSbox('Return'))

        bwSbox.grid(row=5,column=0)
        cfSbox.grid(row=5,column=1)
        lenSbox.grid(row=5,column=2)
        ampSbox.grid(row=5,column=3)
        prfSbox.grid(row=5,column=4)

        #Set bindings to ensure valid input
        # bwSbox.bind('<FocusOut>', leavebwSbox)
        # bwSbox.bind('<Return>', leavebwSbox)
        # cfSbox.bind('<FocusOut>', leavecfSbox)
        # cfSbox.bind('<Return>', leavecfSbox)
        # lenSbox.bind('<FocusOut>', leavelenSbox)
        # lenSbox.bind('<Return>', leavelenSbox)
        # ampSbox.bind('<FocusOut>', leaveampSbox)
        # ampSbox.bind('<Return>', leaveampSbox)
        # prfSbox.bind('<FocusOut>', leaveprfSbox)
        # prfSbox.bind('<Return>', leaveprfSbox)