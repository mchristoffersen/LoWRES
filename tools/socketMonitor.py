#!/home/vervet/anaconda3/bin/python3

import socket
import subprocess
import signal

HOST = '127.0.0.1'  # Standard loopback interface address (localhost)
PORT = 1998        # Port to listen on (non-privileged ports are > 1023)

run = False


with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.bind((HOST, PORT))
    s.listen(1000)
    while True:
        conn, addr = s.accept()
        with conn:
            print('Connected by', addr)
            data = conn.recv(4096).decode()
            if not data:
                continue
            data = data.split(":::")

            for i in range(len(data)//2):
                ptype = data[i*2]
                pdata = data[i*2+1]
                print(ptype)
                if(ptype == "SRT"):
                    if(run):
                        continue
                    run = True
                    ettusProgram = subprocess.Popen(pdata.split(' '))
                    conn.close()
                elif(ptype == "STP"):
                    if(not run):
                        continue
                    run = False
                    ettusProgram.send_signal(signal.SIGINT)
                    conn.close()
                else:
                    print("Invalid packet type")
                    continue
        
