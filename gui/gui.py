import tkinter as tk
import tkinter.ttk as ttk
import tkinter.font as font
import numpy as np
import math
import socket
import select
import struct
import matplotlib
matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure
import var

etip = "192.168.1.35"
ltip = "192.168.1.60"

def buildGui():
    # Main window
    mainWindow = tk.Tk()
    img = tk.PhotoImage(file="/home/mchristo/lowres_gui/vervet.png")
    mainWindow.tk.call('wm', 'iconphoto', mainWindow._w, img)
    mainWindow.title('LoWRES')
    mainWindow.config(bg='black')
    #mainWindow.geometry('1300x800')
    mainWindow.protocol("WM_DELETE_WINDOW", mainWindow.destroy)

    # Set up variables
    var.rxfs = tk.DoubleVar()
    var.txfs = tk.DoubleVar()
    var.trlenTxt = tk.StringVar()
    var.stackTxt = tk.StringVar()
    var.chirpBW = tk.DoubleVar()
    var.chirpCF = tk.DoubleVar()
    var.chirpLen = tk.DoubleVar()
    var.chirpAmp = tk.DoubleVar()
    var.chirpAmpV = tk.DoubleVar()
    var.chirpPRF = tk.DoubleVar()
    var.rxtrace = tk.IntVar()
    var.gpsSat = tk.IntVar()
    var.gpsLon = tk.DoubleVar()
    var.gpsLat = tk.DoubleVar()
    var.gpsElev = tk.DoubleVar()

    # Config and tx/rx tabs
    nb = ttk.Notebook(mainWindow)
    nb.grid(sticky='NEWS')
    config = ttk.Frame(mainWindow)
    config.grid(sticky='NEWS')
    nb.add(config, text='CONFIGURE')
    txrx = ttk.Frame(mainWindow)
    nb.add(txrx, text='TX/RX')

    #### config page ####

    tk.Message(config, text = 'University of Arizona\nLoWRES', 
        font=("Verdana", 25, 'bold'), relief=tk.GROOVE, justify=tk.CENTER,
        bd=8, fg='darkred', bg='lightblue', width = 450)\
        .grid(padx=20, pady=30, sticky='WE')

    # Fs display, tracelen setting, stacking setting
    params = tk.Frame(config)
    params.grid(row=1, sticky='NESW')

    tk.Label(params, text='TX Sampling Frequency (MHz): ', font="Comic 12 bold")\
        .grid(sticky='WE')
    tk.Label(params, textvariable=var.txfs, relief=tk.SUNKEN, bg='White',
        width=9, font='Comic 12 bold')\
        .grid(row=0, column=1, sticky='WE')

    tk.Label(params, text='RX Sampling Frequency (MHz): ', font="Comic 12 bold")\
        .grid(row=1, sticky="W")
    tk.Label(params, textvariable=var.rxfs, relief=tk.SUNKEN, bg='White',
        width=9, font='Comic 12 bold')\
        .grid(row=1, column=1, sticky='W')

    tk.Label(params, text='Trace Length (us):', font="Comic 12 bold")\
        .grid(row=2, sticky='W')
    trlenBox = tk.Entry(params, bg='pink', textvariable=var.trlenTxt, 
            width=9, font='Comic 12 bold italic')
    trlenBox.grid(row=2, column=1, sticky='W') 

    tk.Label(params, text='Stacking: ', font="Comic 12 bold")\
        .grid(row=3, sticky='W')
    stackBox = tk.Entry(params, bg='pink', textvariable=var.stackTxt, 
            width=9, font='Comic 12 bold italic')\
            .grid(row=3, column=1, sticky='W')

    # Sliders for chirp config
    sliders = tk.Frame(config)
    sliders.grid(row=2)

    tk.Label(sliders, text='Bandwidth\n(%)', 
        font="Arial 10 bold").grid(row=0,column=0, sticky='EW', pady=10)
    tk.Label(sliders, text='Center\nFrequency\n(MHz)', 
        font="Arial 10 bold").grid(row=0,column=1, sticky='EW', pady=10)
    tk.Label(sliders, text='Time Length\n(us)', 
        font="Arial 10 bold").grid(row=0,column=2, sticky='EW', pady=10)
    tk.Label(sliders, text='Amplitude\n(dBm)', 
        font="Arial 10 bold").grid(row=0,column=3, sticky='EW', pady=10)
    tk.Label(sliders, text='PRF (KHz)', 
        font="Arial 10 bold").grid(row=0,column=4, sticky='EW', pady=10)


    tk.Scale(sliders, from_=200, to=-200, troughcolor='cyan', 
        resolution=10, variable=var.chirpBW, width=35, length=250, 
        activebackground='lightpink', command=plotChirp,
        tickinterval=50, showvalue=tk.FALSE)\
        .grid(row=1, column=0) #chirp bandwidth (%)
    tk.Scale(sliders, from_=10, to=1, troughcolor='cyan',
        variable=var.chirpCF, width=35, length=250,
        activebackground='lightpink', command=plotChirp,
        resolution=.5, tickinterval=1, showvalue=tk.FALSE)\
        .grid(row=1, column=1) #center frequency (MHz)
    tk.Scale(sliders, from_=10, to=1, troughcolor='cyan',
        variable=var.chirpLen, width=35, length=250, command=plotChirp,
        activebackground='lightpink',
        tickinterval=1, showvalue=tk.FALSE)\
        .grid(row=1, column=2) #chirp length (microseconds)
    tk.Scale(sliders, from_=0, to=-20, troughcolor='cyan',
        variable=var.chirpAmp, width=35, length=250, command=plotChirp,
        activebackground='lightpink',
        tickinterval=2, showvalue=tk.FALSE)\
        .grid(row=1, column=3) #amplitude (dBm)
    tk.Scale(sliders, from_=10, to=1, troughcolor='cyan',
        resolution=1, variable=var.chirpPRF, width=35, length=250,
        activebackground='lightpink', command=plotChirp,
        tickinterval=.5, showvalue=tk.FALSE)\
        .grid(row=1, column=4) #Pulse repitition frequency (KHz)

    tk.Entry(sliders, bg='pink', textvariable=var.chirpBW,
        width=7, font='Comic 12 bold')\
        .grid(row=3, column=0, padx=20) 
    tk.Entry(sliders, bg='pink', textvariable=var.chirpCF,
        width=7, font='Comic 12 bold')\
        .grid(row=3, column=1, padx=20) 
    tk.Entry(sliders, bg='pink', textvariable=var.chirpLen, 
        width=7, font='Comic 12 bold')\
        .grid(row=3, column=2, padx=20) 
    tk.Entry(sliders, bg='pink', textvariable=var.chirpAmp, 
        width=7, font='Comic 12 bold')\
        .grid(row=3, column=3, padx=20) 
    tk.Entry(sliders, bg='pink', textvariable=var.chirpPRF,
        width=7, font='Comic 12 bold')\
        .grid(row=3, column=4, padx=20)

    # Chirp display
    chirp = tk.Frame(config)
    chirp.grid(row=1, column=1, rowspan=2)

    tk.Label(chirp, text='Chirp Preview', 
        font="Arial 16 bold").grid()

    chirpf = Figure(figsize=(5,4), dpi=100)
    chirpf.set_facecolor('green')
    var.chirpPlot = chirpf.add_subplot(111)
    var.chirpPlot.set_facecolor('black')

    var.chirpCanvas = FigureCanvasTkAgg(chirpf, master=chirp)
    var.chirpCanvas.draw()
    var.chirpCanvas.get_tk_widget().config(relief=tk.RAISED, bd=8)
    var.chirpCanvas.get_tk_widget().grid(row=1, column=0,
                        padx=30, pady=30, sticky='NSEW')

    chirpf.text(.512, 0.04, 'Time (us)', ha='center', va='center')
    chirpf.text(0.06, 0.5, 'Voltage (V)', ha='center', va='center', rotation='vertical')

    ##### TX/RX Page ####

    # Live data display
    toolbar = tk.Frame(txrx)
    toolbar.grid()

    live = tk.Frame(txrx)
    live.grid(row=1)

    tk.Label(live, text='RX Signal', font="Arial 16 bold").grid()
    rxf = Figure(figsize=(12,4), dpi=100)
    rxf.set_facecolor('#696969')
    var.rxPlot = rxf.add_subplot(111)
    var.rxPlot.set_facecolor('black')
    var.rxPlot.grid(color='#525252')

    var.rxCanvas = FigureCanvasTkAgg(rxf, master=live)
    NavigationToolbar2Tk(var.rxCanvas, toolbar)
    var.rxCanvas.draw()
    var.rxCanvas.get_tk_widget().config(relief=tk.GROOVE, bd=18)
    var.rxCanvas.get_tk_widget().grid(row=1)

    rxf.text(.512, 0.06, 'Time (us)', ha='center', va='center')
    rxf.text(0.06, 0.5, 'Voltage (mV)', ha='center', va='center', rotation='vertical')

    # Buttons
    buttons = tk.Frame(txrx)
    buttons.grid(row=2)

    tk.Button(buttons, text = 'Transmit', fg ='black', font='Times 18 ', 
        bg='#4beb3d', height=1, width=8, command=sendStartCmd).grid(padx=30)
    tk.Button(buttons, text = 'STOP', fg='black', font='Times 18',
        bg='#cf0e0a', height=1, width=8, command=sendStopCmd)\
        .grid(row=0, column=1, padx=30)

    # Chirp param and gps display
    miscdata = tk.Frame(txrx)
    miscdata.grid(row=3)

    # Chirp param display
    chirpinfo = tk.Frame(miscdata, bg='#9abdf5', bd=3, cursor='dot', relief=tk.SOLID)
    chirpinfo.grid(padx=40)

    tk.Label(chirpinfo, text="Center Freq (MHz): ", font="Arial 12 bold", bg='#9abdf5',).grid(row=0, column=0)
    tk.Label(chirpinfo, text="Bandwidth (%): ", font="Arial 12 bold", bg='#9abdf5').grid(row=1, column=0)
    tk.Label(chirpinfo, text="Length (us): ", font="Arial 12 bold", bg='#9abdf5').grid(row=2, column=0)
    tk.Label(chirpinfo, text="Amplitude (dBm): ", font="Arial 12 bold", bg='#9abdf5').grid(row=3, column=0)

    tk.Label(chirpinfo, textvariable=var.chirpCF, font="Arial 12 bold", bg='white', relief=tk.SUNKEN, borderwidth=2, width=8)\
        .grid(row=0, column=1)
    tk.Label(chirpinfo, textvariable=var.chirpBW, font="Arial 12 bold", bg='white', relief=tk.SUNKEN, borderwidth=2, width=8)\
        .grid(row=1, column=1)
    tk.Label(chirpinfo, textvariable=var.chirpLen, font="Arial 12 bold", bg='white', relief=tk.SUNKEN, borderwidth=2, width=8)\
        .grid(row=2, column=1)
    tk.Label(chirpinfo, textvariable=var.chirpAmp, font="Arial 12 bold", bg='white', relief=tk.SUNKEN, borderwidth=2, width=8)\
        .grid(row=3, column=1)

    # RX param display
    rxinfo = tk.Frame(miscdata, bg='#9abdf5', bd=3, cursor='dot', relief=tk.SOLID)
    rxinfo.grid(row=0, column=1, padx=40)

    tk.Label(rxinfo, text="Pulse Rep Freq (kHz): ", font="Arial 12 bold", bg='#9abdf5').grid(row=4, column=0)
    tk.Label(rxinfo, text="RX Fs (MHz): ", font="Arial 12 bold", bg='#9abdf5').grid(row=5, column=0)
    tk.Label(rxinfo, text="Trace Length (us): ", font="Arial 12 bold", bg='#9abdf5').grid(row=6, column=0)
    tk.Label(rxinfo, text="Stacking: ", font="Arial 12 bold", bg='#9abdf5').grid(row=7, column=0)

    tk.Label(rxinfo, textvariable=var.chirpPRF, font="Arial 12 bold", bg='white', relief=tk.SUNKEN, borderwidth=2, width=8)\
        .grid(row=4, column=1)
    tk.Label(rxinfo, textvariable=var.rxfs, font="Arial 12 bold", bg='white', relief=tk.SUNKEN, borderwidth=2, width=8)\
        .grid(row=5, column=1)
    tk.Label(rxinfo, textvariable=var.trlenTxt, font="Arial 12 bold", bg='white', relief=tk.SUNKEN, borderwidth=2, width=8)\
        .grid(row=6, column=1)
    tk.Label(rxinfo, textvariable=var.stackTxt, font="Arial 12 bold", bg='white', relief=tk.SUNKEN, borderwidth=2, width=8)\
        .grid(row=7, column=1)

    # GPS display
    gpsinfo = tk.Frame(miscdata, bg='#9abdf5', bd=3, cursor='dot', relief=tk.SOLID)
    gpsinfo.grid(row=0, column=2, padx=40)

    tk.Label(gpsinfo, text='RX Traces', font="Arial 12 bold", bg='#9abdf5').grid(row=0)
    tk.Label(gpsinfo, text='GPS Sats', font="Arial 12 bold", bg='#9abdf5').grid(row=1)
    tk.Label(gpsinfo, text='Lat', font="Arial 12 bold", bg='#9abdf5').grid(row=2)
    tk.Label(gpsinfo, text='Lon', font="Arial 12 bold", bg='#9abdf5').grid(row=3)
    tk.Label(gpsinfo, text='Elev', font="Arial 12 bold", bg='#9abdf5').grid(row=4)

    tk.Label(gpsinfo, textvariable=var.rxtrace, font="Arial 12 bold", bg='white', relief=tk.SUNKEN, borderwidth=2, width=8)\
        .grid(row=0, column=1)
    tk.Label(gpsinfo, textvariable=var.gpsSat, font="Arial 12 bold", bg='white', relief=tk.SUNKEN, borderwidth=2, width=8)\
        .grid(row=1, column=1)
    tk.Label(gpsinfo, textvariable=var.gpsLat, font="Arial 12 bold", bg='white', relief=tk.SUNKEN, borderwidth=2, width=8)\
        .grid(row=2, column=1)
    tk.Label(gpsinfo, textvariable=var.gpsLon, font="Arial 12 bold", bg='white', relief=tk.SUNKEN, borderwidth=2, width=8)\
        .grid(row=3, column=1)
    tk.Label(gpsinfo, textvariable=var.gpsElev, font="Arial 12 bold", bg='white', relief=tk.SUNKEN, borderwidth=2, width=8)\
        .grid(row=4, column=1)

    return mainWindow


