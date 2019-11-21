from socket import *
import select 
import sys
import threading
import time
import json

class Client(): 
    def __init__(self, serverName, serverPort): 
        """ Loads 2 sockets """

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

            if self._isServerActive == False: break
            try: 

                data = input() 
                data = data.split(" ") 
                command = data[0]
                args = data[1:] 
                
                # Commands which do not run through the server: "private" and "stopprivate "
                if command == "private": self.privateMessage(args)
                elif command == "stopprivate": self.stopPrivateMessage(args)
                else: self._serverSocket.send(self.constructReq(command, args)) 
            
            except (KeyboardInterrupt, BrokenPipeError): 
                break

            time.sleep(0.7)

        # Ensure that client leaves their private chats...
        for peerConnection in self._privateChats:
            self._privateChats[peerConnection].send(self.constructReq("private", { 
                "sender" : self._username, 
                "message" : "Private chat is being closed."
            }))
            self._privateChats[peerConnection].close()
        
        # Close client's private socket
        self._p2pSocket.close()
        self._serverSocket.close()
        print("Connection closed") 


    def listenToOthers(self):
        """ Listen to the server, it's own private server and other connections made to private server """

        readList = [self._serverSocket, self._p2pSocket]
        while self._isServerActive:

            try:
                readable, writable, errorable = select.select(readList, [], [], 1) 
            except (ConnectionResetError, OSError, SystemError, ValueError): 
                break  

            for connection in readable: 

                # Data arrived from server 
                if connection is self._serverSocket: 
                    response = connection.recv(1024) 
                    status, data = self.decodeResponse(response)

                    # logout request approved
                    if status == "logout": 
                        self._isServerActive = False 
                        break

                    # Startprivate request approved by the server 
                    if status == "success" and data["command"] == "startPrivate": 

                        # Connection with target exists 
                        if data["target"] in self._privateChats: 
                            print(f'>> Private chat exists with {data["target"]}')
                            continue 

                        try: 
                            print(f'Connecting to peer ({data["target"]}) @{data["targetAddress"]}...')
                            newPeerConnection = socket(AF_INET, SOCK_STREAM) 
                            newPeerConnection.connect(tuple(data["targetAddress"])) 
                            newPeerConnection.send(self.constructReq("SYN", { 
                                "sender" : self._username
                            }))

                            self._privateChats[data["target"]] = newPeerConnection
                            print(f'Added new connection! You can private message {data["target"]}now.')
                            readList.append(newPeerConnection)
                        except ConnectionRefusedError: 
                                print("Could not connect to peer, please try again") 

                        continue
                                
                    if status == "success": print(f'>> {data["message"]}')
                    elif status == "message": print(f'<{data["source"]}> {data["message"]}')
                    elif status == "broadcast": print(f'<<Broadcast from {data["sender"]}>> {data["message"]}')
                    elif status == "serverMessage": print(f'>> {data["message"]}')
                    elif status in ["unknown", "unsuccessful"] : print(f'>> {data["message"]}')
                    else: break
                    continue
                    
                # Connection Received from other clients 
                elif connection is self._p2pSocket: 
                    newConnection, serverSocketAddr = self._p2pSocket.accept()
                    
                    data = newConnection.recv(1024) 
                    status, info = self.decodeResponse(data)     
                    readList.append(newConnection) 
                    self._privateChats[info["sender"]] = newConnection
                    print(f'<{info["sender"]}> started a private connection. You can private message them now.')
                    continue 

                # Data received from other clients 
                data = connection.recv(1024) 
                if not data: 
                    print(f"Peer connection from {connection.getsockname()} was closed.")
                    readList.remove(connection)
                    continue
 
                status, data =  self.decodeResponse(data)
                print(f'PRIVATE <<{data["sender"]}>> {data["message"]}')

    def login(self, username, password): 
        """ Authenticates a client """ 

        self._serverSocket.send(self.constructReq("login", [username, password]))

        try: 
            reply = self._serverSocket.recv(1024) 
            status, data = self.decodeResponse(reply)
        except (SystemError, ConnectionResetError): 
            print("There's an error on the server side. Connection closed") 
            sys.exit()
        
        if status == "success": 
            self._username = username
            print(f"Login success! Welcome {username}")

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

    def privateMessage(self, data): 
        """ Private message - Does not pass through client """

        # Need 2 arguments 
        if len(data) < 2: 
            print("Missing arguments for private message")
            return 
        
        targetName = data[0]
        message = " ".join(data[1:])

        # Cannot send empty string 
        if message == "": 
            print(">> Error, cannot send empty string") 
            return 

        # Cannot send private to self 
        if targetName == self._username: 
            print(">> Cannot private message youself") 
            return

        try: 
            targetSocket = self._privateChats[targetName]
            targetSocket.send(self.constructReq("private", { 
                "sender" : self._username, 
                "message" : message 
            }))
            print(f">> Private message has been sent to {targetName}")
        except KeyError: 
            print(f'>> Private chat not established for {targetName}')
    
    def stopPrivateMessage(self, data): 
        """ Stops an already established private chat """ 
        
        if len(data) < 1: 
            print(">> Missing argument for stop private") 
            return

        try: 
            targetName = data[0]
            targetSocket = self._privateChats[targetName]
            targetSocket.send(self.constructReq("private", { 
                "sender" : self._username, 
                "message" : "Private chat is being closed."
            }))
            # targetSocket.close()
            del self._privateChats[targetName]
            print(f'Chat with {targetName} closed.')
            
        except KeyError: 
            print(f'>> No private chat exists for {targetName}')

    def constructReq(self, command, data=[]): 
        """ Constructs a response to follow the protocol """

        req = {} 
        req["command"] = command 
        req["data"] = data
        req = json.dumps(req) 
        req = req.encode() 
        return req 

    def decodeResponse(self, response): 
        """ Decodes the response according to the protocol """
        if not response: 
            # raise SystemError
            sys.exit()

        response = response.decode() 
        response = json.loads(response) 
        status = response.get("status") 
        data = response.get("data") 
        return status, data 
        
        
