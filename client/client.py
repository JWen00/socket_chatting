from socket import *
import select 
import sys
import threading
import time
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
        self._isServerActive = True
        
    def listen(self): 
        """ Listening and getting responses """

        newThread = threading.Thread(target=self.listenToOthers)
        newThread.start()

        while newThread.isAlive():

            if self._isServerActive == False: 
                break
            try: 
                data = input(self._username + " >> ") 
                data = data.split(" ") 
                command = data[0]
                args = data[1:] 
                
                # Commands which do not run through the server: "private" and "stopprivate "
                if command == "private": self.privateMessage(args[0], " ".join(args[1:]))
                elif command == "stopprivate": self.stopPrivateMessage(arg[0])
                else: self._serverSocket.send(self.constructReq(command, args)) 
            
            except (KeyboardInterrupt, BrokenPipeError): # TODO: need to manage each broken pip separate 
                print("Connection closed.")
                break

            time.sleep(1.2)

        print("Main thread also dead")

        # Ensure that client leaves their private chats...
        for peerConnection in self._privateChats:
            peerConnection.close()
        
        self._p2pSocket.close()
        self._serverSocket.close()

        

    def listenToOthers(self):
        readList = [self._serverSocket, self._p2pSocket]
        while self._isServerActive: 
            if self._isServerActive == False: break
            readable, writable, errorable = select.select(readList, [], [], 1) 
        
            for connection in readable: 

                # Data arrived from server 
                if connection is self._serverSocket: 
                    try: 
                        response = connection.recv(1024) 
                        status, data = self.decodeResponse(response) 
                    except (ConnectionResetError, SystemError): 
                        self._isServerActive = False
                        break


                    if status == "success" and data["command"] == "startPrivate": 
                        try: 
                            print(f'Connecting to peer ({data["target"]}) @{data["targetAddress"]}...')
                            newPeerConnection = socket(AF_INET, SOCK_STREAM) 
                            newPeerConnection.connect(tuple(data["targetAddress"])) 
                            newPeerConnection.send(self.constructReq("SYN", { 
                                "username" : self._username
                            }))

                            self._privateChats[data["target"]] = newPeerConnection
                            readList.append(newPeerConnection)
                            continue

                        except ConnectionRefusedError: 
                            print("Could not connect to peer, please try again") 
 
                                    
                    if status == "success": print(f'{data["message"]}')
                    elif status == "message": print(f'  <{data["source"]}> {data["message"]}')
                    elif status == "broadcast": print(f'  <<Broadcast>> {data["message"]}')
                    elif status == "serverMessage": print(f' -- Message from Server: {data["message"]} --')
                    elif status == "unknown": print(f'{data["message"]}')
                    elif status == "unsuccessful": print(f'{data["message"]}')
                    else: 
                        print("HERE!") 
                        self._isServerActive = False
                        break

                    
                # Connection Received from other clients 
                elif connection is self._p2pSocket: 
                    newConnection, serverSocketAddr = self._p2pSocket.accept() # Not sure why it's called serverSocketAddr
                    readList.append(newConnection) 
                    print(f"Received new connection from {serverSocketAddr}")
                    data = newConnection.recv(1024) 
                    status, data = self.decodeResponse(data) 
                    if status == "SYN": self._privateChats[data["username"]] = newConnection

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

        print("Thread is dead")


    def login(self, username, password): 
        """ Authenticates a client """ 

        self._serverSocket.send(self.constructReq("login", [username, password]))
        reply = self._serverSocket.recv(1024) 
        status, data = self.decodeResponse(reply)
        
        if status == "success": 
            self._username = username

            # User has unread messages 
            if len(data["unreadMessages"]) > 0: 
                print("============================\n")
                print(f'| You have {len(data["unreadMessages"])} unread messages')
                for message in data["unreadMessages"]: 
                    print(f'|{message}\n')
                print("============================")
            return True

        print(f'Login unsuccessful. {data.get("message")}') 
        if "You've been blocked" in data["message"]: 
            sys.exit()
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
            del self._privateChats[target]
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

        if not response: 
            raise SystemError
        response = response.decode() 
        response = json.loads(response) 
        status = response.get("status") 
        data = response.get("data") 
        return status, data 
        
        