def genRadarCmd():
    cmd = '/home/lowres/LoWRES/radar '\
        + '--tx-rate ' + str(var.txfs.get()) + 'e6 --rx-rate ' + str(var.rxfs.get()) + 'e6 '\
        + '--tx-freq 0 --rx-freq 0 --chirp-bw '\
        + str(var.chirpBW.get()) + ' --chirp-cf ' + str(var.chirpCF.get()) + 'e6 --chirp-len '\
        + str(var.chirpLen.get()) + 'e-6 --chirp-amp ' + str(var.chirpAmpV.get()) + ' --chirp-prf '\
        + str(var.chirpPRF.get()) + 'e3 --trace-len ' + var.trlenTxt.get() + 'e-6 --stack '\
        + var.stackTxt.get()

    return cmd

def sendStartCmd():
    var.running = True
    cmd = genRadarCmd()
    eDip = etip
    eDport = 1997
    eD = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    eD.connect((eDip, eDport))
    eD.send(("SRT:::"+cmd+":::").encode())
    eD.close()
    nsamp = int(float(var.trlenTxt.get())*1e-6*(var.txfs.get()*1e6))
    t = np.linspace(0, float(var.trlenTxt.get()), nsamp)
    var.rxPlot.cla()
    var.rxLine, = var.rxPlot.plot(t, [0]*len(t), 'g')
    var.rxPlot.grid(color='#525252')
    var.mainWindow.after(1, updateRX)

