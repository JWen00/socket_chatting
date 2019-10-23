from socket import *
import select 
import time 
import _thread 
import threading
from clientPacketHander import constructReq, decodeResponse
import sys

class NewClient(): 
    def __init__(self, name): 
        self._name = name
        self._socket = None 
        self.status = "active"
        self._timeout = 0

    def bindSocket(self, socket): 
        self._socket = socket 

    def setTimeout(self, timeout): 
        self._timeout = timeout

    def listen(self): 
        while True: 
            timer = threading.Timer(self._timeout, _thread.interrupt_main) 
            command = None 
            try: 
                command = input(self._name + ": ") 
            except KeyboardInterrupt:
                pass 
            timer.cancel() 
            
            if command == "exit": 
                self._socket.send(constructReq("exit")) 
                self._socket.close() 
                print("ByeBye :)")
                sys.exit()
            else: 
                print("Command Unknown...  YEEeet") 
