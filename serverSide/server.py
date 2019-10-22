# import os 
from socket import *
import select 
from loader import loadCredentialsFile
from serverPacketHandler import *
import os 

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

# Fireup sockets 
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

        else: 
            information = connectionSocket.recv(1024) 
            if not information: 
                # Socket has closed.. 
                s.close() 
                read_list.remove(s) 
                break

            print("ACK! Received: " + str(information))
            command, data = decodeReq(information) 

            if command == "login": 
                username = data.get("username") 
                password = data.get("password") 

                # Check if user is already logged in TODO:

                for credential in login_credentials: 
                    if credential["username"] == username and credential["password"] == password: 
                        response = constructResponse("success")
                data = {
                    "explanation" : "Invalid credentials" 
                }
                response = constructResponse("unsuccessful", data)

            else: 
                response = constructResponse("Unsuccessful", data = {
                    "explanation" : "Unknown Command" 
                })
            
            connectionSocket.send(response)



# class Server(): 
#     def __init__(self, serverPort, blockDuration, timeout): 
#         self.serverPort = serverPort 
#         self.blockDuration = blockDuration
#         self.timeout = timeout 
#         self.serverName = "localhost"
#         self.socket = socket(AF_INET, SOCK_STREAM)
#         self.socket.bind((self.serverName, self.serverPort)) 
#         self.socket.listen(1)
#         print("Listening on " + self.serverName + ":" + str(self.serverPort) + "...")
        
#         self.onlineUsers = [] 

#     def listen(self): 
#         # read_list = [self.socket]
#         while 1: 
            
#             clientConnection, address = self.socket.accept()
#             print("New Connection from" + address) 
#             self.socket.send("Hi! Welcome to the primitiveMess :)\n Please enter in your username and password!") 
#             # readable, w, e = select.select(read_list, [], []) 
#             # for item in readable: 
#             #     print("checking item in readable")
#             #     # Incoming connection
#             #     if item in socket: 
#             #         newConn, addr = socket.accept() 
#             #         read_list.append(newConn) 
#             #         print("New Connection from" + addr) 
#             #         self.socket.send("Hi! Welcome to the primitiveMess :)\n Please enter in your username and password!") 


#             #     # Incoming packet 
#             #     else: 
#             #         packet = socket.recv(1024) 
#             #         print("Received: " + packet)
#             #         # packet = json.loads(data)
#             #         # command = packet.get("command") 
                    
#             #         # Depending on what the command 

#     # def clientLogin(self): 
        
#     #     prompt for username and password 
#     #     if new user: 
#     #         store into credentials.txt 

#     #     else:
#     #         if user is online: 
#     #             raise exception("User is already online!") 
#     #         for (nTries = 0; nTries < 3; nTries++):  
#     #             check input and compare to credentials.txt 
#     #             if input == correct: 
#     #                 newOnlineUser = OnlineUser(...)
#     #                 self.onlineUsers.append(newOnlineUser) 
#     #                 return  newOnlineUser
                
#     #         raise exception("Too many attempts, you have been blocked for " + str(blockDuration) " seconds.") 
#             # (even from another IP address). Hm. TODO: 

#     # def clientLogoff(self): 
#     #     self.broadcast(user) 
#     #     for user in self.onlineUsers: 
#     #         if user.name  == userName: 
#     #             self.onlineUsers.remove(user) 
    
#     # def getOnlineUsers(self): 
#     #     response_string = ""
#     #     for user in self.onlineUsers: 
#     #         response_string.append(user.name + " is online.\n")
#     #     if len(self.onlineUsers) == 0: 
#     #         response_string = "There are currently no users online." 
#     #     return response_string
        
#     # def broadcast(self, userName): 
   
# # if os.argv < 3:
# #     print("Usage: python server.py <server_port> <block_duration> <timeout>") 
# #     os.exit(1) 

# # serverPort = os.argv[1]
# # blockDuration = os.argv[2] 
# # timeout = os.argv[3] 

# # For testing, going to use the static values 
serverPort = 5000
blockDuration = 2
timeout = 2
# server = Server(serverPort, blockDuration, timeout) 
# server.listen() 
