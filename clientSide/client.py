import os 
from socket import *
from clientPacketHander import constructReq, decodeResponse
import time
from NewClient import NewClient

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
            c = NewClient(username)
            return c

        nTries += 1
        print("Unsuccessful: " + data.get("explanation")) 
    
    print("You have been blocked for " + str(block_duration) + "(s)\n") 
    time.sleep(int(block_duration))
    return None
    

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

welcomePacket = clientSocket.recv(1024)
status, data = decodeResponse(welcomePacket)

if status  != "welcomePacket": 
    print("Error! No setup configurations given")
    clientSocket.close() 

blockDuration = data["blockDuration"] 
timeout = data["timeout"] 

client = None
while client == None: 
    client = initialise(5) 
print("Login Success!")

client.bindSocket(clientSocket) 
client.setTimeout(timeout)
client.listen() 
