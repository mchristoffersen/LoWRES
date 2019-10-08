import os
import struct
import numpy as np
import matplotlib.pyplot as plt
import folium

def parseDat(fname):
  print(fname)
  fd = open(fname, 'rb')
  data = fd.read()
  nb = len(data)

  if(data[0:4] != bytes.fromhex("d0d0beef")):
    return -1

  dd = {}

  dd["version"] = struct.unpack('f', data[4:8])[0]

  if(dd["version"] == 1.0):
    hdr = struct.unpack("ifdddddddi", data[0:68])
   
    dd["chirpCF"] = hdr[2]
    dd["chirpBW"] = hdr[3]
    dd["chirpLen"] = hdr[4]
    dd["chirpAmp"] = hdr[5]
    dd["chirpPRF"] = hdr[6]
    dd["traceLen"] = hdr[7]
    dd["fs"] = hdr[8]
    dd["stack"] = hdr[9]
    dd["spt"] = int(dd["traceLen"]*dd["fs"])
    dd["ntrace"] = int((nb - 68)/(56 + dd["spt"]*4));
    dd["rx0"] = np.zeros((dd["spt"], dd["ntrace"])).astype("float")
    dd["lat"] = np.zeros(dd["ntrace"]).astype("float")
    dd["lon"] = np.zeros(dd["ntrace"]).astype("float")
    dd["alt"] = np.zeros(dd["ntrace"]).astype("float")
    dd["dop"] = np.zeros(dd["ntrace"]).astype("float")
    dd["nsat"] = np.zeros(dd["ntrace"]).astype("int32")
    dd["tfull"] = np.zeros(dd["ntrace"]).astype("int64")
    dd["tfrac"] = np.zeros(dd["ntrace"]).astype("double")

    for i in range(dd["ntrace"]):
      ofst = 68 + ((56 + dd["spt"]*4)*i)
      fix = struct.unpack("qqdqffffIi", data[ofst:ofst+56])
      dd["tfull"][i] = fix[1]
      dd["tfrac"][i] = fix[2]
      dd["lat"][i] = fix[4]
      dd["lon"][i] = fix[5]
      dd["alt"][i] = fix[6]
      dd["dop"][i] = fix[7]
      dd["nsat"][i] = fix[8]

      dd["rx0"][:,i] = struct.unpack('f'*dd["spt"], data[ofst+56:ofst+56+dd["spt"]*4])
  
  return dd

def generateChirp(cf, bw, length, fs):
  initFreq = cf - (cf*bw/200)
  freqSlope = (cf*bw/100)/length
  nsamp = int(length*fs)
  t = np.linspace(0, length-1/fs, nsamp)

  c = np.zeros(nsamp)
  for i in range(nsamp):
    c[i] = np.cos(-np.pi/2 + 2*np.pi*(initFreq + (freqSlope/2)*t[i])*t[i])

  return c

def pulseCompress(data):
  data["pc"] = np.zeros((data["spt"], data["ntrace"])).astype("float")
  chirp = generateChirp(data["chirpCF"], data["chirpBW"], data["chirpLen"], data["fs"])
  c = np.zeros(data["spt"])
  c[0:len(chirp)] = chirp
  C = np.conj(np.fft.fft(c))
  for i in range(data["ntrace"]):
    t = data["rx0"][:,i]
    T = np.fft.fft(t)
    data["pc"][:,i] = np.fft.ifft(np.multiply(T,C))
  
  return data

def removeMean(data):
  sumint = 100
  rx0_orig = data["rx0"]

  for i in range(data["ntrace"]): 
    mt = np.zeros(data["spt"])
    if(i < sumint/2):
      for j in range(0, sumint):
        mt = mt + rx0_orig[:,j]/sumint
      #plt.plot(mt)
      #plt.plot(data["rx0"][:,i])
      data["rx0"][:,i] = data["rx0"][:,i] - mt
      #plt.plot(data["rx0"][:,i])
      #plt.show()

    elif(i > data["ntrace"] - sumint//2):
      for j in range(data["ntrace"] - sumint, data["ntrace"]):
        mt = mt + rx0_orig[:,j]/sumint
      data["rx0"][:,i] = data["rx0"][:,i] - mt

    else:
      for j in range(i-sumint//2, i+sumint//2):
        mt = mt + rx0_orig[:,j]/sumint
      data["rx0"][:,i] = data["rx0"][:,i] - mt

  return data

def generateMap(data):

def main():
  fdir = "/home/mchristo/DATA/"
  flist = os.listdir(fdir)

  for i in range(len(flist)):
    fname = flist[i]

    # Skip if not raw data file
    if(fname[-4::] != ".dat"):
      continue

    # Skip if already processed
    if(os.path.exists(fdir + fname.replace(".dat",".mat"))):
      continue

    data = parseDat(fdir + fname)

    data = removeMean(data)
    data = pulseCompress(data)

    plt.imshow(np.log(data["pc"]**2))
    plt.show()

    print(data)


main()
