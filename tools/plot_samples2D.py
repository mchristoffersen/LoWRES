import struct
import matplotlib.pyplot as plt
import numpy as np

fname = "./datafile.dat"

with open(fname, mode='rb') as fd: # b is important -> binary
    data = fd.read()

data = struct.unpack("f" * (len(data) // 4),data) #*(len(data)/4)
data = np.array(data)
data = np.reshape(data, (len(data)//5000, 5000))
data = np.transpose(data)
plt.imshow(data) # [::2]) for complex files
plt.show()
