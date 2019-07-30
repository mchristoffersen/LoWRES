# LoWRES
Control code for the Long Wavelength Radio Echo Sounder (LoWRES) - C++ for an Ettus X310

Important notes:
- Developed on Ubuntu 18.04 with all of the UHD requirements intalled via the apt package manager (libuhd-dev libuhd003 uhd-host)
  - So the Makefile UHDFLAGS will probably need to be modified if you compile from source.
- Developed for an Ettus X310 with the LFTX and LFRX daughterboards, using the PCIe x4 interface to communicate with the host computer.
- Pin 5 (Data[3]) on the X310 GPIO is being used to trigger a power amplifier.

Example params:
./radar --tx-rate 25e6 --rx-rate 100e6 --tx-freq 0 --rx-freq 0 --chirp-cf 5e6 --chirp-bw 100 --chirp-len 5e-6 --chirp-amp 0.31618 --chirp-prf 2000 --trace-len 50e-6 --stack 100

