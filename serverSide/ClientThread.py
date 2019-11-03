import thread 

# Multithreaded Python Server 
class ClientThread(Thread): 
    def __init__(self, ip, port, socket): 
        Thread.__init__(self) 
        self.ip = ip 
        self.port = port 
        self.connectionSocket = socket
        print(f">> New server socket thread started @{self.ip}:{self.port}")

    def run(self): 
        while True: 
            data = connectionSocket.recv(1024) 
            print("received data") 
                
            