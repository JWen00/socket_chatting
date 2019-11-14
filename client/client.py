from socket import *
import select 
import sys
import threading
import json

class Client(): 
    def __init__(self, serverName, serverPort): 
        try: 
            self._serverSocket = socket(AF_INET, SOCK_STREAM)
            self._serverSocket.connect((serverName, serverPort)) 
            self._serverSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        except ConnectionRefusedError: 
            print("Server is not up yet") 
            sys.exit() 

        try: 
            p2pPort = self._serverSocket.getsockname()[1]

            self._p2pSocket = socket(AF_INET, SOCK_STREAM) 
            self._p2pSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self._p2pSocket.bind((serverName, p2pPort))
            self._p2pSocket.listen(1) 

        except ConnectionRefusedError: 
            print("Cannot listen on 0.0.0.0")
            sys.exit() 
        
    def listen(self): 
        """ Main thread for listening and second for getting responses """

        t = threading.Thread(target=self.listenToOthers) 
        t.start()  

        def getCommand():  
            try: 
                data = input(self._name + " >> ") 
            except Exception:
                self._serverSocket.close()
                print("\nExiting...\nConnection closed.")
                sys.exit()
            
            data = data.split(" ") 
            command = data[0]
            args = data[1:] 
            
            # Commands which do not run through the server: "private" and "stopprivate "
            if command is "private": 
                pass
            elif command is "stopprivate": 
                pass 
            else: 
                self._serverSocket.send(self.constructReq(command, args)) 
            
        
        while True: 
            getCommand() 

    def listenToOthers(self): 
        """ Listen to server, but also to incoming private connections """ 

        readList = [self._serverSocket, self._p2pSocket]
        while True:
            readable, writable, errorable = select.select(readList, [], []) 
            for connection in readable: 

                # Data arrived from server 
                if connection is self._serverSocket: 
                    response = self._serverSocket.recv(1024) 
                    status, data = self.decodeResponse(response) 

                    if data["command"] == "startprivate": 
                        pass
                        
                        # Make a connection with the given information
                    elif data["command"] == "exit": 
                        self._serverSocket.close() 
                        print("Exiting...\nConnection closed.")
                        sys.exit()

                    if status == "success": print("Success! " + data["message"])
                    elif status == "message": print(f'  <{data["source"]}> {data["message"]}')
                    elif status == "broadcast": print(f"=== Broadcast ===\n{data["message"]}\n")
                    else: print(f'Command {data["command"]} unsuccessful\nError message: {data["message"]}')
                
                # Connection Received from other clients 
                elif connection is self._p2pSocket: 
                    newConnection, serverSocketAddr = self._p2pSocket.accept() # Not sure why it's called serverSocketAddr
                    readList.append(newConnection) 
                    print(f"Received connection from {serverSocketAddr}")

                # Data received from other clients 
                else: 
                    data = connection.recv(1024) 
                    if not data: 
                        print(f"Peer connection from {connection.getsockname()} was closed.")
                        readList.remove(connection)
                    else: 
                        status, data =  self.decodeResponse(data) 
                        if status == "privateMessage": print(data["message"])
                        # Disregard everything else. 

 
    def constructReq(self, command, data): 
        req = {} 
        req["command"] = command 
        req["data"] = data
        req = json.dumps(req) 
        req = req.encode() 
        return req 

    def decodeResponse(self, response): 
        try: 
            response = response.decode() 
            response = json.loads(response) 
        except: 
            print("Server Error") 
            sys.exit()
            
        status = response.get("status") 
        data = response.get("data") 
        return status, data 

    def login(self, username, password): 
        self._serverSocket.send(self.constructReq("login", [username, password]))
        reply = self._serverSocket.recv(1024) # Blocking code 
        status, data = self.decodeResponse(reply)
        
        if status == "success": return True
        print(f'Login unsuccessful: {data.get("message")}') 
        return False
