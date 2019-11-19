from src.Server import Server

# # if os.argv < 3:
# #     print("Usage: python server.py <server_port> <block_duration> <timeout>") 
# #     os.exit(1) 

# # serverPort = os.argv[1]
# # blockDuration = os.argv[2] 
# # timeout = os.argv[3] 

serverPort = 5000
serverName = "localhost"
blockDuration = 5
timeout = 5
s = Server(serverName, serverPort, blockDuration, timeout)
s.listen()


