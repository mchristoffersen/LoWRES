"""
This script displays an interactable GUI which allows
The user to create a chirp signal with various parameters. They
can then transmit that signal, in which we create a subprocess (a 
predetermined filepath to a .cpp exe) that handles the transmittion. 
The subprocess pipes back response signals and we are then able 
to display that in the GUI.
"""

'''
Author: Alex Sisson
'''


from tkinter import *
import tkinter.font as font
import tkinter.ttk as ttk
import matplotlib
matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import NavigationToolbar2Tk, FigureCanvasTkAgg
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
import numpy as np
import math
import time
import os
import subprocess
import signal
import struct
import select
import time

import socket
#try:
#    from queue import Queue, Empty
#except ImportError:
#    from Queue import Queue, Empty  # python 2.x

try:
    import fcntl
except ImportError:
    print('Only runs on linux os')



# messages = [ B'This is the message. ',
#              B'It will be sent ',
#              B'in parts.',
#             ]
controller = ('localhost', 4747)
ettus = ("localhost", 1997)

# Create a TCP/IP socket
socks = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
socks.connect(server_address)

i = 0
while i < 10:
    print('Arrived')
    data = socks.recv(1024)
    if data:
        print('Received: ' + str(data))
    i += 1
socks.close()

#Main GUI window
mainWindow = Tk()
mainWindow.title('Chirp Generator')
mainWindow.config(bg='black')
mainWindow.geometry('1300x800')

#chirp variables
sampFreq = 100 #in MHz
receiveSampFreq = 100 #in MHz
cableImpedance = 50

numReceiveSamps = 1000 #This is the number of samples to receive per burst
transmitLoop = False

#yAmpP2 yOffsetP2 xMinEntry xMaxEntry
yAmpFocus = DoubleVar()
yOffsetFocus = DoubleVar()
xMinFocus = DoubleVar()
xMaxFocus = DoubleVar()

maxNum = 0  #rf graph limits
minNum = 0  #rf graph limits

bw = IntVar()
cf = IntVar()
length = IntVar() # chirp length in microseconds
amp = IntVar()
ampVolt = 0
prf = DoubleVar()
traceLength = IntVar()
stack = IntVar()

traceLength.set(50) # in microseconds
stack.set(100)

''' 
All Functions defined here
'''

# Ensure safe exit from all running processes
# safely kills child process 
exitFlag = False
def on_quit(): 
    global exitFlag
    exitFlag = True
    transmitStop()
    mainWindow.destroy()

mainWindow.protocol("WM_DELETE_WINDOW", on_quit)

def convertOctalToBase10(entryWig):
    """values with prepended 0's are treated as octals. This deletes
    those 0's so it is treated as a base10 value"""
    text = entryWig.get()
    numsDeleted = 0
    if (len(text) > 1):
        for i in range(len(text) - 1):
            if (text[i] == '0' and text[i+1] != '.'):
                entryWig.delete(i - numsDeleted, i - numsDeleted + 1)
                numsDeleted += 1
            else:
                break     


def hideFocusError(event):
    """Removes error message when reentering values on page 2 graph focus"""
    focusEntryError.grid_remove()

def focusRxGraph():
    """Zooms rf graph based on user entered 'focus' parameters"""
    p = re.compile('[+-]?(\d+(\.\d*)?|\.\d+)([eE][+-]?\d+)?') #used to verify floats (isdigit doesnt work)
    validValues = 0 #used to count correct values, verifying all entrys are valid
    convertOctalToBase10(yAmpP2)  #make sure each entry is interpreted as base10 float
    convertOctalToBase10(yOffsetP2)
    convertOctalToBase10(xMinEntry)
    convertOctalToBase10(xMaxEntry)

    if (yAmpP2.get()):
        if (p.match(yAmpP2.get())):
            if (abs(float(yAmpFocus.get())) > .001):
                validValues = 1
    if (yOffsetP2.get()):
        if (p.match(yOffsetP2.get())):
            validValues += 1
    if (xMinEntry.get()):
        if (p.match(xMinEntry.get())):
            validValues += 1
    if (xMaxEntry.get()):
        if (p.match(xMaxEntry.get())):
            if (xMaxFocus.get() > xMinFocus.get()):
                validValues += 1
    if (validValues == 4):
        #do graph stuff
        yMax = yOffsetFocus.get() + abs(yAmpFocus.get())
        yMin = yOffsetFocus.get() - abs(yAmpFocus.get())
        rfaSub.set_ylim(yMin, yMax)
        rfaSub.set_xlim(float(xMinFocus.get()), xMaxFocus.get())
    else:
        # Display error msg
        focusEntryError.grid()


def setTraceLen(event):
    """Set Sbox to base10, or 0 if invalid entry"""
    convertOctalToBase10(traceLenBox)
    if (traceLenBox.get()):
        traceLenValP2.config(text=str(traceLength.get()))
    else:
        traceLenValP2.config(text='0')
        traceLength.set(0)


def verifyTraceEntry(event):
    """Remove non-digit entry, insert 0 if neccessary"""
    if (traceLenBox.get()):
        while not (traceLenBox.get().isdigit()):
            if (len(traceLenBox.get()) <= 1):
                traceLenBox.insert(0, '0')
            else:
                traceLenBox.delete(len(traceLenBox.get()) - 1, END)


def setStack(event):
    """Set Sbox to base10, or 0 if invalid entry"""
    convertOctalToBase10(stackBox)
    if (stackBox.get()):
        stackvalP2.config(text=str(stack.get()))
    else:
        stackvalP2.config(text='0')
        stack.set(0)


