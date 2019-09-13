import struct
import matplotlib.pyplot as plt
import sys
fname = sys.argv[1]

with open(fname, mode='rb') as fd: # b is important -> binary
    data = fd.read()

data = struct.unpack("f" * (len(data) // 4),data) #*(len(data)/4)
plt.plot(data) # [::2]) for complex files
plt.show()
