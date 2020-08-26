import json 
import time
import sys
from .session import Session
from .exceptions.clientExceptions import *

""" Manages client authentication and client information"""
class ClientManager(): 
    def __init__(self, blockDuration):

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

            self._clients.append({ 
                "socket" : None, 
                "status" : "inactive", 
                "lastActive" : None, 
                "username" : username, 
                "currSession" : None,
                "sessions" : [], 
                "blockedUsers" : [], 
                })

        self._serverStartTime = time.monotonic() 
        self._loginAttempts = {}
        self._blockDuration = blockDuration 
        self._unreadMessages = {} 

    def updateClient(self, socket, username): 
        """ Updates client information after successful login """

        client = self.getClientByUsername(username) 
        client["socket"] = socket
        client["status"] = "active"
        client["lastActive"] = time.monotonic()
        client["currSession"] = Session.createSession()
         
    def updateLastActive(self, clientSocket): 
        """ Updates last active time """ 

        try: 
            client = self.getClientBySocket(clientSocket) 
            client["lastActive"] = time.monotonic()
        except ErrorClientNotFound as e: 
            sys.exit()

    def addUnreadMessages(self, messageData):  
        """ Adds unread messages to bank of unread messages """ 

        source = messageData["source"] 
        target = messageData["target"]
        message = messageData["message"] 

        if target in self._unreadMessages: 
            self._unreadMessages[target].append(f' <Message from {source}> {message}')
        else: self._unreadMessages[target] = [f' <Message from {source}> {message}']

    def retrieveUnreadMessage(self, username): 
        if username in self._unreadMessages: 
            return self._unreadMessages[username] 
        else: return []

    def closeClientSession(self, socket): 
        """ Manage client's session when socket disconnects """

        client = self.getClientBySocket(socket) 
        client["currSession"].endSession() 
        oldSession = client["currSession"] 
        client["sessions"].append(oldSession)
        client["currSession"] = None 
        client["status"] = "inactive" 

    def getClientByUsername(self, username): 
        for client in self._clients: 
            if client["username"] == username: return client 
        
        raise ErrorClientNotFound # This shouldn't happen

    def getClientBySocket(self, socket): 
        for client in self._clients: 
            if client["socket"] == socket: return client 
        
        return None

    def authenticateClient(self, username, password): 
        """ Checks if a client has logged in and returns "blocked", "alreadyActive" or "success" """

        try: 
            # User already active
            client = self.getClientByUsername(username)
            if client["status"] == "active": return "alreadyActive"
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
                client = self.getClientByUsername(username) 
                client["lastActive"] = time.monotonic()
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
            if client["status"] == "active": 
                result.append(client["username"])
                continue

            if time: 
                for session in client["sessions"]: 
                    if session.isSessionWithin(time):
                        result.append(client["username"]) 
        
        return result 

    def hasBeenBlocked(self, clientName): 
        for client in self._clients: 
            if clientName in client["blockedUsers"]: return True 
        return False 

    def getSocketToAvoid(self, clientName): 
        """ Get sockets of users who have blocked the client && client's own socket """
        
        sockets = []

        clientSocket = self.getClientByUsername(clientName)["socket"] 
        if clientSocket: sockets.append(clientSocket) 

        for client in self._clients: 
            if clientName in client["blockedUsers"]: sockets.append(client["socket"])

        return sockets
        
    def block(self, sourceName, targetName, action="block"): 
        """ Blocks and unblocks depending on action """ 

        target = self.getClientByUsername(targetName) 
        client = self.getClientByUsername(sourceName)

        if action =="block": 
            client["blockedUsers"].append(targetName)
            return 

        if targetName not in client["blockedUsers"]: 
            raise ErrorClientNotFound
        client["blockedUsers"].remove(targetName) 
        
        


        
        