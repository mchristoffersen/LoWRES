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
  
  dd["rx0"] = np.array(dd["rx0"]).astype(np.float32)

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

def h5build(dd, fname):
  f = h5py.File(fname, "w")
  # rx0 dataset
  rx0 = f.create_dataset("rx0", data = dd["rx0"], dtype=np.float32) #, compression="gzip")
  rx0.attrs.create("fsHz", dd["fs"], dtype=np.uint64)
  rx0.attrs.create("traceLengthS", dd["traceLen"], dtype=np.float64)
  rx0.attrs.create("stacking", dd["stack"], dtype=np.uint64)
  rx0.attrs.create("samplesPerTrace", dd["spt"], dtype=np.uint64)
  rx0.attrs.create("numTraces", dd["ntrace"], dtype=np.uint64)

  # ref chirp
  chirp = generateChirp(dd["chirpCF"], dd["chirpBW"], dd["chirpLen"], dd["fs"])
  ch = np.zeros((dd["rx0"].shape[0], 1)).astype("float32")
  ch[0:len(chirp)] = chirp

  # tx0 dataset
  tx0 = f.create_dataset("tx0", data = ch, dtype=np.float32)
  tx0.attrs.create("chirpCenterFrequencyHz", dd["chirpCF"], dtype=np.float64)
  tx0.attrs.create("chirpBandwidthPct", dd["chirpBW"], dtype=np.float64)
  tx0.attrs.create("chirpLengthS", dd["chirpLen"], dtype=np.float64)
  tx0.attrs.create("chirpPulseRepetitionFrequencyHz", dd["chirpPRF"], dtype=np.float64)

  # loc dataset
  loc_t = np.dtype([('lat', np.float32),
                    ('lon', np.float32),
                    ('altM', np.float32),
                    ('DOP', np.float32),
                    ('nsat', np.uint8)])
  locList = [None]*dd["ntrace"]
  for i in range(dd["ntrace"]):
    locList[i] = (dd["lat"][i], dd["lon"][i], dd["alt"][i], dd["dop"][i], dd["nsat"][i])
  locList = np.array(locList, dtype=loc_t)
  loc0 = f.create_dataset("loc0", data=locList, dtype=loc_t)
  loc0.attrs.create("CRS", np.string_("WGS84"))

  # time dataset 
  time_t = np.dtype([('fullS', np.uint64),
                     ('fracS', np.float64)])
  timeList = [None]*dd["ntrace"]
  for i in range(dd["ntrace"]):
    timeList[i] = (dd["tfull"][i], dd["tfrac"][i])
  timeList = np.array(timeList, dtype=time_t)
  time0 = f.create_dataset("time0", data=timeList, dtype=time_t)
  time0.attrs.create("Clock", np.string_("GPS"))

  f.close()

def main():
  dd = parseRaw(sys.argv[1])
  outf = sys.argv[1].replace(".dat",".h5")
  print(outf)
  h5build(dd, outf)

main()
