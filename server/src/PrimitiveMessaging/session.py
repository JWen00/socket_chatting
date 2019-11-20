import time

class Session(): 
    def __init__(self, start): 
        self.sessionStart = start
        self.sessionEnd = None
        self.status = "active" 

    @staticmethod
    def createSession(): 
        return Session(time.monotonic())
    
    def endSession(self): 
        self.status = "offline" 
        self.sessionEnd = time.monotonic() 

    def isSessionWithin(self, timeSince):
        if (time.monotonic() - timeSince) < self.sessionStart: 
            return True 
        return False



