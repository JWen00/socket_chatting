
from .PrimitiveMessaging import *
class Server(): 
    def __init__(self, serverName, serverPort, blockDuration, timeout): 
        try:
            self._serverSocket = socket(AF_INET, SOCK_STREAM) 
            self._serverSocket.bind((serverName, serverPort))
            self._serverSocket.listen(1) 
            print(f"Server listening on {serverName} : {serverPort}...")
        except OSError:
            print(f"Port busy!")
            sys.exit() 

        self._blockDuration = blockDuration
        self._timeout = timeout
        self._readList = []
        self._manager = ClientManager(blockDuration)

    def listen(self): 
        """ Server listens to all incoming information until closed """

        self._readList = [self._serverSocket]
        while True: 
            readable, writable, errorable = select.select(self._readList, [], [])
            for s in readable: 

                # Receiving new connections 
                if s is self._serverSocket: 
                    connection, addr = self._serverSocket.accept() 
                    self._readList.append(connection) 
                    print("New connection @" + str(addr))
                
                # Receiving data from made connections 
                else: 
                    try: 
                        incomingPacket = s.recv(1024) 
                        command, data = self.decodeReq(incomingPacket)
                        data.append(s)

                    # Client left without informing
                    except ConnectionResetError:
                        try: 
                            client = self._manager.getClientBySocket(s) 
                            self.broadcast(f'{client["username"]} has left the server.', client["username"
                            ])
                        except ErrorClientNotFound:
                            pass 
                        self._readList.remove(s) 

                    # Calculate client timeout
                    if not incomingPacket:
                        try: 
                            client = self._manager.getClientBySocket(s) 
                            if time.monotonic() - client["lastActive"] > self._timeout: 
                                print(f'<{client["username"]} has timed out')
                                self.closeClientConnection([socket])
                        except ErrorClientNotFound: 
                            pass
                        continue

                    # Special Case for client logout
                    if command == "logout": 
                        status, info = self.closeClientConnection(s) 
                        s.send(self.constructResponse((status, info))) 
                        if status == "success": self._readList.remove(s) 
                    
                    else: s.send(self.processCommand(command, data))
     
    def processCommand(self, command, data): 
        """ Redirects client to appropriate command """ 

        commands = { 
            "login" : self.authenticate,
            "broadcast" : self.produceBroadcasts, 
            "whoelse" : self.whoElse, 
            "whoelsesince" : self.whoElseSince, 
            "block" : self.blockUser, 
            "unblock" : self.unblockUser, 
            "startprivate" : self.startPrivate,
            "message" : self.message,  
        }

        if not command in commands: 
            return self.constructResponse("unknown", {
                "command" : command, 
                "message" : f'Command unknown: {command}'
            })

        try: 
            return commands[command](data)
        except ErrorMissingData as e: 
            return self.constructResponse("unsuccessful", {
                "command" : command, 
                "message" : f'Missing arguments for {command}.'
            })

    def message(self, data): 
        if not data: 
            raise ErrorMissingData

        try:
            message = " ".join(data[1:-1])
            clientSocket = data[-1]
            targetName = data[0] 

            client = self._manager.getClientBySocket(clientSocket)
            clientName = client["username"]
            target = self._manager.getClientByUsername(targetName)
        except ErrorClientNotFound: 
            return self.constructResponse("unsuccessful", { 
                "command" : "message", 
                "message" : f"User '{targetName}' not found."
            })


        # Target blocked or client blocked (2-way) 
        if targetName in client["blockedUsers"] or clientName in target["blockedUsers"]: 
            return self.constructResponse("unsuccessful", { 
                "command" : "message", 
                "message" : f'Unable to reach {targetName}'
            })

        # Target Offline
        if target["status"] == "inactive": 
            self._manager.addUnreadMessages({ 
                "source" : clientName, 
                "target" : targetName, 
                "message" : message
            }) 

            return self.constructResponse("success", { 
                "command" : "message", 
                "message" : f'Your message will be sent when {targetName} is online.'
            })
        
        target["socket"].send(self.constructResponse("message", { 
                "source" : clientName, 
                "message" : message
            }))

        return self.constructResponse("success", { 
            "command" : "message", 
            "message" : f"Your message to {targetName} has been sent."
        })

    def startPrivate(self, data): 
        if not data: 
            raise ErrorMissingData

        print(data)
        targetName = data[0]
        clientSocket = data[-1]

        try:
            target = self._manager.getClientByUsername(targetName)
            clientName = self._manager.getClientBySocket(clientSocket)

        except ErrorClientNotFound as e: 
            return self.constructResponse("unsuccessful", { 
                "command" : "startPrivate", 
                "message" : f"Cannot start private with '{targetName}' - User Unknown" 
            })

        # Check if target is offline 
        if not target["socket"]: 
            return self.constructResponse("unsuccessful", { 
                "command" : "startPrivate", 
                "message" : f"Cannot start private with '{targetName}' - User offline"
            }) 

        # Checked if blocked
        if clientName in target["blockedUsers"]: 
            return self.constructResponse("unsuccessful", { 
                "command" : "startPrivate", 
                "message" : f"Cannot start private with '{targetName}' - User unavailable"
            }) 


        return self.constructResponse("success", { 
            "command" : "startPrivate", 
            "message" : f"Ready to start a private connection with {targetName}",
            "target" : targetName,
            "targetAddress" : target["socket"].getpeername(), 
        }) 
                  
    def blockUser(self, data): 
        """ Client Command: Blocks User """ 

        if not data: 
            raise ErrorMissingData
        
        try: 
            clientSocket = data[-1]
            clientName = self._manager.getClientBySocket(clientSocket)["username"]
            targetName = data[0]

            self._manager.block(clientName, targetName) 
            return self.constructResponse("success", {
                "command" : "block", 
                "message" : f'You have blocked {targetName}'
            })

        except ErrorClientNotFound as e: 
            return self.constructResponse("unsuccessful", { 
                "command" : "block", 
                "message" : f'Error: {targetName} does not exit.'
            })
             
    def unblockUser(self, data): 
        """ Client Command: Unblocks User """

        if not data: 
            raise ErrorMissingData 

        try: 
            clientSocket = data[-1]
            clientName = self._manager.getClientBySocket(clientSocket)["username"]
            targetName = data[0]
            
        except ErrorClientNotFound as e: 
            return self.constructResponse("unsuccessful", {
            "command" : "unblock", 
            "message" : f"{targetName} does not exit."
        })

        self._manager.block(clientName, targetName, action="unblock") 
        return self.constructResponse("success", {
            "command" : "unblock", 
            "message" : f"You have unblocked {targetName}"
        })
    
    def whoElseSince(self, data): 
        """ Get all active clients since <time>(s) """

        time = int(data[0]) * 1000
        clientSocket = data[-1]
        clientName = self._manager.getClientBySocket(clientSocket)
        clients = self._manager.getActiveClients(time) 

        message = f"Users active since {time}(s):\n===========\n"
        for client in clients: 
            if client is not clientName: message += f' * {client}\n'
        message += "===========\n"
        return self.constructResponse("success", { 
            "command" : "whoelsesince",  
            "message" : message
        })

    def whoElse(self, data):
        """ Get all active clients """ 
        clientSocket = data[-1]
        clientName = self._manager.getClientBySocket(clientSocket)

        clients = self._manager.getActiveClients() 
        message = "Users currently active:\n=======\n"
        for client in clients: 
            if client is not clientName: message += f' * {client}\n'
        message += "=======\n"
        return self.constructResponse("success", data ={ 
            "command" : "whoelse", 
            "message" : message 
        })

    def produceBroadcasts(self, data): 
        """ Run broadcast for all clients """ 

        message = " ".join(data[:-1])
        clientSocket = data[-1]
        clientName = self._manager.getClientBySocket(clientSocket)["username"]

        self.broadcast(message, clientName) 

        if self._manager.hasBeenBlocked(clientName): message = "Your message has been broadcasted! [Note that some recipients may not have received your broadcast]" 
        else: message = "Your message has been broadcasted!"

        return self.constructResponse("success", { 
            "command" : "broadcast", 
            "message" : message 
        })

    def closeClientConnection(self, clientSocket): 
        """ Closes a client's connection """ 
        
        clientName = self._manager.getClientBySocket(clientSocket)["username"]
        self._manager.closeClientSession(clientSocket) 
        self.broadcast(f'{clientName} has left the chat.', clientName)
        return "success", { 
            "command" : "exit", 
            "message" : "You have successfully disconnected" 
        }

    def authenticate(self, data): 
        """ Authenticate a client """ 

        if not data:
            raise ErrorMissingData 

        username = data[0] 
        password = data[1]
        socket = data[-1]

        status = self._manager.authenticateClient(username, password) 
        if status == "success": 
            self._manager.updateClient(socket, username) 
            self.broadcast(f'{username} is online!', username)
            
            return self.constructResponse("success", { 
                "command" : "login", 
                "message" : f"Logged in as {username}",
                "unreadMessages" : self._manager.retrieveUnreadMessage(username)
            })
        elif status == "blocked": return self.constructResponse("unsuccessful", { 
            "message": f"You've been blocked, please try in {self._blockDuration}(s).", 
        })
        elif status == "alreadyActive" : return self.constructResponse("unsuccessful", { 
            "message" : "You're already logged in elsewhere."
        })
        elif status == "wrongCredentials": return self.constructResponse("unsuccessful", { 
            "message" : f'Invalid credentials'
        })
        
    def broadcast(self, message, clientName): 
        """ Send message to all applicable clients """ 

        socketsToAvoid = self._manager.getSocketToAvoid(clientName) 
        for socket in self._readList: 
            if socket == self._serverSocket: continue
            if socket in socketsToAvoid: continue 
            socket.send(self.constructResponse("broadcast", {
                "status" : "broadcast", 
                "message" : message
            }))
        

    def constructResponse(self, status, data={}): 
        response = {} 
        response["status"] = status 
        response["data"] = data
        response = json.dumps(response) 
        response = response.encode() 
        return response 

    def decodeReq(self, req):
        req = req.decode() 
        req = json.loads(req) 
        command = req.get("command") 
        data = req.get("data") 
        return command, data 
    

