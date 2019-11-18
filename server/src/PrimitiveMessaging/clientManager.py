import json 
import time
import sys
from .session import Session
from .exceptions.clientExceptions import *

""" Manages client authentication and client information"""
class ClientManager(): 
    def __init__(self, blockDuration):

        # Loading Blocking Data
        data = None 
        with open("docs/blockingData.txt", "r") as f: 
            data = f.read() 
            if not data: self._clientBlockingData = None 
            else: self._clientBlockingData = json.loads(data)

        # Loading Login Credentials Data 
        data = None
        with open("docs/credentials.txt", "r") as f: 
            data = f.read().splitlines()
        if not data: 
            print("Missing credentails file.")
            raise FileNotFoundError 

        self._login_credentials = []
        self._clients = []
        for line in data:
            username, password = line.split(" ", 1)
            newLogin = {
                "username" : username, 
                "password" : password 
            }
            self._login_credentials.append(newLogin)

            if self._clientBlockingData is not None and username in self._clientBlockingData: 
                userBlockList = self._clientBlockingData[username]
            else: userBlockList = []

            self._clients.append({ 
                "socket" : None, 
                "status" : "inactive", 
                "lastActive" : None, 
                "username" : username, 
                "currSession" : None,
                "sessions" : [], 
                "blockedUsers" : userBlockList, 
                })

        self._serverStartTime = time.monotonic() 
        self._loginAttempts = {}
        self._blockDuration = blockDuration 
        self._unreadMessages = {} 

    def getClients(self): 
        return self.clients

    def addClient(self, socket):
        self._clients.append({ 
            "socket" : socket, 
            "status" : "active", 
            "lastActive" : time.monotonic(), 
            "username" : None, 
            "currSession" : None,
            "sessions" : [], 
            "blockedUsers" : [], 
        })

    def updateClient(self, socket, username): 
        """ Updates client information after successful login """

        client = self.getClientBySocket(socket) 
        client["username"] = username 
        client["lastActive"] = time.monotonic()
        client["currSession"] = Session.createSession()
         
    def updateLastActive(self, clientSocket): 
        try: 
            client = self.getClientBySocket(clientSocket) 
            client["lastActive"] = time.monotonic()
        except ErrorClientNotFound as e: 
            print("Cannot update last active - Client doesn't exist yet") 
            sys.exit()

    def addUnreadMessages(self, messageData): 
        source = messageData["source"] 
        target = messageData["target"]
        message = messageData["message"] 

        if target in self._unreadMessages: 
            self._unreadMessages[target].append(f'  <Message from {source}> {message}')
        else: self._unreadMessages[target] = [f'  <Message from {source}> {message}']

    def retrieveUnreadMessage(self, username): 
        if username in self._unreadMessages: 
            return self._unreadMessages[username] 
        else: return []

    def closeClientSession(self, socket): 
        """ Manage client's session when socket disconnects """

        try: 
            client = self.getClientBySocket(socket) 

            # Client never logged in
            if client["currSession"] == None: return

            client["currSession"].endSession() 
            oldSession = client["currSession"] 
            client["sessions"].append(oldSession)
            client["currSession"] = None 
            client["status"] = "inactive" 
            client["socket"] = None 

        except ErrorClientNotFound: 
            return 

    def getClientByUsername(self, username): 
        for client in self._clients: 
            if client["username"] == username: return client 
        
        raise ErrorClientNotFound # This shouldn't happen

    def getClientBySocket(self, socket): 
        for client in self._clients: 
            if client["socket"] == socket: return client 
        raise ErrorClientNotFound

    def authenticateClient(self, username, password): 
        """ Checks if a client has logged in and returns "blocked", "alreadyActive" or "success" """

        try: 
            # User already active
            client = self.getClientByUsername(username)
            if client["socket"]: return "alreadyActive"
        except ErrorClientNotFound: 
            pass 

        def addUserAttempt(username): 
            self._loginAttempts[username] = { 
                    "status" : "active", 
                    "attempts" : 0, 
                    "blockTime" : None
            }
            return self._loginAttempts[username]

        try: 
            # User has attempted login before
            client = self._loginAttempts[username]
            if client["status"] == "blocked": 
                if time.monotonic() - client["blockTime"] < self._blockDuration: return "blocked" 
                del self._loginAttempts[username] 
                client = addUserAttempt(username) 
                
        except KeyError: 
            # First time trying to login
            client = addUserAttempt(username) 

        # Check whether it's correct login 
        for credential in self._login_credentials: 
            if credential["username"] == username and credential["password"] == password: 
                del self._loginAttempts[username] 
                return "success"

        # Incorrect username/password 
        client["attempts"] += 1
        if client["attempts"] == 3: 
            client["status"] = "blocked" 
            client["blockTime"] = time.monotonic() 
            return "blocked"

        return "wrongCredentials"

    def getActiveClients(self, time=None): 
        result = []
        for client in self._clients: 
            if client["status"] == "active": result.append(client["username"]) 

            if time: 
                for session in client["sessions"]: 
                    if session.isSessionWithin(time): result.append(client["username"]) 

        return result 

    def getSocketsWhoBlockedClient(self, clientSocket): 
        source = self.getClientBySocket(clientSocket) 
        clientUsername = source["username"] 
    
        sockets = [] 
        for client in self._clients: 
            if clientUsername in client["blockedUsers"]:
                sockets.append(client["socket"])

        return sockets 

    def getSocketsNotBlockedBy(self, clientSocket): 
        socketsWhoHaveBlockedClient = self.getSocketsWhoBlockedClient(clientSocket)
        sockets = [] 
        for client in self._clients:
            if client["username"] not in socketsWhoHaveBlockedClient and client["socket"] is not None: 
                sockets.append(client["socket"]) 
        return sockets    
        
    def block(self, sourceName, targetName, action="block"): 
        
        target = self.getClientByUsername(targetName) 
        client = self.getClientByUsername(sourceName)

        if action =="block": client["blockedUsers"].append(targetName)
        else: client["blockedUsers"].remove(targetName) 
        
        


        
        