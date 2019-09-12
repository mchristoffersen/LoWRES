import struct
import matplotlib.pyplot as plt

fname = "./testfile.dat"

with open(fname, mode='rb') as fd: # b is important -> binary
    data = fd.read()

data = struct.unpack("ifdddddddi" + "f" * ((len(data) - 68) // 4), data)

print(data[1:10])
#plt.plot(data) # [::2]) for complex files
#plt.show()
