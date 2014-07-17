'''
Created on 16.07.2014

@author: mend_ma
'''
from generic.python.websocket.Autobahn_Client import Autobahn_Client
import logging
from autobahn.twisted.choosereactor import install_reactor
from autobahn.wamp import types
import time
from threading import Thread

SERVER_SESSION_ID = 7559482794710710

class TestClient(Autobahn_Client):
    def __init__(self, config=types.ComponentConfig(u"anonymous")):
        PARSER_FILE = "../config/definitions.xml"
        uRC_MODULE_NAME = "TestEmitter"
        Autobahn_Client.__init__(self, uRC_MODULE_NAME, PARSER_FILE)
        
    def _initSubscriptions(self):
        Autobahn_Client._initSubscriptions(self)
        self._subscriptions["uRC.sensor.TRIGGER.COMPLETED"] = self.echo_data
        self._subscriptions["uRC.sensor.TRIGGER.ERROR"] = self.echo_data
        self._subscriptions["uRC.sensor.PROPS"] = self.echo_data
        self._subscriptions["uRC.sensor.STATUS"] = self.echo_data
        
    def _startupComponents(self):
        Autobahn_Client._startupComponents(self)
        Thread(target=do_some_calls, args=[self]).start()
        
    def echo_data(self, data):
        print "data received: {}".format(data)
        
        
def do_some_calls(parent):
    time.sleep(1)
    print "trigger:", parent.remoteCall("uRC.sensor.TRIGGER." + str(SERVER_SESSION_ID), {})
    time.sleep(1)
    print "status get:",parent.remoteCall("uRC.sensor.STATUS.GET." + str(SERVER_SESSION_ID), {})
    time.sleep(1)
    print "props get:",parent.remoteCall("uRC.sensor.PROPS.GET." + str(SERVER_SESSION_ID), {})
    time.sleep(1)
    print "props set:",parent.remoteCall("uRC.sensor.PROPS.SET." + str(SERVER_SESSION_ID), {"orientation":{"pitch":90.0, "roll":0.0, "yaw":0.0}})
    time.sleep(1)
    print "props get:",parent.remoteCall("uRC.sensor.PROPS.GET." + str(SERVER_SESSION_ID), {})
    parent.disconnect()
            
if __name__ == "__main__":
    reactor = install_reactor()
    logging.basicConfig(level=logging.INFO)
    Autobahn_Client.startup_client_2(TestClient)
    reactor.run()