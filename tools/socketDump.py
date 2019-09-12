#!/home/vervet/anaconda3/bin/python3

import socket
import subprocess
import signal

HOST = '127.0.0.1'  # Standard loopback interface address (localhost)
PORT = 1997        # Port to listen on (non-privileged ports are > 1023)

run = False


with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.bind((HOST, PORT))
    s.listen(1000)
    while True:
        conn, addr = s.accept()
        with conn:
            print('Connected by', addr)
            data = conn.recv(4096)
            if not data:
                continue
            print(data)
