import os 
from socket import *
from clientPacketHander import constructReq, decodeResponse
import time
from NewClient import NewClient

# Prompt the user to log in
def login(): 
    username = input("Username: ") 
    password = input("Password: ") 
    data = { 
        "username" : username, 
        "password" : password 
    }

    req = NewClient.constructReq("login", data)
    clientSocket.send(req) 
    reply = clientSocket.recv(1024)
    status, data = NewClient.decodeResponse(reply)
    if status == "success": 
        c = NewClient(username)
        return c

    print("Unsuccessful: " + data.get("explanation")) 
    
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

client = None
while client == None: 
    client = login() 
print("Login Success!")

client.bindSocket(clientSocket) 
client.listen() 
