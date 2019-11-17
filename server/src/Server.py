
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
        self._timeout = timeout * 1000 
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
                    self._manager.addClient(connection) 
                    self._readList.append(connection) 
                    print("New connection @" + str(addr))

                # Receiving data from made connections 
                else: 
                    client = self._manager.getClientBySocket(s) 
                    try: 
                        information = s.recv(1024)
                    except ConnectionResetError:
                        self.broadcast(f'{client["username"]} has left the chat.', s)
                        self._readList.remove(s) 
                        # self._readList = [x for x in self._readList if x is not s]

                    if information: 
                        command, data = self.decodeReq(information)    

                        # Include socket information with every command
                        data.append(s) 
                    
                        # Process the command
                        s.send(self.processCommand(command, data))

                        # Update the lastActive 
                        if client:
                            client["lastActive"] = time.time()
 
                    else: 
                        if client and (time.time() - client["lastActive"] > self._timeout): 
                            print(f'Timeout for client: @{client["username"]}')
                            self.closeClientConnection({ 
                                "socket" : socket
                            }) 
                            self.broadcast(f'{client["username"]} has left the chat.')

    def processCommand(self, command, data): 
        """ Redirects client to appropriate command """ 

        commands = { 
            "login" : self.authenticate, 
            "logout" : self.closeClientConnection, 
            "broadcast" : self.produceBroadcasts, 
            "whoelse" : self.whoElse, 
            "whoelsesince" : self.whoElseSince, 
            "block" : self.blockUser, 
            "unblock" : self.unblockUser, 
            "startprivate" : self.startPrivate,
            "message" : self.message,  
        }

        if not command in commands: 
            return self.constructResponse("unsuccessful", {
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

        targetName = data[0] 
        message = " ".join(data[1:-1])
        clientSocket = data[-1]
        clientName = self._manager.getClientBySocket(clientSocket)["username"]

        # Check for blocking
        socketsWhoBlockedClient = self._manager.getSocketsWhoBlockedClient(clientSocket)
        if targetName in socketsWhoBlockedClient: 
            return self.constructResponse("unsuccessful", { 
                "command" : "message", 
                "message": f"Unable to reach {targetName}"
            })

        try: 
            target = self._manager.getClientByUsername(targetName)
            targetSocket = target["socket"] 
            if not targetSocket:  
                self._manager.addUnreadMessages({ 
                    "source" : clientName, 
                    "target" : targetName, 
                    "message" : message
                }) 

                return self.constructResponse("success", { 
                    "command" : "message", 
                    "message" : f'Your message will be sent when {targetName} is online.'
                })

            else: 
                targetSocket.send(self.constructResponse("message", { 
                    "source" : clientName, 
                    "message" : message
                }))

                return self.constructResponse("success", { 
                    "command" : "message", 
                    "message" : "Your message has been sent."
                })

        except ErrorClientNotFound as e: 
            return self.constructResponse("unsuccessful", { 
                "command" : "message", 
                "message" : f"User '{targetName}' not found"
            })
  
    def startPrivate(self, data): 
        if not data: 
            raise ErrorMissingData

        targetName = data[0]
        clientSocket = data[-1]
        target = self._manager.getClientByUsername(targetName)
        clientName = self._manager.getClientBySocket(clientSocket)

        try:
            # Checked if blocked
            if clientName in target["blockedUsers"]: 
                return self.constructResponse("unsuccessful", { 
                    "command" : "startPrivate", 
                    "message" : f"Cannot start private with '{targetName}' - User unavailable"
                }) 


            return self.constructResponse("successful", { 
                "command" : "startPrivate", 
                "message" : f"Ready to start a private connection with {targetName}",
                "targetAddress" : target["socket"].getpeername() , 
            }) 
            
        except ErrorClientNotFound as e: 
            return self.constructResponse("unsuccessful", { 
                "command" : "startPrivate", 
                "message" : f"Cannot start private with '{targetName}' - User Unknown" 
            })
        
    def blockUser(self, data): 
        """ Client Command: Blocks User """ 

        if not data: 
            raise ErrorMissingData
        
        try: 
            clientSocket = data[-1]
            clientName = self._manager.getClientBySocket()["username"]
            targetName = data[0]

            self._manager.block(clientName, targetName) 
            return self.constructResponse("success", {
            "command" : "block", 
            "message" : f'You have blocked {targetName}'
        })

        except ErrorClientNotFound as e: 
            return self.constructResponse("unsuccessful", { 
                "command" : "block", 
                "message" : f'{targetName} does not exit.'
            })
             
    def unblockUser(self, data): 
        """ Client Command: Unblocks User """

        if not data: 
            raise ErrorMissingData 

        try: 
            clientSocket = data[-1]
            clientName = self._manager.getClientBySocket()["username"]
            targetName = data[0]
            
            self._manager.block(clientName, targetName, action="unblock") 
            return self.constructResponse("success", {
            "command" : "unblock", 
            "message" : f"You have unblocked {targetName}"
        })

        except ErrorClientNotFound as e: 
            return self.constructResponse("unsuccessful", {
            "command" : "unblock", 
            "message" : f"{targetName} does not exit."
        })
       
    def whoElseSince(self, data): 
        """ Get all active clients since <time>(s) """

        time = int(data[0]) * 1000
        clientSocket = data[-1]
        clientName = self._manager.getClientBySocket(clientSocket)
        clients = self._manager.getClientsActiveSince(time) 

        message = f"Users active since {time}(s):\n=======\n"
        for client in clients: 
            if client is not clientName: message += f' * {client}\n'
        message += "=======\n"
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

        self.broadcast(message, clientSocket) 
        if len(self._manager.getSocketsWhoBlockedClient(clientSocket)) > 0: 
            message = "Your message has been broadcasted! [Note that some recipients may not have received your broadcast]" 
        else: message = "Your message has been broadcasted!"

        return self.constructResponse("success", { 
            "command" : "broadcast", 
            "message" : message 
        })

    def closeClientConnection(self, data): 
        """ Closes a client's connection """ 
        
        # Note: Closing the socket (.close()) will be handled as an exception
        clientSocket = data[-1]
        self._manager.closeClientSession(clientSocket) 
        return self.constructResponse("success", data = { 
            "command" : "exit", 
            "message" : "You have successfully disconnected" 
        })

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
            self.broadcast(f'{username} is online!', socket)
            
            return self.constructResponse("success", { 
                "command" : "login", 
                "message" : f"Logged in as {username}",
                "unreadMessages" : self._manager.retrieveUnreadMessage(username)
            })
        elif status == "blocked": return self.constructResponse("unsuccessful", { 
            "message": f"You've been blocked for {self._blockDuration}(s). Please try again later", 
        })
        elif status == "alreadyActive" : return self.constructResponse("unsuccessful", { 
            "message" : "You're already logged in elsewhere."
        })
        elif status == "wrongCredentials": return self.constructResponse("unsuccessful", { 
            "message" : f'Invalid credentials'
        })
        
    def broadcast(self, message, clientSocket): 
        """ Send message to all applicable clients """ 

        sendableSockets = self._manager.getSocketsNotBlockedBy(clientSocket)
        for socket in sendableSockets: 
            if socket is not clientSocket: 
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
    