def verifyStackEntry(event):
    """Remove non-digit entry, insert 0 if neccessary"""
    if (stackBox.get()):
        while not (stackBox.get().isdigit()):
            if (len(stackBox.get()) <= 1):
                stackBox.insert(0, '0')
            else:
                stackBox.delete(len(stackBox.get()) - 1, END)


def leavebwSbox(event):
    """Round to correct precision and update chirp display"""
    bw.set(int(round(bw.get() / 10.0) * 10))
    generateChirp()

def leavecfSbox(event):
    """Round to correct precision and update chirp display"""
    cf.set(round(float(cfSbox.get())))
    generateChirp()

def leavelenSbox(event):
    """Round to correct precision and update chirp display"""
    length.set(round(float(lenSbox.get())))
    generateChirp()

def leaveampSbox(event):
    """Round to correct precision and update chirp display"""
    amp.set(round(float(ampSbox.get())))
    generateChirp()

def leaveprfSbox(event):
    """Round to correct precision and update prf display"""
    prf.set(round(prf.get(), 1))
    prfvalP2.config(text=str(prf.get()) + " KHz")


def non_block_read(output, numReceiveSamps, lookForChar):
    """Reads binary values from buffer in non-blocking mode
    (will read up to numReceiveSamps amount of floats)"""
    if (acceptingPackets):
        fd = output.fileno()    
        fl = fcntl.fcntl(fd, fcntl.F_GETFL)
        fcntl.fcntl(fd, fcntl.F_SETFL, fl | os.O_NONBLOCK)
        
        if lookForChar:
            try:
                return output.read(1)
            except:
                return ""
        else:
            try:
                return output.read(4 * numReceiveSamps)
            except:
                return ""
    else:
        return ""

def block_read(readSocket, numFloats):
    #return readSocket.recv(1024)    
    pass

def generateEttusCommand(numReceiveSamps):
    """chirp command generated from user-determined chirp values"""
    chirpCmd = ['/home/vervet/Desktop/msc_x310/txrx_loopback_to_file_ALEX', '--ref', 'gpsdo', '--tx-rate',
            str(sampFreq) + 'e6', '--rx-rate', str(receiveSampFreq) + 'e6', 
            '--tx-freq', '0', '--rx-freq', '0', '--tx-subdev', 'A:AB', '--tx-ant',
            'A', '--type', 'float', '--chirp-bw', str(bw.get()), '--chirp-cf',
            str(cf.get()) + 'e6', '--chirp-len', str(length.get()) + 'e-6',
            '--chirp-amp', str(ampVolt), '--chirp-prf', str(prf.get()) + 'e3',
            '--trace-len', str(traceLength.get()) + 'e-6', '--stack', str(stack.get())]
    tempCmd = ['/home/alex/Documents/cpp_GUI_test/main']
    return tempCmd


