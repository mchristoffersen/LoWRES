


import numpy as np
import math
import GUI_Vars



# Scale calls functions with an argument, so this is just
# a work around to use the same generateChirp() function
def scaleGenChirp(nata): #Nata holds nothing useful, but it gets rid of an error so...
    generateChirp() 

def generateChirp(): 
    """This generates the chirp with all of the given parameters
    and displays the chirp in the chirp display graph"""
    numSamps = GUI_Vars.GUI_Vars.sampFreq * GUI_Vars.GUI_Vars.length.get()
    timestep = (GUI_Vars.GUI_Vars.length.get() * 1e-6) / (numSamps-1)
    chirp = []

    #calculate initial frequency and slope
    initFreq = (float(GUI_Vars.GUI_Vars.cf.get() * 1e6) - (float(GUI_Vars.GUI_Vars.cf.get() * 1e6)\
        * float(GUI_Vars.GUI_Vars.bw.get()) / 200))
    finalFreq = (GUI_Vars.GUI_Vars.cf.get() * 1e6) + (GUI_Vars.GUI_Vars.cf.get() *1e6 - initFreq)
    freqSlope = (finalFreq - initFreq) / (GUI_Vars.GUI_Vars.length.get() * 1e-6) / 2
    GUI_Vars.GUI_Vars.ampVolt = math.sqrt((10 ** (float(GUI_Vars.GUI_Vars.amp.get())\
         / 10)) * .001 * cableImpedance) * math.sqrt(2)


    #FIXME ***********************************************LEFT OFF HERE *********************************


    #do actual chirp generation
    curTime = 0
    for intuitive in range(int(numSamps)):
    # ^ its a little counter intuitive, I know.
        chirp.append(ampVolt * math.sin(2*math.pi * 
                (initFreq + freqSlope * curTime) * curTime))
        curTime += timestep
    
    cfvalP2.config(text=str(cf.get()) + " MHz")
    bwvalP2.config(text=str(bw.get()) + "%")
    tlenvalP2.config(text=str(GUI_Vars.GUI_Vars.length.get()) + " us")
    ampvalP2.config(text=str(round(ampVolt, 2)) + " mV")
    ampvalP2b.config(text=str(amp.get()) + ' dBm')

    a.cla()
    t = np.linspace(0, GUI_Vars.GUI_Vars.length.get(), numSamps)
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