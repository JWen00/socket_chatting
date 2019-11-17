import json 
import time
import sys
from .session import Session
from .exceptions.clientExceptions import *

""" Manages client authentication and client information"""
class ClientManager(): 
    def __init__(self, blockDuration):
        def loadClientBlockingData(filePath): 
            data = None 
            with open(filePath, "r") as f: 
                data = f.read() 
                if not data: 
                    return None
            return json.loads(data)
        self._clientBlockingData = loadClientBlockingData("docs/blockingData.txt") 

        def loadCredentialsFile(filePath): 
            data = None
            with open(filePath, "r") as f: 
                data = f.read().splitlines()

            if not data: 
                raise FileNotFoundError 

            credentials_list = []
            for line in data:
                username, password = line.split(" ", 1)
                new_login = {}
                new_login["username"] = username
                new_login["password"] = password
                credentials_list.append(new_login) 
                
            return credentials_list
        # Get credentials file 
        try: 
            self._login_credentials = loadCredentialsFile("docs/credentials.txt")
        except FileNotFoundError as e: 
            print("Credential file not found")
            sys.exit()

        self._serverStartTime = time.time() 
        self._loginAttempts = {}
        self._blockDuration = blockDuration * 1000
        self._clients = []
        self._unreadMessages = {} 

    def getClients(self): 
        return self.clients

    def addClient(self, socket):
        self._clients.append({ 
            "socket" : socket, 
            "status" : "active", 
            "lastActive" : time.time(), 
            "username" : None, 
            "currSession" : None,
            "sessions" : [], 
            "blockedUsers" : [], 
        })

    def updateClient(self, socket, username): 
        """ Updates client information after successful login """

        client = self.getClientBySocket(socket) 
        client["username"] = username 
        client["lastActive"] = time.time()
        client["currSession"] = Session.createSession()
         
    def updateLastActive(self, clientSocket): 
        try: 
            client = self.getClientBySocket(clientSocket) 
            client["lastActive"] = time.time()
        except ErrorClientNotFound as e: 
            print("Cannot update last active - Client doesn't exist yet") 
            sys.exit()

    def addUnreadMessages(self, messageData): 
        source = messageData["source"] 
        target = messageData["target"]
        message = messageData["message"] 

        if target in self._unreadMessages: 
            self._unreadMessages[target].append(f'  <Message from {source}> {message}\n')
        else: self._unreadMessages[target] = [f'  <Message from {source}> {message}\n']

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
        
        for login in self._login_credentials: 
            if login["username"] == username: 
                tempClient = { 
                    "socket" : None, 
                } 
                return tempClient 
        raise ErrorClientNotFound

    def getClientBySocket(self, socket): 
        for client in self._clients: 
            if client["socket"] == socket: return client 
        raise ErrorClientNotFound

    def authenticateClient(self, username, password): 
        """ Checks if a client has logged in and returns "blocked", "alreadyActive" or "success" """

        # Check if user is blocked
        if username in self._loginAttempts: 
            userInfo = self._loginAttempts.get(username) 

            def isBlocked(userInfo):
                if userInfo.get("status") != "blocked":  return False

                print("Time since user has been blocked: " + str(time.time() - userInfo.get("blockTime")))
                if time.time() - userInfo.get("blockTime") > self._blockDuration:
                    userInfo["status"] == "unsuccessful"
                    return False
                return True
                    
            if isBlocked(userInfo): return "blocked"

        # Check if user is active
        try: 
            client = self.getClientByUsername(username) 
            if client["socket"]: return "alreadyActive"
        except ErrorClientNotFound as e: 
            pass

        # Check for correct login 
        for credential in self._login_credentials: 
            if credential["username"] == username and credential["password"] == password: 

                # Delete previous attempts, if any
                if username in self._loginAttempts: del self._loginAttempts[username]
                print(f'{username} has logged on')
                return "success"

        # Incorrect Login
        if username in self._loginAttempts: 
            self._loginAttempts[username]["attempts"] += 1 
            if self._loginAttempts[username]["attempts"] == 3:
                self._loginAttempts[username] = { 
                    "status" : "blocked", 
                    "attempts" : 0, 
                    "blockTime" : time.time()
                }
                print("{username} has been blocked at time: " + str(time.time()))

        else: 
            self._loginAttempts[username] = { 
                "attempts" : 1, 
                "status" : "unsuccessful" 
            } 
            
        return "wrongCredentials"

    def getActiveClients(self): 
        result = []
        for client in self._clients: 
            if client["status"] == "active": result.append(client["username"]) 
        return result 

    def getClientsActiveSince(self, time): 
        result = [] 
        for client in self._clients: 
            if client["status"] == "active": result.append(client["username"]) 
            else: 
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
        
    def block(self, source, target, action="block"): 

        for credential in self._login_credentials: 
            if credential["username"] == target: 
                t = self.getClientByUsername(source)
                blockedUsers = t["blockedUsers"] 
                if action == "block": blockedUsers.append(target) 
                else: t["blockedUsers"] = [client for client in blockedUsers if client is not target]
                return 
        raise ErrorClientNotFound 

        
        


        
        