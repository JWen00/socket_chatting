import os 
from socket import *
import select 
from clientPacketHander import *
import time 

# Prompt the user to log in
def initialise(block_duration): 
    nTries = 0
    while nTries < 3: 
        username = input("Username: ") 
        password = input("Password: ") 
        data = { 
            "username" : username, 
            "password" : password 
        }

        req = constructReq("login", data) 
        clientSocket.send(req) 
        reply = clientSocket.recv(1024)
        status, data = decodeResponse(reply)
        if status == "success": 
            return True

        nTries += 1
        print("Unsuccessful: " + data.get("explanation")) 
    
    print("You have been blocked for " + str(block_duration) + "(s)\n") 
    time.sleep(int(block_duration))
    return False
    
    
# if len(os.argv) < 3: 
#     print("Usage: python client.py <portNumber>") 
#     os.exit() 

# serverIP = os.argv[1]
# serverPort = os.argv[2]
serverPort = 5000
serverName = "localhost" 
clientSocket = socket(AF_INET, SOCK_STREAM) 
clientSocket.connect((serverName, serverPort)) 
print("Made a connection!") 

loginStatus = False 
while not loginStatus: 
    initialise(5) 
print("Login Success!")
clientSocket.close()

# class Client(): 
#     def __init__(self, serverIP, serverPort):
#         self.serverIP = serverIP 
#         self.serverPort = serverPort 
#         self.socket = socket(AF_INET, SOCK_STREAM) 
        
#         self.name = ""
#         # self.blockedUsers = []
#         # self.commandsAvailable = { 
#         #     login: clientCommands.login,
#         #     logout: clientCommands.logout, 
#         #     message : clientCommands.message, 
#         #     broadcast : clientCommands.broadcast, 
#         #     whoelse : clientCommnds.whoelse, 
#         #     whoelsesince : clientCommands.whoelsesince, 
#         #     block : clientCommands.message, 
#         #     unblock : clientCommands.unblock, 

#     def listen(self): 
#         self.socket.connect((self.serverIP, self.serverPort)) 
#         print("Listening on " + self.serverIP + ":" + str(self.serverPort) + "...")
#         msg = "hello"
#         self.socket.send(msg.encode("utf-8"))
#         # Does not respond until received an ack! 
#         message = self.socket.recv(1024) 
#         print(message) 

#         # Since this is the initial connection, prompt: w
#         username =  raw_input("Username: ")
#         password = raw_input("Password: ")
#         data = { 
#             "username" : username,  
#             "password" : password  
#         }

#         self.constructResponse("login", data)
#         socket.send(response)
#         self.name = username 

#         while 1:       
#             ready = select([self.socket], [], [], 1)
#             if ready[0]: 
#                 message, serverAddress = self.socket.recv(1024) 
#                 print(message) 
#             # if input[0] not in self.commandsAvailable: 
#             #     print("Unknown command: " + input[0])
       
#     def constructResponse(self, command, data): 
#         response = { 
#             "user" : self.name, 
#             "command": command, 
#             "data" : data
#         }
#         return JSON.stringify(response)

        

#     # def waitForResponse(self): 
#     #     ...socket magic
    


    