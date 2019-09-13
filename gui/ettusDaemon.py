import socket
import subprocess

def main():
  controller = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  controller.bind(("localhost", 1997))
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
      
    elif("STP:::" in cmd and running):
      running = False
      proc.terminate()

main()
