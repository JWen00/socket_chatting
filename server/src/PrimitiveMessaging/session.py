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

    def isSessionWithin(self, time): 
        if self.status == "active" or self.sessionEnd >= time: 
            return True
        return False
        



