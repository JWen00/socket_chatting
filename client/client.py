from socket import *
import select 
import sys
import threading
import json

class Client(): 
    def __init__(self, name): 
        self._name = name
        self._socket = None 
        self.status = "active"

    def bindSocket(self, socket): 
        self._socket = socket 
        
    def listen(self): 
        # Main thread for listening and second for getting responses
        t = threading.Thread(target=self.listenToServer) 
        # t.daemone = True 
        t.start()  

        def getCommand(): 
            command = None 
            try: 
                command = input(self._name + " >> ") 
                command = command.split(" ") 
            except KeyboardInterrupt:
                pass 
            
            if len(command) > 1: 
                args = command[1:] 
                self._socket.send(self.constructReq(command, args)) 
            else: 
                self._socket.send(self.constructReq(command))

        while True: 
            getCommand() 

    def listenToServer(self): 
        ready = select.select([self._socket], [],[]) 
        if ready[0]: 
            response = self._socket.recv(1024) 
            status, data = self.decodeResponse(response) 

            try: 
                if status == "success": print("Success! " + data.get("message")) 
                else:  print(f'Command {data.get("command")} unsuccessful\nError message: {data.get("message")}')
            except KeyError as e: 
                print("This really shouldn't happen..") 

            if data.get("command") == "exit": 
                self._socket.close() 
                print("ByeBye! :)") 
                sys.exit() 
            
    @staticmethod
    def constructReq(command, data={}): 
        req = {} 
        req["command"] = command 
        req["data"] = data
        req = json.dumps(req) 
        req = req.encode() 
        return req 

    @staticmethod
    def decodeResponse(response): 
        response = response.decode() 
        response = json.loads(response) 
        status = response.get("status") 
        data = response.get("data") 
        return status, data 

    # Prompt the user to log in
    @staticmethod
    def login(clientSocket): 
        username = input("Username: ") 
        password = input("Password: ") 

        req = Client.constructReq("login", data = { 
            "username" : username, 
            "password" : password 
        })
        clientSocket.send(req) 
        reply = clientSocket.recv(1024)
        status, data = Client.decodeResponse(reply)
        if status == "success": 
            c = Client(username)
            return c

        print(f'Unsuccessful: " {data.get("message")}') 
        return None
