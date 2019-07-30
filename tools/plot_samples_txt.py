import struct
import matplotlib.pyplot as plt

fname = "./chirp.txt"

with open(fname, mode='r') as fd: # b is important -> binary
    data = fd.read()

data = data.split("\n")
data = filter(None, data)

for i in range(len(data)):
    data[i] = float(data[i])

plt.plot(data)
plt.show()
