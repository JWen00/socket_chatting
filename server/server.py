from src.Server import Server
import sys

if len(sys.argv) < 3:
    print("Usage: python server.py <server_port> <block_duration> <timeout>") 
    sys.exit(1) 

serverPort = int(sys.argv[1])
blockDuration = int(sys.argv[2])
timeout = int(sys.argv[3])

# serverPort = 5000
# blockDuration = 5

serverName = "localhost"
s = Server(serverName, serverPort, blockDuration, timeout)
s.listen()


