import struct
import matplotlib.pyplot as plt
import sys

if(len(sys.argv) != 2):
    print("Invalid num args")
    sys.exit()

with open(sys.argv[1], mode='rb') as fd:
    data = fd.read()

if(data[0:4] != bytes.fromhex("d0d0beef")):
    print("Wrong file type")
    sys.exit()

hdr = struct.unpack("ifdddddddi", data[0:68])

spt = hdr[8]*hdr[7]
bpt = spt*4 + 48
ntrace = (len(data) - 68)/bpt
print(len(data))

print("\nLoWRES Raw Data File")
print("Version:  {}\n".format(hdr[1]))
print("  Chirp:")
print("    Center freq:    {} MHz".format(hdr[2]/1e6))
print("    Bandwidth:      {} %".format(hdr[3]))
print("    Duration:       {} us".format(round(hdr[4]/1e-6, 2)))
print("    Slope:          Linear")
print("    Amplitude:      {} V\n".format(round(hdr[5], 3)))
print("  PRF:            {} kHz".format(hdr[6]/1000))
print("  Trace length:   {} us".format(round(hdr[7]/1e-6, 2)))
print("  Sampling freq:  {} MHz".format(hdr[8]/1e6))
print("  Stacking:       {}\n".format(hdr[9]))
print(hdr[8], hdr[7], hdr[8]*hdr[7], spt, ntrace)

