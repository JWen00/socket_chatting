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
        
        self._logins = {}
        
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
        read_list = [self._serverSocket] 
        print("Awaiting connections...") 
        while True: 
            readable, writable, errorable = select.select(read_list, [], [])
            for s in readable: 
                if s is self._serverSocket: 
                    connectionSocket, addr = self._serverSocket.accept() 
                    read_list.append(connectionSocket)
                    print("New connection @" + str(addr))

                    t = threading.Thread(target=self.listenToClient, args=(connectionSocket, addr)) 
                    # t.daemon = True # Closes when thread finishes 
                    t.start() 

    def listenToClient(self, connectionSocket, address): 
        print(f"Listening to client: {address}")
        while True:
            ready = select.select([connectionSocket], [], [], self._timeout)
            print("S")
            if ready[0]: 
                information = connectionSocket.recv(1024)
                print("ACK! Received: " + str(information))
                command, data = decodeReq(information)    
                connectionSocket.send(self.processCommand(command, data))
            else: 
                print(f'Timeout for connection @{address}')
                # connectionSocket.close() 
                # TODO: Remove from self._logins when client logs off 
                break

    def processCommand(self, command, data): 
        commands = { 
            "login" : self.authenticate 
        }
        return commands[command](data)

    def authenticate(self, loginData): 
        username = loginData.get("username") 
        password = loginData.get("password") 


        # Check if user is blocked or already active
        if username in self._logins: 
            userInfo = self._logins.get(username) 
            def isBlocked(userInfo):
                if userInfo.get("status") != "blocked":  return False
                if time.time() - userInfo.get("blockTime") > self._blockDuration:
                    userInfo["status"] == "unsuccessful"
                    return False
                return True
            
            def isActive(userInfor): 
                if userInfo.get("status") != "active": return False 
                return True

            if isBlocked(userInfo):
                return self.constructResponse("Unsuccessful",  { 
                        "explanation": "You've been blocked. Please try again later"
                    })
            if isActive(userInfo): return self.constructResponse("Unsuccessful", { 
                    "explanation" : "You're already logged in elsewhere."
                })

        # Check for correct login 
        for credential in self._login_credentials: 
            if credential["username"] == username and credential["password"] == password: 
                if username in self._logins: 
                    self._logins.get(username)["status"] = "active"
                else: 
                    self._logins[username] = { 
                        "status" : "active"
                    }
                return constructResponse("success")

        if username in self._logins: 
            self._logins[username]["attempts"] += 1 
            if self._logins[username]["attempts"] == 3:
                self._logins[username] = { 
                    "status" : "blocked", 
                    "attempts" : 0, 
                    "blockTime" : time.time()
                }

        else: 
            self._logins[username] = { 
                "attempts" : 1, 
                "status" : "unsuccessful" 
            } 
            
        return constructResponse("unsuccessful", { 
            "explanation" : "Invalid Credentials"
        })

    def constructResponse(self, status, data=None): 
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

