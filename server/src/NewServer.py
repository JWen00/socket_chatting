import time 
from socket import *
import select 
import json 
from ClientManager import ClientManager


class NewServer(): 
    def __init__(self, serverName, serverPort, blockDuration, timeout): 
        try:
            self._serverSocket = socket(AF_INET, SOCK_STREAM) 
            self._serverSocket.bind((serverName, serverPort))
            self._serverSocket.listen(1) 
            print(f"Server listening on {serverName} : {serverPort}...")
        except OSError:
            print(f"Port busy! Try again in a bit")
            sys.exit() 

        self._blockDuration = blockDuration
        self._timeout = timeout
        self._readList = []
        self._manager = ClientManager() 

    def listen(self): 
        print("Server is listening...") 
        self._readList = [self._serverSocket]
        while True: 
            readable, writable, errorable = select.select(self._readList, [], [])
            for s in readable: 

                # Receiving new connections 
                if s is self._serverSocket: 
                    connection, addr = self._serverSocket.accept() 
                    self.manager.addClient(connection) 
                    self._readList.append(socket) 
                    print("New connection @" + str(addr))

                # Receiving data from made connections 
                else: 
                    information = s.recv(1024)
                    clientOJB = None
                    for client in self._clients: 
                        if client.sockName == s.getsockname: clientOJB = client

                    if information: 
                        command, data = self.decodeReq(information)    
                        print(f"ACK! Command: {command} w/ data {data}")

                        # Add connectionSocketDataOnto the packet for initial authentication
                        if command in ["login", "exit"]: data["socket"] = socket

                        # Process the command
                        s.send(self.processCommand(command, data))

                        # Update the lastActive 
                        clientOJB.lastActive = time.time() 
                    elif not information and time.time() - clientOJB.lastActive > self._timeout: 
                        print(f'Timeout for client: @{client.username}')
                        self.closeClientConnection(data = { 
                            "socket" : socket
                        }) 
                        self.broadcast(f'{clientOJB.username} has left the chat.')

    def processCommand(self, command, data): 
        commands = { 
            "login" : self.authenticate, 
            "logout" : self.closeClientConnection, 
            "broadcast" : self.produceBroadcasts, 
            "whoelse" : self.whoElse, 
            "whoelsesince" : self.whoelsesince, 
            "block" : self.blockUser, 
            "unblock" : self.unblockUser, 
        }
        return commands[command](data)

    def blockUser(self, data): 
        hater = data["username"] 
        hated = data["target"]
        try: 
            self.manager.block(hater, hated) 
        # except: 
        return self.constructResponse("success", data={
            "command" : "block", 
            "message" : f'You have blocked {hated}'
        })
        
    def unblockUser(self, data): 
        hatered = data["username"] 
        unhated = data["target"] 
        try: 
            self.manager.unblock(hatered, unhated) 
        # except: 
        return self.constructResponse("success", data={
            "command" : "unblock", 
            "message" : f"You have unblocked {unhated}"
        })

    def whoElseSince(self, data): 
        time = data["time"] 
        try: 
            clients = self.manager.getClientsActiveSince(time) 
        # except: 

        return self.constructResponse("success", data={ 
            "command" : "whoelsesince",  
            "users" : clients, 
            "message" : f"Users who have been active since {time}:"
        })

    def whoElse(self): 
        activeUsers = self.manager.getActiveClients() 
        return self.constructResponse("success", data ={ 
            "command" : "whoelse", 
            "users" : activeUsers, 
            "message" : "Users currently active: " 
        })

    def produceBroadcasts(self, data=None): 
        """ Run broadcast for all clients """ 
        try:  
            self.broadcast(data["message"]) 
        # except: 
        return self.constructResponse("success", data= { 
            "command" : "broadcast", 
            "message" : "Your message has been broadcasted!"  
        })

    def closeClientConnection(self, data): 
        """ Closes a client's connection """ 
        # TODO: Haven't physically socket.close()?? 
        
        socket = data["socket"]
        self._readList.remove(socket) 
        self.manage.removeClient(socket) 
        return self.constructResponse("success", data = { 
            "command" : "exit", 
            "message" : "You have successfully disconnected" 
        })

    def authenticate(self, loginData): 
        """ Authenticate a client """ 

        username = loginData.get("username") 
        password = loginData.get("password") 
        socket = loginData.get("socket")
        status = self.manage.authenticateClient(username, password) 
        if status == "success": 
            self.manager.updateClient(socket, username) 
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
        elif status == "wrontCredentials": return self.constructResponse("unsuccessful", { 
            "message" : f'Invalid credentials, you have {(3 - self._loginAttempts[username]["attempts"])}(s)" left.'
        })
        

    def broadcast(self, clientSocket, message): 
        broadcaster = self.manager.getClientBySocket(clientSocket) 
        for client in self._manager.getClientsNotBlockedBy(broadcaster): 
            client["socket"].send(self.constructResponse("broadcast", {
            "status" : "receivedBroadcast", 
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
        try:
            req = req.decode() 
            req = json.loads(req) 
            command = req.get("command") 
            data = req.get("data") 
            return command, data 
        except JSONDecodeError as e: 
            print("There is something seriously wrong.. response is not JSON format D:") 
            sys.exit()