def sendStopCmd():
    var.running = False
    cmd = genRadarCmd()
    eDip = etip
    eDport = 1997
    eD = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    eD.connect((eDip, eDport))
    eD.send(("STP::::::").encode())
    eD.close()

def plotChirp(event): 
    numSamps = int(var.txfs.get()*1e6*var.chirpLen.get()*1e-6)
    si = 1/(var.txfs.get()*1e6)
    chirp = [None]*numSamps

    # calculate initial frequency and slope
    initFreq = (var.chirpCF.get() * 1e6) - (var.chirpCF.get() * 1e6 * (var.chirpBW.get() / 200))
    finalFreq = (var.chirpCF.get() * 1e6) + (var.chirpCF.get() * 1e6 * (var.chirpBW.get() / 200))
    freqSlope = (finalFreq - initFreq) / (var.chirpLen.get() * 1e-6) / 2
    var.chirpAmpV.set(math.sqrt((10 ** (var.chirpAmp.get() / 10)) * .001 * 50) * math.sqrt(2))

    # chirp gen
    t = 0
    for i in range(numSamps):
        chirp[i] = var.chirpAmpV.get() * math.sin(2*math.pi * (initFreq + freqSlope * t) * t)
        t += si

    # plotting
    var.chirpPlot.cla()
    t = np.linspace(0, var.chirpLen.get(), numSamps)
    var.chirpPlot.set_xlim(0-(si/1e-6), var.chirpLen.get()+(si/1e-6))
    ampv = var.chirpAmpV.get()
    var.chirpPlot.set_ylim(-ampv-.1*ampv, ampv+.1*ampv)
    var.chirpPlot.grid(color='#525252')
    var.chirpPlot.plot(t, chirp, 'g')
    var.chirpCanvas.draw_idle()

