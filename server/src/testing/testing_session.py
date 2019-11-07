""" Testing code to check time checking mechanisms """

import time 
import unittest 
import sys 
from Session import Session 

def test_timeBeforeSession(): 
    TEST_TIME = time.time()
    time.sleep(1)

    s = Session.createSession() 
    s.endSession() 

    assert s.isSessionWithin(TEST_TIME) == True

def test_timeDuringSession(): 
    s = Session.createSession() 
    time.sleep(1)

    TEST_TIME = time.time()
    time.sleep(1)

    s.endSession() 

    assert s.isSessionWithin(TEST_TIME) == True

def test_timeAfterSession(): 
    s = Session.createSession() 
    time.sleep(1)
    s.endSession() 

    TEST_TIME = time.time()
    time.sleep(1)

    assert s.isSessionWithin(TEST_TIME) == False
