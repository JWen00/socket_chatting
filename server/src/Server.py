
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
                        self.broadcast(f'{client["username"]} has left the chat.')
                        self._readList = [x for x in self._readList if x is not s]

                    if information: 
                        print("Received info!")
                        command, data = self.decodeReq(information)    
                        print(f"ACK! Command: {command} w/ data {data}")

                        # Add connectionSocketDataOnto the packet for initial authentication
                        if command in ["login", "exit"]: data["socket"] = s

                        # Process the command
                        s.send(self.processCommand(command, data))

                        # Update the lastActive 
                        if client:
                            client["lastActive"] = time.time()
 
                    else: 
                        if client and (time.time() - client["lastActive"] > self._timeout): 
                            print(f'Timeout for client: @{client["username"]}')
                            self.closeClientConnection(data = { 
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

    def blockUser(self, data): 
        """ Client Command: Blocks User """ 

        if not data: 
            raise ErrorMissingData
        
        source = data["username"] 
        target = data["target"]

        try: 
            self._manager.block(source, target) 
            return self.constructResponse("success", {
            "command" : "block", 
            "message" : f'You have blocked {target}'
        })

        except ErrorClientNotFound as e: 
            return self.constructResponse("unsuccessful", { 
                "command" : "block", 
                "message" : f'{target} does not exit.'
            })
             
    def unblockUser(self, data): 
        """ Client Command: Unblocks User """

        if not data: 
            raise ErrorMissingData 

        source = data["username"] 
        target = data["target"]

        try: 
            self._manager.block(source, target, action="unblock") 
            return self.constructResponse("success", {
            "command" : "unblock", 
            "message" : f"You have unblocked {target}"
        })

        except ErrorClientNotFound as e: 
            return self.constructResponse("unsuccessful", {
            "command" : "unblock", 
            "message" : f"{target} does not exit."
        })
       
    def whoElseSince(self, data): 
        """ Get all active clients since <time>(s) """
        time = data["time"] * 1000 
        clients = self._manager.getClientsActiveSince(time) 
        message = f"Users active since {time}(s):\n=======\n"
        for client in clients: message.append(f' * {client}\n')
        message.append("=======\n")
        return self.constructResponse("success", { 
            "command" : "whoelsesince",  
            "message" : message
        })

    def whoElse(self):
        """ Get all active clients """ 

        clients = self._manager.getActiveClients() 
        message = "Users currently active:\n=======\n"
        for client in clients: message.append(f' * {client}\n')
        message.append("=======\n")
        return self.constructResponse("success", data ={ 
            "command" : "whoelse", 
            "message" : message 
        })

    def produceBroadcasts(self, data): 
        """ Run broadcast for all clients """ 

        self.broadcast(data["message"], data["source"]) 
        return self.constructResponse("success", { 
            "command" : "broadcast", 
            "message" : "Your message has been broadcasted!"  
        })

    def closeClientConnection(self, data): 
        """ Closes a client's connection """ 
        
        # Note: Closing the socket (.close()) will be handled as an exception
        socket = data["socket"]
        self.manage.removeClient(socket) 
        return self.constructResponse("success", data = { 
            "command" : "exit", 
            "message" : "You have successfully disconnected" 
        })

    def authenticate(self, loginData): 
        """ Authenticate a client """ 

        if not loginData:
            raise ErrorMissingData 

        username = loginData.get("username") 
        password = loginData.get("password") 
        socket = loginData.get("socket")
        status = self._manager.authenticateClient(username, password) 
        if status == "success": 
            self._manager.updateClient(socket, username) 
            self.broadcast(f'{username} is online!', socket)
            return self.constructResponse("success", { 
                "command" : "login", 
                "message" : f"Logged in as {username}",
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
        for socket in self._manager.getSocketsNotBlockedBy(clientSocket): 
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
    

