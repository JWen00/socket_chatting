import json 
import time
import os 
from Session import Session
from exceptions.clientExceptions import *

""" Manages client authentication and client information"""
class ClientManager(): 
    def __init__(self):
        self._clients = []

        def loadClientBlockingData(filePath): 
            data = None 
            with open(filePath, "r") as f: 
                data = f.read() 
                if not data: 
                    return None
            return json.loads(data)
        self._clientBlockingData = loadClientBlockingData("blockingData.txt") 

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
            self._login_credentials = loadCredentialsFile("credentials.txt")
        except FileNotFoundError as e: 
            print("Credential file not found")
            os.exit()

        self._serverStartTime = time.time() 
        self._loginAttempts = {}

def getClients(self): 
    return self.clients

def addClient(self, socket):
    self.clients.append(newClient = { 
        "socket" : socket, 
        "status" : "active", 
        "lastActive" : None, 
        "username" : None, 
        "currSession" : None,
        "sessions" : [], 
        "blockedUsers" : [] 
    })

def removeClient(self, socket): 
    for client in self.clients:
        if client["socket"] == socket: self.client.remove(client) 

def getClientByUsername(self, username): 
    for client in self.clients: 
        if client["username"] == username: return username 
    raise ErrorClientNotFound

def getClientBySocket(self, socket): 
    for client in self.clients: 
        if client["socket"] == socket: return client 
    raise ErrorClientNotFound

def updateClient(self, socket, username): 
    client = getClientBySocket(socket) 
    client["username"] = username 
    client["lastActive"] = time.time()
    client["currSession"] = Session.createSession()

def authenticateClient(self, username, password): 
    if username in self._loginAttempts: 
        userInfo = self._loginAttempts.get(username) 

    def isBlocked(userInfo):
        if userInfo.get("status") != "blocked":  return False
        if time.time() - userInfo.get("blockTime") > self._blockDuration:
            userInfo["status"] == "unsuccessful"
            return False
        return True
            
    if isBlocked(userInfo): return "blocked"

    # Check if user is active
    try: 
        client = getClientByUsername(username) 
        return "alreadyActive"
    except ErrorClientNotFound as e: 
        pass

    # Check for correct login 
    for credential in self._login_credentials: 
        if credential["username"] == username and credential["password"] == password: 

            # Delete previous attempts, if any
            if username in self._loginAttempts: del self._loginAttempts[username]
            print("Login success for user: " + username)
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

    else: 
        self._loginAttempts[username] = { 
            "attempts" : 1, 
            "status" : "unsuccessful" 
        } 
        
    return "wrongCredentials"

def getActiveClients(self): 
    result = []
    for client in self._clients: 
        if client.status == "active": result.append(client["username"]) 
    return result 

def getClientsActiveSince(self, time): 
    result = [] 
    for client in self._clients: 
        if client["status"] == "active": result.append(client["username"]) 
        else: 
            for session in client["sessions"]: 
                if session.wasActiveSince(time): result.append(client["username"]) 

    return result
