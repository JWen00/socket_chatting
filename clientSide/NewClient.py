from socket import *
import select 
import sys
import json

class NewClient(): 
    def __init__(self, name): 
        self._name = name
        self._socket = None 
        self.status = "active"

    def bindSocket(self, socket): 
        self._socket = socket 

    def listen(self): 
        while True: 
            command = None 
            try: 
                command = input(self._name + ": ") 
            except KeyboardInterrupt:
                pass 
            
            if command == "exit": 
                self._socket.send(constructReq("exit")) 
                self._socket.close() 
                print("ByeBye :)")
                sys.exit()
            else: 
                print("Command Unknown...  YEEeet") 

    @staticmethod
    def constructReq(command, data=None): 
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
