import h5py
import numpy as np
import sys
import matplotlib.pyplot as plt

def pulseCompress(rx0, refchirp):
  pc = np.zeros(rx0.shape).astype("float32")
  C = np.conj(np.fft.fft(refchirp))
  for i in range(rx0.shape[1]):
    t = rx0[:,i]
    T = np.fft.fft(t)
    pc[:,i] = np.fft.ifft(np.multiply(T,C))
  
  return pc

def removeSlidingMeanFFT(rx0):
  mean = np.zeros(rx0.shape)
  sumint = 1000
  a = np.zeros(rx0.shape[1])
  a[0:sumint//2] = 1
  a[rx0.shape[1]-sumint//2:rx0.shape[1]] = 1
  #for i in range(rx0.shape[1]):
  #  if(a[i] == 1):
  #    print(i,a[i])
  A = np.fft.fft(a)

  # Main circular convolution
  for i in range(rx0.shape[0]):
    T = np.fft.fft(rx0[i,:])
    mean[i,:] = np.fft.ifft(np.multiply(T,A))/sumint

  # Handle edges
  mt = np.zeros(rx0.shape[0])
  for i in range(0, sumint):
    mt = np.add(mt, np.divide(rx0[:,i], sumint))

  for i in range(0, sumint//2):
    mean[:,i] = mt

  mt = np.zeros(rx0.shape[0])
  for i in range(rx0.shape[1] - sumint, rx0.shape[1]):
    mt = np.add(mt, np.divide(rx0[:,i], sumint))
  
  for i in range(rx0.shape[1] - sumint//2, rx0.shape[1]):
    mean[:,i] = mt

  rx0NM = np.subtract(rx0, mean)

  return rx0NM

def removeSlidingMean(rx0):
  sumint = 50
  rx0NM = np.zeros(rx0.shape)

  for i in range(rx0.shape[1]): 
    mt = np.zeros(rx0.shape[0])

    if(i < sumint/2):
      for j in range(0, sumint):
        mt = np.add(mt, np.divide(rx0[:,j], sumint))
      rx0NM[:,i] = mt #rx0[:,i] - mt


    elif(i > rx0.shape[1] - sumint//2):
      for j in range(rx0.shape[1] - sumint, rx0.shape[1]):
        mt = np.add(mt, np.divide(rx0[:,j], sumint))
      rx0NM[:,i] = mt #rx0[:,i] - mt

    else:
      for j in range(i-sumint//2, i+sumint//2):
        mt = np.add(mt, np.divide(rx0[:,j], sumint))
      rx0NM[:,i] = mt #rx0[:,i] - mt

  return rx0NM

def removeMean(rx0):
  rx0NM = np.zeros(rx0.shape)
  mt = np.zeros(rx0.shape[0])

  for i in range(rx0.shape[1]): 
    mt = np.add(mt, np.divide(rx0[:,i], rx0.shape[1]))

  for i in range(rx0.shape[1]): 
    rx0NM[:,i] = rx0[:,i] - mt

  return rx0NM

def main():
  f = h5py.File(sys.argv[1], 'a')
  rx0 = f["rx0"][:]
  refchirp = f["tx0"][:,0]

  # Process data
  #mean = removeSlidingMean(rx0)
  rx0NM = removeSlidingMeanFFT(rx0)
  #for i in range(rx0.shape[1]):
  #  print(i, np.sum(meanFFT[:,i] - mean[:,i]))
  rx0NM = np.roll(rx0NM, -105, axis=0)
  pc = pulseCompress(rx0NM, refchirp)
  #pc = removeMean(pc)

  # Save processed dataset
  proc0 = f.require_dataset("proc0", shape=rx0.shape, dtype=np.float32)
  proc0[:] = pc
  proc0.attrs.create("RefChirp", np.string_("tx0"))
  proc0.attrs.create("Notes", np.string_("Mean removed in sliding 500 trace window : -105 sample circ shift to correct for xmit delay"))

  f.close()

main()
