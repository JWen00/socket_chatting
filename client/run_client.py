import os 
from socket import *
from Client import Client


# if len(os.argv) < 3: 
#     print("Usage: python client.py <portNumber>") 
#     os.exit() 

# serverIP = os.argv[1]
# serverPort = os.argv[2]


def createClient(): 
    serverPort = 5000
    serverName = "localhost" 
    clientSocket = socket(AF_INET, SOCK_STREAM) 
    clientSocket.connect((serverName, serverPort)) 
    print("Made a connection!") 

    client = None
    while client == None: 
        client = Client.login(clientSocket) 
    print("Login Success!")
    client.bindSocket(clientSocket) 
    client.listen() 

createClient()