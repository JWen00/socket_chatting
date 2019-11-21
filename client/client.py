import sys 
from socket import *
from clientClass import Client


if len(sys.argv) < 3: 
    print("Usage: python client.py <serverPort> <portNumber>") 
    os.exit() 

serverIP = sys.argv[1]
serverPort = int(sys.argv[2])

try: 
    c = Client(serverIP, serverPort) 
except FileNotFoundError: 
    sys.exit()

loginSuccess = False
while not loginSuccess:
    username = input("Username: ") 
    password = input("Password: ") 
    loginSuccess =  c.login(username, password) 

c.listen()
