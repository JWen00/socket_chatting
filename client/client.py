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
            self._serverSocket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        except ConnectionRefusedError: 
            print("Server is not up yet") 
            sys.exit() 

        try: 
            p2pPort = self._serverSocket.getsockname()[1]

            self._p2pSocket = socket(AF_INET, SOCK_STREAM) 
            self._p2pSocket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
            self._p2pSocket.bind(("0.0.0.0", p2pPort))
            self._p2pSocket.listen(1) 

        except ConnectionRefusedError: 
            print("Cannot listen on 0.0.0.0")
            sys.exit()

        self._privateChats = {} 
        self.username = None 
        
    def listen(self): 
        """ Listening getting responses """
        readList = [self._serverSocket, self._p2pSocket]

        def getCommand():  
            try: 
                data = input(self._username + " >> ") 
            except Exception:
                self._serverSocket.close()
                print("\nExiting...\nConnection closed.")
                sys.exit()
            
            data = data.split(" ") 
            command = data[0]
            args = data[1:] 
            
            # Commands which do not run through the server: "private" and "stopprivate "
            if command is "private": self.privateMessage(args[0], " ".join(args[1:]))
            elif command is "stopprivate": self.stopPrivateMessage(arg[0])
            else: self._serverSocket.send(self.constructReq(command, args)) 

        def listenToOthers(): 
            readable, writable, errorable = select.select(readList, [], []) 
            for connection in readable: 

                # Data arrived from server 
                if connection is self._serverSocket: 
                    response = connection.recv(1024) 
                    status, data = self.decodeResponse(response) 

                    if status == "success": print("\nSuccess! " + data["message"])
                    elif status == "message": print(f'\n  <{data["source"]}> {data["message"]}')
                    elif status == "broadcast": print(f'\n=== Broadcast ===\n{data["message"]}\n')
                    elif status == "serverMessage": print(f'\n -- Message from Server: {data["message"]} --')
                    else: print(f'\nCommand {data["command"]} unsuccessful. {data["message"]}')
                
                    if status == "success" and data["command"] == "startPrivate": 
                        try: 
                            print(f'Connecting to peer ({data["target"]}) @{data["targetAddress"]}...')
                            newPeerConnection = socket.socket(AF_INET, SOCK_STREAM) 
                            newPeerConnection.connect((data["targetAddress"])) 
                            newPeerConnection.send("SYN", self._username)
                            self._privateChats[target] = newPeerConnection
                            readList.append(newPeerConnection)

                        except ConnectionRefusedError: 
                            print("Could not connect to peer, please try again") 

                        
                    elif status == "success" and data["command"] == "exit": 
                        # self._serverSocket.close() # TODO:
                        print("Exiting...\nConnection closed.")
                        sys.exit()

                    
                # Connection Received from other clients 
                elif connection is self._p2pSocket: 
                    newConnection, serverSocketAddr = self._p2pSocket.accept() # Not sure why it's called serverSocketAddr
                    readList.append(newConnection) 
                    print(f"Received new connection from {serverSocketAddr}")
                    data = newConnection.recv(1024) 
                    status, peerName = self.decodeResponse(data) 
                    if status == "SYN": self._privateChats[peerName] = newConnection

                # Data received from other clients 
                else: 
                    data = connection.recv(1024) 
                    if not data: 
                        print(f"Peer connection from {connection.getsockname()} was closed.")
                        readList.remove(connection)
                    else: 
                        status, data =  self.decodeResponse(data) 
                        if connection not in self.privateChats:
                            self.privateChats[data["source"]] = connection
                        if status == "privateMessage": print(f'  PRIVATE <<{data["source"]}>> {data["message"]}')
                        # Disregard everything else. 

        while True: 
            getCommand() 
            listenToOthers()

        

    def login(self, username, password): 
        self._serverSocket.send(self.constructReq("login", [username, password]))
        reply = self._serverSocket.recv(1024) # Blocking code 
        status, data = self.decodeResponse(reply)
        
        if status == "success": 
            self._username = username
            print("Login Success!")

            # User has unread messages 
            if len(data["unreadMessages"]) > 0: 
                print("============================\n")
                print(f'| You have {len(data["unreadMessages"])} unread messages')
                for message in data["unreadMessages"]: 
                    print(f'| {message}\n')
                print("============================")
            return True
        print(f'Login unsuccessful: {data.get("message")}') 
        return False

    def privateMessage(self, target, message): 
        try: 
            targetSocket = self._privateChats[target]
            targetSocket.send(self.constructReq("privateMessage", { 
                "sender" : self._username, 
                "message" : message 
            }))
        except KeyError: 
            print(f'Private chat not established for {target}')
    
    def stopPrivateChat(self, target): 
        try: 
            targetSocket = self._privateChats[target]
            # targetSocket.close() # ISSUE: File descriptor Error
            del self._privateChats[privateChat]
            print(f'Chat with {target} closed.')
        except KeyError: 
            print(f'No private chat exists for {target}')

    def constructReq(self, command, data=[]): 
        req = {} 
        req["command"] = command 
        req["data"] = data
        req = json.dumps(req) 
        req = req.encode() 
        return req 

    def decodeResponse(self, response): 
        response = response.decode() 
        response = json.loads(response) 
        status = response.get("status") 
        data = response.get("data") 
        return status, data 
