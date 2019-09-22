# LoWRES
Control code for the Long Wavelength Radio Echo Sounder (LoWRES) - C++ for an Ettus X310

General notes:
- Developed on Ubuntu 18.04 with all of the UHD requirements intalled via the apt package manager (libuhd-dev libuhd003 uhd-host)
  - So the Makefile UHDFLAGS will probably need to be modified if you compile from source.
- Developed for an Ettus X310 with the LFTX and LFRX daughterboards, using the dual 10 gig ethernet interface (so the XG fpga image) to communicate with the host computer. The IP addresses of the host computers 10 gig ethernet interfaces must be 192.168.1.30 and 192.168.1.40 for communicating with the X310 ethernet ports 0 and 1, respectively. 
- Pin 5 (Data[3]) on the X310 GPIO is being used to trigger a power amplifier.
- The script init.sh sets several networking settings to take advantage of the 10 gig ethernet. This software was developed on Ubuntu 18.04, changing these settings on another OS probably looks different.
- The software needs four threads - one TX thread, one RX thread, one data handling thread (fed by the RX thread through a pipe), and one ettusDaemon thread (started separately)
- All the python in this project is python3. A conda environment spec is on the way soon.
- Right now several parameters in the software are hard coded for a 2 kHz PRF - other PRFs will not work. Improvements will be made to handle higher PRFs. 

The gui:
The gui can be run on a computer that is not the host computer (for example, a laptop). The remote computer must be on the same network as the host computer and the host computer must have a known (preferrably static) IP address. The gui will communicate with the ettusDaemon, which must be running on the host computer, to start and stop the X310. The IP of the remote computer does not have to be preconfigured - the ettusDaemon listens for connections from any IP and will pass that on to the X310 C++ so that it will send display data back to the right place. Running the gui on the host computer and using X11 forwarding or something similar to get it onto a screen works well too, but the display becomes much less responsive. 

Example params:
./radar --tx-rate 25e6 --rx-rate 100e6 --tx-freq 0 --rx-freq 0 --chirp-cf 5e6 --chirp-bw 100 --chirp-len 5e-6 --chirp-amp 0.31618 --chirp-prf 2000 --trace-len 50e-6 --stack 100