def transmitAnimate():
    """When transmitting, this funtion handles the transmittion animation, as well
    as receiving the binary samples while displaying them"""
    global transmitLoop, sendLabel, ov1, ov2, ov3, ov4, ov5, acceptingPackets #ettusProgram
    global maxNum, minNum, numReceiveSamps, ettusSocket

    bufferMax = 16384 #65536 Byte maximum in a buffer divided by 4 (4 bytes per float)
    animTime = time.time() #animation is based on real time clock
    transmitLoop = True
    page2.grab_set() #forces lock to page 2, so we cant modify chirp values while transmitting
    clearButt.config(state=DISABLED)
    transmitB.config(state=DISABLED)
    tracesVal.config(text = '0')

    acceptingPackets = True
    
    numReceiveSamps = receiveSampFreq * traceLength.get()
    if (numReceiveSamps < bufferMax and numReceiveSamps > 0):
        bufferMax = numReceiveSamps #the maximum amount of floats we will get per trace
    zeros = [0] * numReceiveSamps
    rfLine = generateResponseGraph(zeros) #initial to expected number of trace samples set to 0 
    maxNum = 0
    minNum = 0 
    print('Samples per trace: ' + str(numReceiveSamps))
    print('Buffer Max: ' + str(bufferMax))
    cmd = generateEttusCommand(bufferMax)

    #open pipe to ettus with our generated shell command
    #ettusProgram = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE)

    #TODO SOCKETYNESS TODO
    ettusAddress = ('localhost', 4747) #192.168.20.1
    ettusSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    ettusSocket.create_connection(ettusAddress)
    ettusSocket.setblocking(0)
    #ettusSocket.bind(ettusAddress)

    
    
    #Handle visuals
    sendLabel.config(text='Sending: ', fg='#1ee646')
    milseconds = 0
    animateSpeed = .5 #milliseconds between updates

    # These two bools make sure animation doesn't 
    #  steps multiple times before the next in sequence
    oddStep = False 
    evenStep = False 

    sampReceivedCtr = 0 # counter from number of samples piped in from cpp file
    leftoverSamps = numReceiveSamps % bufferMax
    responseSamps = [0] * numReceiveSamps 

    #These two are for detecting the initial transmit signal
    #We need this to know when to start accepting packets
    waitForRxSignal = False
    numCorrect = 0

    #Animate and display response packets from ettus
    while (transmitLoop and not exitFlag):
        mainWindow.update_idletasks() #This lets GUI respond to other events
        mainWindow.update()     #This also lets GUI respond to other events
        milseconds += 1
        fullRead = False

        #wait for signal to start receiving
        if waitForRxSignal:
            #FIXME line = non_block_read(ettusProgram.stdout, 1, True)
            #line = readSocket.recv(1)
            if line:
                line = line.decode("utf-8")
                if (line == 'T' and numCorrect == 0):
                    numCorrect = 1
                elif (line == 'R' and numCorrect == 1):
                    numCorrect = 2
                elif (line == 'A' and numCorrect == 2):
                    numCorrect = 3
                elif (line[0] == 'N' and numCorrect == 3):
                    numCorrect = 4
                elif (line[0] == 'S' and numCorrect == 4):
                    numCorrect = 5
                elif (line[0] == 'M' and numCorrect == 5):
                    numCorrect = 6
                elif (line[0] == 'I' and numCorrect == 6):
                    numCorrect = 7
                elif (line[0] == 'T' and numCorrect == 7):
                    waitForRxSignal = False
                    print('Transmitting...')
                else:
                    numCorrect = 0
        else: # We have received start signal
            #get bufferMax amount of floats at a time (if possible)
            if (numReceiveSamps - sampReceivedCtr >= bufferMax):
                #FIXME line = non_block_read(ettusProgram.stdout, bufferMax, False) 
                line = readSocket.recv(bufferMax)
                if (line):
                    if (len(line) / 4 == bufferMax):
                        fullRead = True
                        sampReceivedCtr += bufferMax
                    else:
                        fullRead = False
                        sampReceivedCtr += (len(line) // 4) #4 bytes per sample, so div by 4
                        leftoverSamps = len(line) // 4
            else: #get less than 1K floats for the end of the trace (if neccessary)
                #FIXME line = non_block_read(ettusProgram.stdout, numReceiveSamps - sampReceivedCtr, False)
                line = readSocket.recv(numReceiveSamps - sampReceivedCtr)
                if (line):
                    sampReceivedCtr += (len(line) // 4) #4 bytes per sample, so div by 4
                    leftoverSamps = len(line) // 4
                    fullRead = False
            if line:
                if (fullRead): #read full buffer size of samples
                    responseSamps[sampReceivedCtr - bufferMax : sampReceivedCtr] = struct.unpack(
                            str(bufferMax) + 'f', line)
                else:
                    responseSamps[sampReceivedCtr - leftoverSamps : sampReceivedCtr] = struct.unpack(
                            str(leftoverSamps) + 'f', line)

                #check if received enough to update graph
                if (sampReceivedCtr == numReceiveSamps): 
                    #Set min and max y values with a little padding
                    minNum = min(responseSamps) - .05
                    maxNum = max(responseSamps) + .05
                    updateResponseGraph(rfLine, responseSamps)
                    sampReceivedCtr = 0
                    tracesVal.config(text = str(int(tracesVal.cget("text")) + 1))

        #Animation steps
        timeElapsed = abs(round(time.time() - animTime, 2)) 
        if (abs(timeElapsed - animateSpeed) < .1 and not oddStep):
            ov1 = gOval1.create_oval(ovInitX, ovInitY, ovInitX + ovSize,
                 ovInitY + ovSize, fill = 'green', width=2)
            oddStep = True
            evenStep = False
        elif (abs(timeElapsed - (2 * animateSpeed)) < .1 and not evenStep):
            ov2 = gOval1.create_oval(ovInitX + ovSize + ovDist, ovInitY,
                ovInitX + (2 * ovSize) + ovDist, ovInitY + ovSize, fill = 'green', width=2)
            oddStep = False
            evenStep = True
        elif  (abs(timeElapsed - (3 * animateSpeed)) < .1 and not oddStep):
            ov3 = gOval1.create_oval(ovInitX + (2 * ovSize) + (2 * ovDist), ovInitY,
                ovInitX + (3 * ovSize) + (2 * ovDist), ovInitY + ovSize, fill = 'green', width=2)
            oddStep = True
            evenStep = False
        elif (abs(timeElapsed - (4 * animateSpeed)) < .1 and not evenStep):
            ov4 = gOval1.create_oval(ovInitX + (3 * ovSize) + (3 * ovDist), ovInitY,
                ovInitX + (4 * ovSize) + (3 * ovDist), ovInitY + ovSize, fill = 'green', width=2)
            oddStep = False
            evenStep = True 
        elif  (abs(timeElapsed - (5 * animateSpeed)) < .1 and not oddStep):
            ov5 = gOval1.create_oval(ovInitX + (4 * ovSize) + (4 * ovDist), ovInitY,
                ovInitX + (5 * ovSize) + (4 * ovDist), ovInitY + ovSize, fill = 'green', width=2)
            oddStep = True
            evenStep = False
        elif (abs(timeElapsed - (6 * animateSpeed)) < .1 and not evenStep):
            gOval1.delete(ov1)
            oddStep = False
            evenStep = True
        elif  (abs(timeElapsed - (7 * animateSpeed)) < .1 and not oddStep):
            gOval1.delete(ov2)
            oddStep = True
            evenStep = False
        elif (abs(timeElapsed - (8 * animateSpeed)) < .1 and not evenStep):
            gOval1.delete(ov3)
            oddStep = False
            evenStep = True 
        elif (abs(timeElapsed - (9 * animateSpeed)) < .1 and not oddStep):
            gOval1.delete(ov4)
            oddStep = True
            evenStep = False
        elif (abs(timeElapsed - (10 * animateSpeed)) < .1 and not evenStep):
            gOval1.delete(ov5)
            animTime = time.time()
            oddStep = False
            evenStep = True            

    print('... End of Transmition')  

def transmitStop():
    """Stop transmition, safely kill child process, and end animation"""
    global transmitLoop, ov1, ov2, ov3, ov4, ov5, ettusProgram, acceptingPackets
    #only do stuff if we are currently transmitting
    if (transmitLoop):
        transmitLoop = False #ends animation
        acceptingPackets = False

        #Update GUI if the window isn't being closed
        if not exitFlag:
            page2.grab_release()
            transmitB.config(state=NORMAL)
            clearButt.config(state=NORMAL)
            sendLabel.config(text='Stopped: ', fg='#d90000')
        
            #Make sure Ovals are defined, then delete them
            try:
                ov1
            except NameError:
                pass
            else:
                gOval1.delete(ov1)
            try:
                ov2
            except NameError:
                pass
            else:
                gOval1.delete(ov2)
            try:
                ov3
            except NameError:
                pass
            else:
                gOval1.delete(ov3)
            try:
                ov4
            except NameError:
                pass
            else:
                gOval1.delete(ov4)
            try:
                ov5
            except NameError:
                pass
            else:
                gOval1.delete(ov5)
        
        #Make sure child processes are killed
        try:
            ettusSocket
        except NameError:
            pass
        else:
            #ettusSocket.shutdown(SHUT_RDWR)
            ettusSocket.close()

        try:
            ettusProgram
        except NameError:
            pass
        else:
            ettusProgram.send_signal(signal.SIGINT)
            stdout, stderr = ettusProgram.communicate()
            if (stderr == None):
                print('No errors within subprocess')
            else:
                print(stderr)


# Scale calls functions with an argument, so this is just
# a work around to use the same generateChirp() function
def scaleGenChirp(nata): #Nata holds nothing useful, but it gets rid of an error so...
    generateChirp() 

def generateChirp(): 
    """This generates the chirp with all of the given parameters
    and displays the chirp in the chirp display graph"""
    numSamps = sampFreq * length.get()
    timestep = (length.get() * 1e-6) / (numSamps-1)
    chirp = []
    global ampVolt

    #calculate initial frequency and slope
    initFreq = (float(cf.get() * 1e6) - (float(cf.get() * 1e6) * float(bw.get()) / 200))
    finalFreq = (cf.get() * 1e6) + (cf.get() *1e6 - initFreq)
    freqSlope = (finalFreq - initFreq) / (length.get() * 1e-6) / 2
    ampVolt = math.sqrt((10 ** (float(amp.get()) / 10)) * .001 * cableImpedance) * math.sqrt(2)

    #do actual chirp generation
    curTime = 0
    for intuitive in range(int(numSamps)):
    # ^ its a little counter intuitive, I know.
        chirp.append(ampVolt * math.sin(2*math.pi * 
                (initFreq + freqSlope * curTime) * curTime))
        curTime += timestep
    
    cfvalP2.config(text=str(cf.get()) + " MHz")
    bwvalP2.config(text=str(bw.get()) + "%")
    tlenvalP2.config(text=str(length.get()) + " us")
    ampvalP2.config(text=str(round(ampVolt, 2)) + " mV")
    ampvalP2b.config(text=str(amp.get()) + ' dBm')

    a.cla()
    t = np.linspace(0, length.get(), numSamps)
    a.grid(color='#525252')
    a.plot(t, chirp, 'g')
    chirpCanvas.draw_idle()


def generateResponseGraph(sampVals):
    """Plots the initial response samples. This is only called
    once per transmittion"""
    t = np.linspace(0, traceLength.get(), len(sampVals))
    rfaSub.cla()
    rfaSub.grid(color='#525252')
    rfaSub.use_sticky_edges = False
    rfLine, = rfaSub.plot(t, sampVals, 'g') # Returns a tuple of line objects, thus the comma
    if (maxNum):
        rfaSub.set_ylim(minNum -.05, maxNum + .05)

    rfaCanvas.draw_idle()

    ampFocus = (rfaSub.get_ylim()[1] - rfaSub.get_ylim()[0]) / 2
    ampOffset = (rfaSub.get_ylim()[1] + rfaSub.get_ylim()[0]) / 2
    yAmpP2.delete(0, END)
    yAmpP2.insert(0, ampFocus)
    yOffsetP2.delete(0, END)
    yOffsetP2.insert(0, ampOffset)

    xMinEntry.delete(0, END)
    xMinEntry.insert(0, 0)
    xMaxEntry.delete(0, END)
    xMaxEntry.insert(0, traceLength.get())

    return rfLine

def updateResponseGraph(line, sampVals):
    """Contiously called during transmittion. Updates
    response graph in realtime"""
    line.set_ydata(sampVals)
    rfaCanvas.draw()
    rfaCanvas.flush_events()

def clearRfaGraph():
    """Removes most recently displayed trace"""
    rfaSub.cla()
    rfaSub.grid(color='#525252')
    rfaCanvas.draw_idle()

def resetGraphView():
    """Zoom fits the graph window to see entire trace"""
    rfaSub.set_ylim(minNum -.05, maxNum + .05)
    if (traceLength.get() != 0):
        rfaSub.set_xlim(0, traceLength.get())
    rfaCanvas.draw_idle()

# /end of Funtion definitions


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

page1 = ttk.Frame(mainWindow)
nb.add(page1, text='SETUP')

page2 = ttk.Frame(mainWindow)
nb.add(page2, text='SEND IT')

rows = 0
while (rows <= 28):
    # Column/Row weight affect how they expand with the window size
    if (rows > 24 and rows <= 26):
        page1.rowconfigure(rows, weight=1, minsize=200)
    elif (rows == 24):
        page1.rowconfigure(rows, weight=1, minsize=15)
    elif (rows <= 3):
        page1.rowconfigure(rows, weight=1, minsize=35)
    elif (rows >= 0 and rows < 20):
        page1.rowconfigure(rows, weight=1, minsize=15)
    elif (rows > 26):
        page1.rowconfigure(rows, weight=20)    
    rows += 1

col = 0
while (col < 10):
    # Column/Row weight affect how they expand with the window size
    if  (col == 0):
        page1.columnconfigure(col, weight = 1, minsize=100)
    elif (col == 3):
        page1.columnconfigure(col, weight = 1, minsize=100)
    elif (col < 3):
        page1.columnconfigure(col, weight = 1, minsize=160)
    elif (col == 4):
        page1.columnconfigure(col, weight = 1)
    elif (col > 4 and col <= 6):
        page1.columnconfigure(col, weight = 10, minsize=350)
    else:
        page1.columnconfigure(col, weight = 1)
    col += 1


#*************************************************************************************
#Create main page 

#UA Represent "Comic-Sans-MS 25 bold italic"
msgObj = Message(page1, text = 'University of Arizona\nVervet', 
            font=("Verdana", 25, 'bold'), relief=GROOVE, justify=CENTER, bd=8, fg='darkred') #'Comic 25 bold'
msgObj.config(bg='lightblue', width = 450)
msgObj.grid(row=0,column=0, padx=20, pady=30, rowspan=4, columnspan=4, sticky='WE')


#Top Label and entries
Label(page1, text='Sampling Frequency: ', font="Comic 12 bold italic"
        ).grid(row=5, column=0, columnspan=2, sticky="SWE")
sfValue = Label(page1, text= str(sampFreq) + ' MHz', relief=SUNKEN, bg='White',
            font='Comic 12 bold italic')
sfValue.grid(row=5, column=2, sticky='SW')

Label(page1, text='Trace Length (\u03BCs): ', font="Comic 12 bold italic"
        ).grid(row=6, column=0, columnspan=2, sticky='SWE')
traceLenBox = Entry(page1, bg='pink', textvariable=traceLength, 
            width=7, font='Comic 12 bold italic')
traceLenBox.grid(row=6, column=2, sticky='SW') 

Label(page1, text='Stack Size: ', font="Comic 12 bold italic"
        ).grid(row=7, column=0, columnspan=2, sticky='SWE')
stackBox = Entry(page1, bg='pink', textvariable=stack, 
            width=7, font='Comic 12 bold italic')
stackBox.grid(row=7, column=2, sticky='SW')

traceLenBox.bind('<FocusOut>', setTraceLen)
traceLenBox.bind('<Return>', setTraceLen)
traceLenBox.bind('<KeyRelease>', verifyTraceEntry)
stackBox.bind('<FocusOut>', setStack)
stackBox.bind('<Return>', setStack)
stackBox.bind('<KeyRelease>', verifyStackEntry)

# /end Top labels and entries

#Create widget housing blocks
sliderFrame = Frame(page1)
sliderFrame.grid(row=25, rowspan=2, column=0, columnspan=4)

#Vervet image
vervetDisplay = Canvas(page1, width=200, height=360)
vervetDisplay.grid(row=0,column=5, rowspan=20, columnspan=2, padx=(30,0), 
                pady=30, sticky='NEW')
img = PhotoImage(file="vervet_monkey.png")
vervetDisplay.create_image(60,400, image=img)

#Generate Chirp display
cDisplayLabel = Label(page1, text='Chirp Preview', 
            font="Arial 10 bold italic")

f = Figure(figsize=(5,4), dpi=100)
f.set_facecolor('green')
a = f.add_subplot(111)
a.set_facecolor('black')
t = np.arange(0, 9, 1)
a.plot(t, [1,2,3,4,5,6,7,8,9], 'g')


chirpCanvas = FigureCanvasTkAgg(f, master=page1)
chirpCanvas.draw()
chirpCanvas.get_tk_widget().config(relief=RAISED, bd=8)
chirpCanvas.get_tk_widget().grid(row=25, column=5, rowspan=2, 
                    columnspan=2, padx=30, pady=30, sticky='NSEW')

cDisplayLabel.grid(row=24, column=5, columnspan=2, sticky='NEW')
f.text(.512, .06, 'Time (us)', ha='center', va='center')
f.text(0.06, 0.5, 'Voltage (mV)', ha='center', va='center', rotation='vertical')
#a.tick_params(axis='x', colors='red')
#f.tight_layout()

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
            resolution=10, variable=bw, width=35, length=250, 
            activebackground='lightpink', command=scaleGenChirp,
            tickinterval=50, showvalue=FALSE) #chirp bandwidth (%)
bwScale.set(100)
cfScale = Scale(sliderFrame, from_=10, to=1, troughcolor='cyan',
            variable=cf, width=35, length=250, 
            activebackground='lightpink', command=scaleGenChirp,
            tickinterval=1, showvalue=FALSE) #center frequency (MHz)
lenScale = Scale(sliderFrame, from_=10, to=1, troughcolor='cyan',
            variable=length, width=35, length=250,
            activebackground='lightpink', command=scaleGenChirp,
            tickinterval=1, showvalue=FALSE) #chirp length (microseconds)
ampScale = Scale(sliderFrame, from_=10, to=-10, troughcolor='cyan',
            variable=amp, width=35, length=250,
            activebackground='lightpink', command=scaleGenChirp,
            tickinterval=2, showvalue=FALSE) #amplitude (dBm)
prfScale = Scale(sliderFrame, from_=3, to=1, troughcolor='cyan',
            resolution=.1, variable=prf, width=35, length=250,
            activebackground='lightpink', command=leaveprfSbox,
            tickinterval=.5, showvalue=FALSE) #Pulse repitition frequency (KHz)

bwScale.grid(row=4,column=0, padx=10)
cfScale.grid(row=4,column=1, padx=10)
lenScale.grid(row=4,column=2, padx=10)
ampScale.grid(row=4,column=3, padx=10)
prfScale.grid(row=4,column=4, padx=10)


#create slider value boxes

bwSbox = Spinbox(sliderFrame, from_=-200, to=200, bg='pink', textvariable=bw, 
            justify=CENTER, validate='all', increment=10, width=5,
            highlightthickness=2, borderwidth=4, font='Helvetica 15 bold',
            command=generateChirp)
cfSbox = Spinbox(sliderFrame, from_=1, to=10, bg='pink', textvariable=cf, 
            justify=CENTER, width=5, highlightthickness=2, borderwidth=4,
            font='Helvetica 15 bold', command=generateChirp)
lenSbox = Spinbox(sliderFrame, from_=1, to=10, bg='pink', textvariable=length, 
            justify=CENTER, width=5, highlightthickness=2, borderwidth=4,
            font='Helvetica 15 bold', command=generateChirp)
ampSbox = Spinbox(sliderFrame, from_=-10, to=10, bg='pink', textvariable=amp, 
            justify=CENTER, width=5, highlightthickness=2, borderwidth=4,
            font='Helvetica 15 bold', command=generateChirp)
prfSbox = Spinbox(sliderFrame, from_=1, to=3, bg='pink', textvariable=prf, 
            justify=CENTER, increment=.1, width=5, highlightthickness=2, 
            borderwidth=4, font='Helvetica 15 bold', command=lambda: leaveprfSbox('Return'))

bwSbox.grid(row=5,column=0)
cfSbox.grid(row=5,column=1)
lenSbox.grid(row=5,column=2)
ampSbox.grid(row=5,column=3)
prfSbox.grid(row=5,column=4)

#Set bindings to ensure valid input
bwSbox.bind('<FocusOut>', leavebwSbox)
bwSbox.bind('<Return>', leavebwSbox)
cfSbox.bind('<FocusOut>', leavecfSbox)
cfSbox.bind('<Return>', leavecfSbox)
lenSbox.bind('<FocusOut>', leavelenSbox)
lenSbox.bind('<Return>', leavelenSbox)
ampSbox.bind('<FocusOut>', leaveampSbox)
ampSbox.bind('<Return>', leaveampSbox)
prfSbox.bind('<FocusOut>', leaveprfSbox)
prfSbox.bind('<Return>', leaveprfSbox)


#*************************************************************************************
#PAGE 2
#*************************************************************************************

rows = 0
while (rows < 16):
    if (rows < 14 and rows != 0):
        page2.rowconfigure(rows, weight=0)
    elif (rows == 0):
        page2.rowconfigure(rows, weight=2)
    else:
        page2.rowconfigure(rows, weight=20)
    rows += 1

col = 0
while (col < 25):
    if (col < 16 and col > 8):
        page2.columnconfigure(col, weight = 5, minsize=50)
    elif (col == 0):
        page2.columnconfigure(col, weight = 1, minsize=90)
    elif (col < 3):
        page2.columnconfigure(col, weight = 1, minsize=60)
    elif (col == 16):
        page2.columnconfigure(col, weight = 1, minsize=88)
    elif (col < 20):
        page2.columnconfigure(col, weight = 1, minsize=80)
    elif (col == 3 or col == 16):
        page2.columnconfigure(col, weight = 15, minsize=60)
    else:
        page2.columnconfigure(col, weight = 15, minsize=10)
    col += 1



# PAGE 2 Sections 

# RF response graph
graphsCanvas = Canvas(master=page2, relief=FLAT, bd=0, highlightthickness=0)

rfaLabel = Label(page2, text='RFA RX', font="Arial 16 bold italic")
rfaFigure = Figure(figsize=(12,4.5), dpi=100)
rfaFigure.set_facecolor('#696969')
rfaSub = rfaFigure.add_subplot(111)
rfaSub.set_facecolor('black')
rfaSub.grid(color='#525252')

rfaCanvas = FigureCanvasTkAgg(rfaFigure, master=graphsCanvas)
rfaCanvas.draw()
rfaCanvas.get_tk_widget().config(relief=GROOVE, bd=18)
rfaCanvas.get_tk_widget().pack()

rfaFigure.text(.512, 0.05, 'Time (us)', ha='center', va='center')
rfaFigure.text(0.06, 0.5, 'Voltage (mV)', ha='center', va='center', rotation='vertical')
# /RF response graph

#create send animation 
sendLabel = Label(page2, text="Stopped: ", font="Arial 12 bold", relief=RAISED,
                fg='#d90000', bg='black')

ovInitX = 5
ovInitY = 5
ovSize = 15
ovDist = 10
gOval1 = Canvas(page2, width=75, height=20)


# Buttons
transmitB = Button(page2, text = 'Transmit', fg ='black', font='Times 18 ', 
                bg='#4beb3d', height=1, width=1, command=transmitAnimate)
stopB = Button(page2, text = 'STOP', fg='black', font='Times 18',
                bg='#cf0e0a', height=1, width=1, command=transmitStop)
clearButt = Button(page2, text = 'Clear Graph', fg='black', font='Times 15', bg='#bdbebf', 
        height=1, width=1, command=clearRfaGraph)
clearButt.grid(row=10, column=8, columnspan=3, sticky='NESW', pady=(10, 0), padx=(30,0))
Button(page2, text='Zoom Fit', fg='black', font='Times 15', bg='#bdbebf',
        height=1, width=1, command=resetGraphView).grid(row=10,
        column=11, columnspan=3, sticky='NEWS', pady=(10,0), padx=(30,0))
# /Buttons

# Chirp Values Display
cvalFrame = Frame(page2, bg='#9abdf5', bd=3, cursor='dot', relief=SOLID)

bwLabelP2 = Label(cvalFrame, text="Bandwidth: ", font="Arial 12 bold", bg='#9abdf5') ##385363
cfLabelP2 = Label(cvalFrame, text="Center Freq: ", font="Arial 12 bold", bg='#9abdf5')
timeLengthLabelP2 = Label(cvalFrame, text="Time Length: ", font="Arial 12 bold", 
                    bg='#9abdf5')
ampLabelP2 = Label(cvalFrame, text="Amplitude: ", font="Arial 12 bold", bg='#9abdf5')
ampLabelP2b = Label(cvalFrame, text="Amplitude: ", font="Arial 12 bold", bg='#9abdf5')
prfLabelP2 = Label(cvalFrame, text="Pulse Rep Freq: ", font="Arial 12 bold", bg='#9abdf5')
sfLabelP2 = Label(cvalFrame, text="Sampling Freq: ", font="Arial 12 bold", bg='#9abdf5')
traceLenLabelP2 = Label(cvalFrame, text="Trace Length: ", font="Arial 12 bold", bg='#9abdf5')
stackLabelP2 = Label(cvalFrame, text="Stack Size: ", font="Arial 12 bold", bg='#9abdf5')

bwvalP2 = Label(cvalFrame, text=str(bw.get()) + "%", font="Arial 12 bold", bg='white',
                relief=SUNKEN, borderwidth=3)
cfvalP2 = Label(cvalFrame, text=str(cf.get()) + " MHz", font="Arial 12 bold", bg='white',
                relief=SUNKEN, borderwidth=3)
tlenvalP2 = Label(cvalFrame, text=str(length.get()) + " us", font="Arial 12 bold", bg='white',
                relief=SUNKEN, borderwidth=3)
ampvalP2 = Label(cvalFrame, text=str(round(ampVolt, 3)) + " mV", font="Arial 12 bold", bg='white',
                relief=SUNKEN, borderwidth=3)
ampvalP2b = Label(cvalFrame, text=str(round(amp.get(), 3)) + " dBm", font="Arial 12 bold", bg='white',
                relief=SUNKEN, borderwidth=3)
prfvalP2 = Label(cvalFrame, text=str(prf.get()) + " KHz", font="Arial 12 bold", bg='white',
                relief=SUNKEN, borderwidth=3)
sfvalP2 = Label(cvalFrame, text=str(sampFreq) + " MHz", font="Arial 12 bold", bg='white',
                relief=SUNKEN, borderwidth=3)
traceLenValP2 = Label(cvalFrame, text=str(traceLength.get()), font="Arial 12 bold", bg='white',
                relief=SUNKEN, borderwidth=3)
stackvalP2 = Label(cvalFrame, text=str(stack.get()), font="Arial 12 bold", bg='white',
                relief=SUNKEN, borderwidth=3)
# /Chirp Values Display

# Window focus thingys
graphFocusFrame = Frame (page2, bg='#9abdf5', bd=3, cursor='dot', relief=SOLID)

Label(graphFocusFrame, text='Y Amp: ', bg='#9abdf5', font="Comic 10 bold italic"
        ).grid(row=0,column=0, sticky='W', padx=(4,0), pady=(4,0))
yAmpP2 = Entry(graphFocusFrame, bg='pink', textvariable=yAmpFocus,
            width=5, font='Comic 10 bold italic')
yAmpP2.delete(0, END)
yAmpP2.insert(0, '0')
yAmpP2.grid(row=0, column=1, padx=(0,2), pady=(4,0)) 
Label(graphFocusFrame, text='Y Offset: ', bg='#9abdf5', font="Comic 10 bold italic"
        ).grid(row=1,column=0, sticky='W', padx=(4,0))
yOffsetP2 = Entry(graphFocusFrame, bg='pink', textvariable=yOffsetFocus,
            width=5, font='Comic 10 bold italic')
yOffsetP2.delete(0, END)
yOffsetP2.insert(0, '0')
yOffsetP2.grid(row=1, column=1, padx=(0,2)) 

Label(graphFocusFrame, text='X Min: ', bg='#9abdf5', font="Comic 10 bold italic"
        ).grid(row=2,column=0, sticky='W', padx=(4,0))
xMinEntry = Entry(graphFocusFrame, bg='pink', textvariable=xMinFocus,
            width=5, font='Comic 10 bold italic')
xMinEntry.delete(0, END)
xMinEntry.insert(0, '0')
xMinEntry.grid(row=2, column=1, padx=(0,2)) 
Label(graphFocusFrame, text='X Max: ', bg='#9abdf5', font="Comic 10 bold italic"
        ).grid(row=3,column=0, sticky='W', padx=(4,0))
xMaxEntry = Entry(graphFocusFrame, bg='pink', textvariable=xMaxFocus,
            width=5, font='Comic 10 bold italic')
xMaxEntry.delete(0, END)
xMaxEntry.insert(0, '0')
xMaxEntry.grid(row=3, column=1, padx=(0,2))


yAmpP2.bind('<KeyRelease>', hideFocusError)
yOffsetP2.bind('<KeyRelease>', hideFocusError)
xMinEntry.bind('<KeyRelease>', hideFocusError)
xMaxEntry.bind('<KeyRelease>', hideFocusError)

Button(graphFocusFrame, text = 'Focus', fg='black', font='Comic 11 bold italic',
            bg='#edf7fc', height=1, width=4, command=focusRxGraph
            ).grid(row=4, column=0, columnspan=2, pady=(4,4))
focusEntryError = Label(graphFocusFrame, text='Must enter valid\nnumeric values', 
                        bg='#9abdf5', font="Comic 10 bold italic", fg='red')
focusEntryError.grid(row=5, rowspan=2, column=0, columnspan=2)
focusEntryError.grid_remove()

graphFocusFrame.grid(row=7, column=16, columnspan=2)
# /Window focus thingys

# ettus response values display
Label(page2, text='Traces Received', font="Arial 10 bold italic", relief=SUNKEN, 
    borderwidth=2, bg='#edf7fc').grid(row=10, column=0, columnspan=2,
    sticky='NESW', pady=(10, 0))
Label(page2, text='GPS Sats', font="Arial 10 bold italic", relief=SUNKEN, 
    borderwidth=2, bg='#edf7fc').grid(row=10, column=4, sticky='NESW', pady=(10, 0))
Label(page2, text='Lon', font="Arial 10 bold italic", relief=SUNKEN, 
    borderwidth=2, bg='#edf7fc').grid(row=10, column=5, sticky='NESW', pady=(10, 0))
Label(page2, text='Lat', font="Arial 10 bold italic", relief=SUNKEN, 
    borderwidth=2, bg='#edf7fc').grid(row=10, column=6, sticky='NESW', pady=(10, 0))
Label(page2, text='Elev', font="Arial 10 bold italic", relief=SUNKEN, 
    borderwidth=2, bg='#edf7fc').grid(row=10, column=7, sticky='NESW', pady=(10, 0))


tracesVal = Label(page2, text='0', font="Arial 10 bold italic", relief=SUNKEN, 
    borderwidth=3, bg='#ebebeb')
tracesVal.grid(row=11, column=0, columnspan=2, sticky='NESW')
gpsSatsVal = Label(page2, text='0', font="Arial 10 bold italic", relief=SUNKEN, 
    borderwidth=3, bg='#ebebeb').grid(row=11, column=4, sticky='NESW')
lonVal = Label(page2, text='0', font="Arial 10 bold italic", relief=SUNKEN, 
    borderwidth=3, bg='#ebebeb').grid(row=11, column=5, sticky='NESW')
latVal = Label(page2, text='0', font="Arial 10 bold italic", relief=SUNKEN, 
    borderwidth=3, bg='#ebebeb').grid(row=11, column=6, sticky='NESW')
elevVal = Label(page2, text='0', font="Arial 10 bold italic", relief=SUNKEN, 
    borderwidth=3, bg='#ebebeb').grid(row=11, column=7, sticky='NESW')
# /ettus response values display



#layout
rfaLabel.grid(row=0, column=0, columnspan=3, sticky='NSW', padx = 40, pady=10)
#rfaCanvas.get_tk_widget().grid(row=1,column=0, rowspan=9, columnspan=16, padx=15, sticky='NEWS')
graphsCanvas.grid(row=1,column=0, rowspan=9, columnspan=16, padx=15, sticky='NEWS')

transmitB.grid(row=12, column=0, columnspan=3, padx=30, pady=20, sticky='NESW')
stopB.grid(row=12, column=3, padx=0, pady=20, sticky='NESW')

gOval1.grid(row=13, column=1, columnspan=3, padx=10, sticky='NEW')
sendLabel.grid(row=13, column=0, pady = 3, sticky='NE')


cvalFrame.grid(row=1,column=16, rowspan=6, columnspan=3)

bwLabelP2.grid(row=0, column=0, sticky = "W")
bwvalP2.grid(row=0, column=1, sticky = "W")
cfLabelP2.grid(row=1, column=0, sticky = "W")
cfvalP2.grid(row=1, column=1, sticky = "W")
timeLengthLabelP2.grid(row=2, column=0, sticky = "W")
tlenvalP2.grid(row=2, column=1, sticky = "W")
ampLabelP2.grid(row=3, column=0, sticky = "W")
ampvalP2.grid(row=3, column=1, sticky = "W")
ampLabelP2b.grid(row=4, column=0, sticky = "W")
ampvalP2b.grid(row=4, column=1, sticky="W")
prfLabelP2.grid(row=5, column=0, sticky = "W")
prfvalP2.grid(row=5, column=1, sticky = "W")
sfLabelP2.grid(row=6, column=0, sticky='W')
sfvalP2.grid(row=6, column=1, sticky='W')
traceLenLabelP2.grid(row=7, column=0, sticky="W")
traceLenValP2.grid(row=7, column=1, sticky='W')
stackLabelP2.grid(row=8, column=0, sticky='W')
stackvalP2.grid(row=8, column=1, sticky='W')
# /layout page2



#Infinite loop to for running application
mainWindow.mainloop()


