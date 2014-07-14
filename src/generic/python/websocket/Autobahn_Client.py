'''
Created on 10.07.2014

@author: mend_ma
'''
from twisted.internet import reactor
from twisted.internet.defer import inlineCallbacks

from autobahn.twisted.wamp import ApplicationSession, ApplicationRunner
import logging
from threading import Event, Thread
import time
import signal
import random
from generic.python.websocket.Autobahn_Dataparser import Autobahn_Dataparser

class Autobahn_Client(ApplicationSession):
    '''
    classdocs
    '''
    uRC_MODULE_NAME = "abstract_client"
    PARSER_FILE = "./config/definitions.xml"
    LOGGER = None
    _parser = None
    
    _pendingAnswers = {}
    _rpcsToComplete = 0
    

    _subscriptions = dict()
    _rpcs = {}
    
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
        self.LOGGER.info("disconnected")
        reactor.stop()  # @UndefinedVariable FIXME: Actually this method exists
        
    def _initSubscriptions(self):
        pass
        
    def _initRpcs(self):
        pass

    def _startupComponents(self):
        signal.signal(signal.SIGINT, self.shutdown)
        self._parser = Autobahn_Dataparser(self.LOGGER, self.PARSER_FILE)
        
    def _rpc_received(self):
        self._rpcsToComplete += 1
        
    def _rpc_completed(self):
        self._rpcsToComplete -= 1
        
    def _handle_RPC(self, function, data):
        self._rpc_received()
        try:
            result = function(data)
            self._rpc_completed()
            return result
        except Exception as e:
            self._rpc_completed()
            raise e
        
    
    def publish(self, topic, *args, **kwargs):
        self.LOGGER.debug("PUB-fired")
        return ApplicationSession.publish(self, topic, *args, **kwargs)
    
    def remoteCall(self, url , *args, **kwargs):
        call_lock = Event()
        call_lock.clear()
        callback_id = url+str(time.time())+str(random.randint(0,10000))
        self._pendingAnswers[callback_id] = (call_lock, None)
        self.LOGGER.debug("RPC-request: " + url)
        self._remoteCall_fire(url, callback_id, *args, **kwargs)
        call_lock.wait()
        call_lock, value = self._pendingAnswers.pop(callback_id)
        self.LOGGER.debug("RPC-response: " + url)
        return value
    
    @inlineCallbacks
    def _remoteCall_fire(self, url, callback_id, *args, **kwargs):
        result = yield self.call(url, *args, **kwargs)
        self._remoteCall_catch(callback_id, result)
        
    def _remoteCall_catch(self, callback_id, result):
        call_lock, value = self._pendingAnswers[callback_id]  # @UnusedVariable
        value = result
        self._pendingAnswers[callback_id] = (call_lock, value)
        call_lock.set()
        
    def shutdown(self, *args, **kwargs):
        def try_shutdown():
            while self._rpcsToComplete > 0:
                self.LOGGER.info("waiting for remote-procedures to complete....")
                time.sleep(1)
            self.leave()
        self.LOGGER.info("shutting down component")
        Thread(target=try_shutdown).start()

        
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    Autobahn_Client.startup_client(Autobahn_Client)