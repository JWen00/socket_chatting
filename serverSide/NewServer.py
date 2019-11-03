import sys
import os 
import time 
import threading
from socket import *
import select 
import json 
from Session import Session 
from ClientInfo import ClientInfo


class NewServer(): 
    def __init__(self, serverName, serverPort, blockDuration, timeout): 
        self._login_credentials = None 
        self._clientBlockingData = None

        self._serverName = serverName
        self._serverPort = serverPort
        self._serverSocket = None 
        self._blockDuration = blockDuration
        self._timeout = timeout
        self._loginAttempts = {}
        self._clients = {} 
        self._serverStartTime = time.time() 
        
    def initialiseServer(self): 
        def loadCredentialsFile(filePath): 
            data = None
            with open(filePath, "r") as f: 
                data = f.read().splitlines()

            if not data: 
                raise FileNotFoundError 

            credentials_list = []
            for line in data:
                username, password = line.split(" ", 1)
                new_login = {}
                new_login["username"] = username
                new_login["password"] = password
                credentials_list.append(new_login) 
                
            return credentials_list
        
        def loadClientBlockingData(filePath): 
            data = None 
            with open(filePath, "r") as f: 
                data = f.read() 
                if not data: 
                    raise FileNotFoundError 
            return json.loads(data)

        # Get credentials file 
        try: 
            self._login_credentials = loadCredentialsFile("credentials.txt")
        except FileNotFoundError as e: 
            print("Credential file not found")
            os.exit()

        # Get user blocking
        try: 
            self._clientBlockingData = loadClientBlockingData("blockingData.txt") 
        except FileNotFoundError as e: 
            print("No blocking data found") 
        
        # Manage Sockets 
        try:
            self._serverSocket = socket(AF_INET, SOCK_STREAM) 
            self._serverSocket.bind((self._serverName, self._serverPort))
            self._serverSocket.listen(1) 
            print(f"Server listening on {self._serverName} : {self._serverPort}...")
        except OSError:
            print(f"Port busy! Try again in a bit")
            sys.exit() 
        
    def listen(self): 
        print("Server is listening...") 
        readList = [self._serverSocket]
        while True: 
            readable, writable, errorable = select.select(readList, [], [])
            for s in readable: 

                # Receiving new connections 
                if s is self._serverSocket: 
                    connection, addr = self._serverSocket.accept() 
                    self._clients.append(ClientInfo(connection, connection.getsockname())) 
                    readList.append(socket) 
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
        pass 

    def unblockUser(self, data): 
        pass 

    def whoElseSince(self, data): 
        time = data["time"] 
        usersActiveSince = []
        for client in self._clients: 
            if client.isActiveSince(time): usersActiveSince.append(client.username) 
        return self.constructResponse("success", data={ 
            "command" : "whoelsesince",  
            "users" : usersActiveSince, 
            "message" : f"Users who have been active since {time}:"
        })

    
    # Make this better with just message..
    def whoElse(self): 
        activeUsers = []
        for client in self._clients: activeUsers.append(client.username) 
        return self.constructResponse("success", data ={ 
            "command" : "whoelse", 
            "users" : activeUsers, 
            "message" : "Users currently active: " 
        })

    # TODO: Possible try catch here for the keyUnfoundErrors
    def produceBroadcasts(self, data=None): 
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
        for client in self._clients: 
            if client.socket == socket: 
                self._clients.remove(client)  
        return self.constructResponse("success", data = { 
            "command" : "exit", 
            "message" : "You have successfully disconnected" 
        })

    def authenticate(self, loginData): 
        username = loginData.get("username") 
        password = loginData.get("password") 
        socket = loginData.get("socket")

        # Check if user is blocked
        if username in self._loginAttempts: 
            userInfo = self._loginAttempts.get(username) 
            def isBlocked(userInfo):
                if userInfo.get("status") != "blocked":  return False
                if time.time() - userInfo.get("blockTime") > self._blockDuration:
                    userInfo["status"] == "unsuccessful"
                    return False
                return True
            
            if isBlocked(userInfo):
                return self.constructResponse("Unsuccessful",  { 
                        "explanation": f"You've been blocked for {self._blockDuration}(s). Please try again later"
                    })


        # Check if user is active 
        if username in self._clients: return self.constructResponse("Unsuccessful", { 
            "explanation" : "You're already logged in elsewhere."
        })

        # Check for correct login 
        for credential in self._login_credentials: 
            if credential["username"] == username and credential["password"] == password: 

                # Delete previous attempts, if any
                if username in self._loginAttempts: del self._loginAttempts[username]

                # Add additional information for the client 
                for client in self._clients: 
                    if client.socket == socket: 
                        client.username = username 
                        client.lastActive = time.time() 
                        client.currSession = Session.createSession() 

                print("Login success for user: " + username)
                return self.constructResponse("success", data = { 
                    "command" : "login", 
                    "message" : f"Logged in as {username}",
                })

        # Incorrect Login
        if username in self._loginAttempts: 
            self._loginAttempts[username]["attempts"] += 1 
            if self._loginAttempts[username]["attempts"] == 3:
                self._loginAttempts[username] = { 
                    "status" : "blocked", 
                    "attempts" : 0, 
                    "blockTime" : time.time()
                }

        else: 
            self._loginAttempts[username] = { 
                "attempts" : 1, 
                "status" : "unsuccessful" 
            } 
            
        return self.constructResponse("unsuccessful", { 
            "message" : f'Invalid credentials, you have {(3 - self._loginAttempts[username]["attempts"])}(s)" left.'
        })

    
        def broadcast(self, clientSocket, message): 
            clientSocket.send(self.constructResponse("broadcast", data={
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

