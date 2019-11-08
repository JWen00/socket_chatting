from src.Server import Server
import unittest
import pytest

@pytest_fixture
def createClient(): 
    serverPort = 5000
    serverName = "localhost" 
    clientSocket = socket(AF_INET, SOCK_STREAM) 
    clientSocket.connect((serverName, serverPort)) 
    return clientSocket

def test_serverListening(): 
    pass 
