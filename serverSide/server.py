# import os 
from socket import *
import select 
from loader import loadCredentialsFile
import threading
from serverPacketHandler import *
import os 
import sys
import json 
import time 


class Server(): 
    def __init__(self, serverName, serverPort, blockDuration, timeout): 
        self._login_credentials = None 

        self._serverName = serverName
        self._serverPort = serverPort
        self._serverSocket = None 
        self._blockDuration = blockDuration
        self._timeout = timeout
        self._readList = []
        self._loginAttempts = {}
        self._activeUsers = {}
        
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
        
        # Get credentials file 
        try: 
            self._login_credentials = loadCredentialsFile("credentials.txt")
        except FileNotFoundError as e: 
            print("Credential file not found")
            os.exit()

        # Get list of who has who blocked
        
        # Manage Sockets 
        try:
            self._serverSocket = socket(AF_INET, SOCK_STREAM) 
            self._serverSocket.bind((serverName, serverPort))
            self._serverSocket.listen(1) 
            print("Server listening on " + serverName + ":" + str(serverPort) + "...")
        except OSError:
            print(f"Port busy! Try again in a bit :)")
            sys.exit() 
        
    def listenForNewConnections(self): 
        print("Awaiting connections...") 
        self._readList = [self._serverSocket]
        while True: 
            readable, writable, errorable = select.select(self._readList, [], [])
            for s in readable: 
                if s is self._serverSocket: 
                    connectionSocket, addr = self._serverSocket.accept() 
                    self._readList.append(connectionSocket)
                    print("New connection @" + str(addr))

                    t = threading.Thread(target=self.listenToClient, args=(connectionSocket, addr)) 
                    # t.daemon = True # Closes when thread finishes 
                    t.start() 

    def listenToClient(self, connectionSocket, address): 
        print(f"Listening to client: {address}")
        while True:
            ready = select.select([connectionSocket], [], [], self._timeout)
            if ready[0]: 
                information = connectionSocket.recv(1024)
                command, data = decodeReq(information)    
                print(f"ACK! Received: {command} with data {data}")

                # Add connectionSocketDataOnto the packet for initial authentication
                if command in ["login", "exit"]: data["socket"] = connectionSocket

                # Process the command
                connectionSocket.send(self.processCommand(command, data))
            else: 
                print(f'Timeout for connection @{address}')
                self.closeClientConnection(data = { 
                    "socket" : connectionSocket
                }) 
                
                break
    
    def processCommand(self, command, data): 
        commands = { 
            "login" : self.authenticate, 
            "exit" : self.closeClientConnection
        }
        return commands[command](data)

    def closeClientConnection(self, data): 
        connectionSocket = data["socket"] 
        connectionSocket.close() 
        self._readList.remove(connectionSocket) 
        del self._activeUsers[connectionSocket]
        return self.constructResponse("exit success")




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
        for user in self._activeUsers: 
            if self._activeUsers[user] == username: return self.constructResponse("Unsuccessful", { 
                    "explanation" : "You're already logged in elsewhere."
                })

        # Check for correct login 
        for credential in self._login_credentials: 
            if credential["username"] == username and credential["password"] == password: 
                if username in self._loginAttempts: del self._loginAttempts[username] 
                self._activeUsers[socket] = username
                print("Login success for user: " + username)
                return constructResponse("success")

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
            
        return constructResponse("unsuccessful", { 
            "explanation" : "Invalid credentials, you have " + (3 - self._loginAttempts[username]["attempts"]) +  " left."
        })

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



# # if os.argv < 3:
# #     print("Usage: python server.py <server_port> <block_duration> <timeout>") 
# #     os.exit(1) 

# # serverPort = os.argv[1]
# # blockDuration = os.argv[2] 
# # timeout = os.argv[3] 
serverPort = 5000
serverName = "localhost"
blockDuration = 5
timeout = 15
s = Server(serverName, serverPort, blockDuration, timeout)
s.initialiseServer() 
s.listenForNewConnections()
# Do we need to have functionality to close the server? 

