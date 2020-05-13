import socket
import subprocess

etip = "192.168.2.35"

def main():
  controller = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  controller.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
  controller.bind((etip, 1997))
  controller.listen()
  
  listen = True
  running = False

  proc = None

  while listen:
    conn, addr = controller.accept()
    cmd = conn.recv(4096).decode()

    if("SRT:::" in cmd and not running):
      conn.send("SRT".encode())
      running = True
      cmd = cmd.split(":::")[1].split(' ')
      cmd.append("--ip-display")
      cmd.append(addr[0])
      proc = subprocess.Popen(cmd)
      #print(cmd.split(":::")[1].split(' '))
      
    elif("STP:::" in cmd and running):
      conn.send("STP".encode())
      running = False
      proc.terminate()
      #print("STOP!")

    else:
      conn.send("INV".encode())
      print("Invalid command")

    conn.close()

main()
