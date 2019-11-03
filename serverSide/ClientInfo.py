import time
class ClientInfo(): 
    def __init__(self, socket): 
        self.socket = socket
        self.status = "active" 
        self.lastActive = None 
        self.username = None 
        self.currSession = None
        self.sessions = [] 
        self.blockedUsers = [] 

    def getJSONString(self): 
        return json.dumps({
            "sessions" : self.sessions, 
            "blockedUsers" : self.blockedUsers
        })
     