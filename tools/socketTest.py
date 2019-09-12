#!/home/vervet/anaconda3/bin/python3

import socket
import time

HOST = '127.0.0.1'  # The server's hostname or IP address
PORT = 1997        # The port used by the server

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect((HOST, PORT))
    s.sendall(b'SRT:::/home/vervet/LoWRES/radar --tx-rate 25e6 --rx-rate 100e6 --tx-freq 0 --rx-freq 0 --chirp-cf 2.5e6 --chirp-bw 100 --chirp-len 5e-6 --chirp-amp 0.31618 --chirp-prf 2000 --trace-len 50e-6 --stack 100:::')
    time.sleep(100)


with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect((HOST, PORT))
    s.sendall(b'STP::::::')
