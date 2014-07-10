'''
Created on 10.07.2014

@author: mend_ma
'''
from generic.python.websocket.Autobahn_Client import Autobahn_Client
import logging
import time

class TestReceiver(Autobahn_Client):
    '''
    classdocs
    '''
    
    uRC_MODULE_NAME = "TestReceiver"
    
    def _initSubscriptions(self):
        Autobahn_Client._initSubscriptions(self)
        self._subscriptions["uRC.testing.receiver.data"] = self.receiveData
        
    def _initRpcs(self):
        Autobahn_Client._initRpcs(self)
        self._rpcs["uRC.testing.receiver.rpc"] = self.handleRPC
        
    def _startupComponents(self):
        Autobahn_Client._startupComponents(self)
        
    def receiveData(self, data):
        print "received: ", data
        
    def handleRPC(self, value, index):
        print value+":"+str(index)
        time.sleep(3)
        return "pong:" + str(index)
        
        
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    Autobahn_Client.startup_client(TestReceiver)