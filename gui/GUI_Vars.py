
from tkinter import *
#import tkinter.ttk as ttk
#import numpy as np

class GUI_Vars:
    #chirp variables
    sampFreq = 100 #in MHz
    receiveSampFreq = 100 #in MHz
    cableImpedance = 50 #Ohms

    numReceiveSamps = 1000 #This is the number of samples to receive per burst
    transmitLoop = False

    root = Tk()
    #yAmpP2 yOffsetP2 xMinEntry xMaxEntry
    yAmpFocus = DoubleVar()
    yOffsetFocus = DoubleVar()
    xMinFocus = DoubleVar()
    xMaxFocus = DoubleVar()

    maxNum = 0  #rf graph limits FIXME Probably move to transmit class
    minNum = 0  #rf graph limits

    bw = IntVar()
    cf = IntVar()
    length = IntVar()
    amp = IntVar()
    ampVolt = 0
    prf = DoubleVar()

    traceLength = IntVar()
    stack = IntVar()
    traceLength.set(50) # in microseconds
    stack.set(100)
