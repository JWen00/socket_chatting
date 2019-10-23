from socket import *
import select 
import time, threading

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
        while self.status == "active": 
            command = raw_input(self.name + ": ")
            
            # Use select with timeout 
        self.socket.close()


# import time, threading
# def foo():
#     print(time.ctime())
#     threading.Timer(10, foo).start()

# foo()