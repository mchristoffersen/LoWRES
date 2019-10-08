import sys
import numpy as np
import struct
import h5py

def parseRaw(fname):
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
    dd["fs"] = int(hdr[8])
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
  
  dd["rx0"] = np.array(dd["rx0"]).astype("float32")

  return dd

def generateChirp(cf, bw, length, fs):
  initFreq = cf - (cf*bw/200)
  freqSlope = (cf*bw/100)/length
  nsamp = int(length*fs)
  t = np.linspace(0, length-1/fs, nsamp)

  c = np.zeros((nsamp,1))
  for i in range(nsamp):
    c[i] = np.cos(-np.pi/2 + 2*np.pi*(initFreq + (freqSlope/2)*t[i])*t[i])

  return c

def main():
  dd = parseRaw(sys.argv[1])
  outf = sys.argv[1].replace(".dat",".h5")
  print(outf)
  f = h5py.File(outf, "w")
  rx0 = f.create_dataset("rx0", data = dd["rx0"]) #, compression="gzip")
  rx0.attrs["fsHz"] = dd["fs"]
  rx0.attrs["traceLengthS"] = dd["traceLen"]
  rx0.attrs["stacking"] = dd["stack"]
  rx0.attrs["samplesPerTrace"] = dd["spt"]
  rx0.attrs["numTraces"] = dd["ntrace"]

  # ref chirp
  chirp = generateChirp(dd["chirpCF"], dd["chirpBW"], dd["chirpLen"], dd["fs"])
  ch = np.zeros((dd["rx0"].shape[0], 1)).astype("float32")
  ch[0:len(chirp)] = chirp
  tx0 = f.create_dataset("tx0", data = ch)
  tx0.attrs.create("chirpCenterFrequencyHz", dd["chirpCF"])
  tx0.attrs["chirpBandwidthPct"] = dd["chirpBW"]
  tx0.attrs["chirpLengthS"] = dd["chirpLen"]
  tx0.attrs["chirpPulseRepetitionFrequencyHz"] = dd["chirpPRF"] 

  f.close()

main()
