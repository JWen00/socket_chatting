# import os 
from socket import *
import select 
from loader import loadCredentialsFile
from serverPacketHandler import *
import os 

def authenticate(loginData): 
    username = data.get("username") 
    password = data.get("password") 

    # Check if user is already logged in TODO:

    for credential in login_credentials: 
        if credential["username"] == username and credential["password"] == password: 
            return constructResponse("success")
        
    return constructResponse("unsuccessful", { 
        "explanation" : "Invalid Credentials"
    })


serverPort = 5000
serverName = "localhost"
blockDuration = 2
timeout = 2
login_credentials = None
try: 
    login_credentials = loadCredentialsFile("credentials.txt")
except FileNotFoundError as e: 
    print("Credential file not found")
    os.exit()

# Fire up sockets 
serverSocket = socket(AF_INET, SOCK_STREAM) 
serverSocket.bind((serverName, serverPort))
serverSocket.listen(1) 
print("Server listening on " + serverName + ":" + str(serverPort) + "...")

read_list = [serverSocket] 
while True: 
    readable, writable, errored = select.select(read_list, [], [])
    for s in readable: 

        # Only receive a new connection if it's from our main one. 
        if s is serverSocket: 
            connectionSocket, addr = serverSocket.accept() 
            read_list.append(connectionSocket)
            print("New connection @" + str(addr))
            connectionSocket.send(constructResponse("welcomePacket", { 
                "blockDuration" : blockDuration, 
                "timeout" : timeout, 
            })) 

        else: 
            information = connectionSocket.recv(1024) 
            if not information: # Socket is closed 
                s.close() 
                read_list.remove(s) 
                break

            print("ACK! Received: " + str(information))
            command, data = decodeReq(information) 

            # TODO: Map a list of commands to function calls 
            if command == "login": 
                connectionSocket.send(authenticate(data))

            else: 
                print("UNKNOWN COMMAND.. YEeeT")
                



# # if os.argv < 3:
# #     print("Usage: python server.py <server_port> <block_duration> <timeout>") 
# #     os.exit(1) 

# # serverPort = os.argv[1]
# # blockDuration = os.argv[2] 
# # timeout = os.argv[3] 