def updateRX():
    if(not var.connected):
        slct = select.select([var.dataStream], [], [], 0.1)
        if(len(slct[0]) > 0):
            var.conn, addr = var.dataStream.accept()
            var.connected = True
    if(var.connected):
        while(len(var.dbuf) < 20048):
            data = var.conn.recv(4096)
            var.dbuf = var.dbuf + data

        nsamp = int(float(var.trlenTxt.get())*1e-6*(var.txfs.get()*1e6))
        tracefmt = 'f'*nsamp
        gpsfmt = 'qdQffffIf'
        
        #print(len(data0), len(data1), struct.calcsize(gpsfmt), struct.calcsize(tracefmt))
        trace = var.dbuf[0:20000]
        gps = var.dbuf[20000:20048]
        #print(len(trace), len(gps))
        #if(len(data) == struct.calcsize(tracefmt)):
        data = struct.unpack(tracefmt, trace)
        var.rxLine.set_ydata(data)
        var.rxCanvas.draw()
        var.rxCanvas.flush_events()
        #elif(len(data) == struct.calcsize(gpsfmt)):
        data = struct.unpack(gpsfmt, gps)
        var.gpsLat.set(round(data[3],3))
        var.gpsLon.set(round(data[4],3))
        var.gpsElev.set(round(data[5],3))
        var.rxtrace.set(data[2])
        var.gpsSat.set(data[7])
        var.dbuf = var.dbuf[20048::]
    if(var.running):
        var.mainWindow.after(10, updateRX)
    elif(not var.running):
        var.connected = False

def networkInit():
    var.dataStream = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    var.dataStream.bind((ltip, 1999))
    var.dataStream.listen()
    var.dataStream.settimeout(10)

def defaults():
    var.rxfs.set(100)
    var.txfs.set(100)
    var.trlenTxt.set(50)
    var.stackTxt.set(100)
    var.chirpBW.set(100)
    var.chirpCF.set(5)
    var.chirpAmp.set(0)
    var.chirpAmpV.set(.31618)
    var.chirpLen.set(5)
    var.chirpPRF.set(2)
    var.rxtrace.set(0)
    var.gpsSat.set(0)
    var.gpsLon.set(0)
    var.gpsLat.set(0)
    var.gpsElev.set(0)
    var.running = False
    var.connected = False
    

def main():
    var.mainWindow = buildGui()
    networkInit()
    defaults()
    plotChirp(None)
    var.mainWindow.mainloop()

main()

