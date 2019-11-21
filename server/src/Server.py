
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
                    continue
                
                # Receiving data from made connections 
                try: 
                    incomingPacket = s.recv(1024) 
                    command, data = self.decodeReq(incomingPacket)
                    data.append(s)

                # Client left without informing
                except (ConnectionResetError, SystemError):
                    self.clientDisconnect(s) 
                

                # Special Case for client logout
                if command == "logout": 
                    status, info = self.closeClientConnection(s) 
                    s.send(self.constructResponse((status, info))) 
                    if status == "success": self.clientDisconnect(s)
                    continue 
                
                try: 
                    s.send(self.processCommand(command, data))
                
                # Client's no longer connected to send information to
                except BrokenPipeError: 
                    self.clientDisconnect(s)
                
            # # Manage timeout by checking the last active times of clients not responding 
            # for connection in self._readList: 

            #     # Don't need to check the server's socket 
            #     if connection is self._serverSocket: continue
            #     if connection not in readable: 
            #         client = self._manager.getClientBySocket(connection) 
            #         print(client)
            #         if not client: continue

            #         print(f'clients last active time was {client["lastActive"]}')
            #         if time.monotonic() - client["lastActive"] > self._timeout: 
            #             print(f'<{client["username"]} has timed out')
            #             connection.send(self.constructResponse("timeout", { 
            #                 "message" : "Your session has timed out"
            #             }))
            #             self.closeClientConnection([socket])
            #             self._readList.remove(connection)   
                        

    def clientDisconnect(self, clientSocket): 
        try: 
            client = self._manager.getClientBySocket(clientSocket) 
            self.broadcast(f'{client["username"]} has left the server.', client["username"])
            self._manager.closeClientSession(clientSocket) 
            

        # Client hasn't logged in yet before leaving so don't do anything
        except ErrorClientNotFound:
            pass 
        print(f'Connection @{clientSocket.getpeername()} has disconnected')
        self._readList.remove(clientSocket)

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

        if len(data) < 2: 
            raise ErrorMissingData
        
        try:
            message = " ".join(data[1:-1])
            clientSocket = data[-1]
            targetName = data[0] 

            client = self._manager.getClientBySocket(clientSocket)
            clientName = client["username"]
            target = self._manager.getClientByUsername(targetName)

        # User doesn't exist
        except ErrorClientNotFound: 
            return self.constructResponse("unsuccessful", { 
                "command" : "message", 
                "message" : f"User '{targetName}' not found."
            })

        # Client cannot send a message to themselves 
        if targetName == clientName: return self.constructResponse("unsuccessful", { 
                "command" : "message", 
                "message" : f'Cannot message yourself'
            })
    
        # Cannot send empty string 
        if message == "": return self.constructResponse("unsuccessful", { 
            "command" : "message", 
            "message" : "Cannot send empty string"
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

        targetName = data[0]
        clientSocket = data[-1]

        try:
            target = self._manager.getClientByUsername(targetName)
            client = self._manager.getClientBySocket(clientSocket)

            if targetName == client["username"]: return self.constructResponse("unsuccessful", { 
                "command" : "startPrivate", 
                "message" : f'Cannot start private with yourself!'
            })

        except ErrorClientNotFound as e: 
            return self.constructResponse("unsuccessful", { 
                "command" : "startPrivate", 
                "message" : f"Cannot start private with '{targetName}' - User Unknown" 
            })

        # Check if target is offline 
        if target["status"] == "inactive": 
            return self.constructResponse("unsuccessful", { 
                "command" : "startPrivate", 
                "message" : f"Cannot start private with '{targetName}' - User offline"
            }) 

        # Checked if blocked
        if client["username"] in target["blockedUsers"]: 
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

        try: 
            clientSocket = data[-1]
            client = self._manager.getClientBySocket(clientSocket)
    
            targetName = data[0]
            target = self._manager.getClientByUsername(targetName)

            if targetName == client["username"]: return self.constructResponse("unsuccessful", { 
                "command" : "block", 
                "message" : "You cannot block yourself" 
            })

            self._manager.block(client["username"], targetName) 
            return self.constructResponse("success", {
                "command" : "block", 
                "message" : f'You have blocked {targetName}'
            })

        except ErrorClientNotFound as e: 
            return self.constructResponse("unsuccessful", { 
                "command" : "block", 
                "message" : f'Error: {targetName} does not exist.'
            })
             
    def unblockUser(self, data): 
        """ Client Command: Unblocks User """

        try: 
            clientSocket = data[-1]
            clientName = self._manager.getClientBySocket(clientSocket)["username"]
            targetName = data[0]
            if clientName == targetName: return self.constructResponse("unsuccessful",  { 
                "command" : "unblock",
                "message" : "You cannot unblock yourself"
            })
            
        except ErrorClientNotFound: return self.constructResponse("unsuccessful", {
            "command" : "unblock", 
            "message" : f"{targetName} does not exit."
        })

        except ErrorClientNotBlocked: return self.constructResponse("unsuccessful", {
            "command" : "unblock", 
            "message" : f"{targetName} was not blocked."
        })


        self._manager.block(clientName, targetName, action="unblock") 
        return self.constructResponse("success", {
            "command" : "unblock", 
            "message" : f"You have unblocked {targetName}"
        })
    
    def whoElseSince(self, data): 
        """ Get all active clients since <time>(s) """

        if len(data) < 2: 
            raise ErrorMissingData

        time = int(data[0])
        clientSocket = data[-1]
        clientName = self._manager.getClientBySocket(clientSocket)
        clientNames = self._manager.getActiveClients(time) 

        message = f"Users active since {time}(s):\n===========\n"
        for client in clientNames: 
            print(f'{client} is not {clientName} apparently..')
            if client is not clientName: message += f' * {client}\n'
        message += "===========\n"
        return self.constructResponse("success", { 
            "command" : "whoelsesince",  
            "message" : message
        })

    def whoElse(self, data):
        """ Get all active clients """ 

        clientSocket = data[-1]
        clientName = self._manager.getClientBySocket(clientSocket)["username"]

        clientNames = self._manager.getActiveClients() 
        message = "Users currently active:\n===========\n"
        for client in clientNames: 
            if client is not clientName: message += f' * {client}\n'
        message += "==========="
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

    def authenticate(self, data): 
        """ Authenticate a client """ 

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
        elif status == "blocked": 
            self._readList.remove(socket)
            return self.constructResponse("unsuccessful", { 
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
                "sender" : clientName, 
                "message" : message, 
            }))
        
    def constructResponse(self, status, data={}): 
        """ Constructs a response to follow the protocol """

        response = {} 
        response["status"] = status 
        response["data"] = data
        response = json.dumps(response) 
        response = response.encode() 
        return response 

    def decodeReq(self, req):
        """ Decodes the response according to the protocol """

        if not req: 
            raise SystemError

        req = req.decode() 
        req = json.loads(req) 
        command = req.get("command") 
        data = req.get("data") 
        return command, data 
    

