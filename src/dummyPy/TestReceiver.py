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
    PARSER_FILE = "../config/definitions.xml"
    uRC_MODULE_NAME = "TestReceiver"
    
    def _initSubscriptions(self):
        Autobahn_Client._initSubscriptions(self)
        self._subscriptions["uRC.testing.receiver.data"] = self.handleTopic
        
    def _initRpcs(self):
        Autobahn_Client._initRpcs(self)
        self._rpcs["uRC.testing.receiver.rpc."+self.uRC_MODULE_NAME] = self.handleRPC
        
    def _startupComponents(self):
        Autobahn_Client._startupComponents(self)
        
    def handleTopic(self, data):
        if self._parser.parse("uRC.testing.receiver.data", data):
            print "received: ", data
        else:
            print "received message contains error", data
        
    def handleRPC(self, data):
        def function(data):
            result = ""
            if self._parser.parse("uRC.testing.receiver.rpc", data):
                print "RPC: Data:" + str(data)
                time.sleep(3)
                result = "pong:" + str(data["index"])
            else:
                print "RPC: Data contains error: " + str(data)
                result = "received rpc contains error"
            return {"ping":result}
        return self._handle_RPC(function, data)
        
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    Autobahn_Client.startup_client(TestReceiver)