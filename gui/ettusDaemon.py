import socket
import subprocess

ltip = "192.168.1.75"
etip = "192.168.1.35"

#litp = "localhost"
#etip = "localhost"

def main():
  controller = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  controller.bind((etip, 1997))
  controller.listen()
  
  listen = True
  running = False

  proc = None

  while listen:
    conn, addr = controller.accept()        
    cmd = conn.recv(4096).decode()
    conn.close()

    if("SRT:::" in cmd and not running):
      running = True
      proc = subprocess.Popen(cmd.split(":::")[1].split(' '))
      #print(cmd.split(":::")[1].split(' '))
      
    elif("STP:::" in cmd and running):
      running = False
      proc.terminate()
      #print("STOP!")

main()
