'''
Created on 10.07.2014

@author: mend_ma
'''
from generic.python.websocket.Autobahn_Client import Autobahn_Client
import logging
from threading import Thread, Event
import time

class TestEmitter(Autobahn_Client):
    '''
    classdocs
    '''    
    PARSER_FILE = "../config/definitions.xml"
    uRC_MODULE_NAME = "TestEmitter"
    worker = None
    
    def _initSubscriptions(self):
        Autobahn_Client._initSubscriptions(self)
        
    def _initRpcs(self):
        Autobahn_Client._initRpcs(self)
        
    def _startupComponents(self):
        Autobahn_Client._startupComponents(self)
        self.worker = EmitterThread(self)
        self.worker.start()
        
    def publishTestData(self, data):
        self.publish("uRC.testing.receiver.data", data)
        
    def testPing(self, i):
        result = self.remoteCall("uRC.testing.receiver.rpc.TestReceiver", {"ping":"ping","index":i})
        if self._parser.parse_response("uRC.testing.receiver.rpc", result):
            return result["ping"]
        else:
            return "error occured: no valid data received"
    
    def onDisconnect(self):
        self.worker.interrupt()
        Autobahn_Client.onDisconnect(self)
        
class EmitterThread(Thread):
    emitter = None
    interrupted = False
    rpc_was_called = Event()
    def __init__(self, emitter, group=None, target=None, name="emitter", args=(), kwargs=None, verbose=None):
        Thread.__init__(self, group=group, target=target, name=name, args=args, kwargs=kwargs, verbose=verbose)
        self.emitter = emitter
        
    def interrupt(self):
        self.interrupted = True
        
    def handleResult_testPing(self, data):
        print "callback received: " + data
        self.rpc_was_called.set()
        
    def run(self):
        Thread.run(self)
        for i in range(10):
            if self.interrupted:
                break
            time.sleep(2)
            print "==run # " + str(i) + "=="
            
            print "publishing..."
            #data = {"message":"This is " + self.emitter.uRC_MODULE_NAME + " testing subscription 'uRC.testing.receiver.data'", "index":i}
            data ={"orientation":{"pitch":0.0, "roll":0.0,"yaw":0.0}}
            self.emitter.publishTestData(data)
            print "done"
            time.sleep(2)
            
            
            print "calling rpc..."
            result = self.emitter.testPing(i)
            print "done, result:", result
        self.emitter.leave()
        
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    Autobahn_Client.startup_client(TestEmitter)