

from tkinter import *
import tkinter.font as font
import socket
import select
import time
import sys
import GUI_Vars
import create_GUI_Pages

# Ensure safe exit from all running processes
# safely kills child process (smother it with a pillow)
exitFlag = False
def on_quit(): 
    global exitFlag
    exitFlag = True
    #transmitStop()
    mainWindow.destroy()

def main():
    global mainWindow
    
    

    #Main GUI window
    mainWindow = GUI_Vars.GUI_Vars.root
    mainWindow.protocol("WM_DELETE_WINDOW", on_quit)
    GUIpages = create_GUI_Pages.GUI_Pages(mainWindow)
    GUIpages.createPage1()
    mainWindow.mainloop()




if __name__ == '__main__':
    main()











# Create a TCP/IP socket
# server_address = ('localhost', 4747)
# socks = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# socks.connect(server_address)

# msg = B'Start'
# try: socks.send(msg)
# except:
#     pass
# else:
#     print('Sent Start')
# time.sleep(3)
# msg = B'Stop'
# try: socks.send(msg)
# except:
#     pass
# else:
#     print('Stop Program')

# time.sleep(3)
# msg = B'End connection'
# try: socks.send(msg)
# except:
#     pass
# else:
#     print('End connection')  
# socks.close()
# END OF TCP SOCKET CONNECTION