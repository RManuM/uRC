'''
Created on 10.07.2014

@author: mend_ma
'''
from twisted.internet import reactor
from twisted.internet.defer import inlineCallbacks

from autobahn.twisted.wamp import ApplicationSession, ApplicationRunner
import logging
from threading import Event
import time
import random
from generic.python.websocket.Autobahn_Dataparser import Autobahn_Dataparser
import atexit

class Autobahn_Client(ApplicationSession):
    '''
    classdocs
    '''
    uRC_MODULE_NAME = "abstract_client"
    PARSER_FILE = "./config/definitions.xml"
    LOGGER = None
    _parser = None
    
    _pendingRPCs = {}

    _subscriptions = dict()
    _rpcs = {}
    
#     @staticmethod
#     def startup_client(implementation, server_url="ws://127.0.0.1:8080/ws", server_name="realm1"):
#         runner = ApplicationRunner(server_url, server_name)
#         runner.run(implementation)
        
    @staticmethod
    def startup_client(implementation, server_url="ws://127.0.0.1:8080/ws", server_name="realm1"):
        runner = ApplicationRunner(server_url, server_name)
        runner.run(implementation)
        
    @inlineCallbacks
    def onJoin(self, details):
        self.LOGGER = logging.getLogger(self.uRC_MODULE_NAME)
        self.LOGGER.info("joining server")

        self.received = 0
        self._initSubscriptions()
        self.LOGGER.info("setting up subscriptions")
        for key, value in self._subscriptions.items():
            yield self.subscribe(value, key)
            
        self.LOGGER.info("setting up rpc-slots")
        self._initRpcs()
        for key, value in self._rpcs.items():
            yield self.register(value, key)
        
        self.LOGGER.info("starting components")
        self._startupComponents()
        self.LOGGER.info("client ready")

    def onDisconnect(self):
        ## TODO: closing pendings rpcs
        for key, value in self._pendingRPCs.items():
            print "removing rpc"
            call_lock, data = value
            data = {"error_message":"closing connection"}
            self._pendingRPCs[key] = (call_lock, data)
            call_lock.set()
            
        self.LOGGER.info("disconnected")
        reactor.stop()  # @UndefinedVariable FIXME: Actually this method exists
        
    def _initSubscriptions(self):
        pass
        
    def _initRpcs(self):
        pass

    def _startupComponents(self):
        atexit.register(self.leave)
        self._parser = Autobahn_Dataparser(self.LOGGER, self.PARSER_FILE)
    
    def publish(self, topic, *args, **kwargs):
        self.LOGGER.debug("PUB-fired")
        return ApplicationSession.publish(self, topic, *args, **kwargs)
    
    def remoteCall(self, url , *args, **kwargs):
        call_lock = Event()
        call_lock.clear()
        callback_id = url+str(time.time())+str(random.randint(0,10000))
        self._pendingRPCs[callback_id] = (call_lock, None)
        self.LOGGER.debug("RPC-request: " + url)
        self._remoteCall_fire(url, callback_id, *args, **kwargs)
        call_lock.wait()
        call_lock, value = self._pendingRPCs.pop(callback_id)
        self.LOGGER.debug("RPC-response: " + url)
        return value
    
    @inlineCallbacks
    def _remoteCall_fire(self, url, callback_id, *args, **kwargs):
        result = yield self.call(url, *args, **kwargs)
        self._remoteCall_catch(callback_id, result)
        
    def _remoteCall_catch(self, callback_id, result):
        call_lock, value = self._pendingRPCs[callback_id]  # @UnusedVariable
        value = result
        self._pendingRPCs[callback_id] = (call_lock, value)
        call_lock.set()

        
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    Autobahn_Client.startup_client(Autobahn_Client)