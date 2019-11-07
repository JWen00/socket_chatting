import unittest
import time
from clientManager import ClientManager

def test_authenticateClient():
    cm = ClientManager(10)
    # Success 
    assert cm.authenticateClient("jenn", "ifer") == "success" 

    # Currently Active
    cm.addClient("socket")
    cm.updateClient("socket", "jenn") 
    assert cm.authenticateClient("jenn", "ifer") == "alreadyActive"

    # Unsuccessful 
    assert cm.authenticateClient("asd", "asd") == "wrongCredentials" 

    # Blocked 
    cm.authenticateClient("qwe", "qwe") 
    cm.authenticateClient("qwe", "qwe") 
    cm.authenticateClient("qwe", "qwe") 
    assert cm.authenticateClient("qwe", "qwe") == "blocked"

def test_blocking(): 

    cm = ClientManager(10)
    cm.addClient("s1") 
    cm.updateClient("s1", "A") 

    cm.addClient("s2") 
    cm.updateClient("s2", "B") 

    cm.block("A", "B") 
    clientA = cm.getClientByUsername("A") 
    print("CLIENT: " + str(clientA["blockedUsers"]))

    assert ("B" in clientA["blockedUsers"]) == True

    cm.block("A", "B", "unblock") 
    assert ("B" in clientA["blockedUsers"]) == False

def test_closeClientSession(): 
    cm = ClientManager(10)
    cm.addClient("s1") 
    cm.updateClient("s1", "A") 

    cm.closeClientSession("s1") 
    clientA = cm.getClientByUsername("A") 
    assert len(clientA["sessions"]) == 1 
    assert clientA["currSession"] == None 



def test_whoElse(): 
    cm = ClientManager(10)
    cm.addClient("s1") 
    cm.updateClient("s1", "A") 

    cm.addClient("s2") 
    cm.updateClient("s2", "B") 

    cm.addClient("s3") 
    cm.updateClient("s3", "C") 

    assert len(cm.getActiveClients()) == 3 
    
    cm.closeClientSession("s1") 
    assert len(cm.getActiveClients()) == 2 

# Not tested
def test_whoElseSince_withOfflineClients():

    startTime = time.time()

    cm = ClientManager(10)
    cm.addClient("s1") 
    cm.updateClient("s1", "A") 

    cm.addClient("s2") 
    cm.updateClient("s2", "B") 

    cm.addClient("s3") 
    cm.updateClient("s3", "C") 

    assert len(cm.getClientsActiveSince(startTime)) == 3 
    
    cm.closeClientSession("s1") 
    assert len(cm.getClientsActiveSince(startTime)) == 3

