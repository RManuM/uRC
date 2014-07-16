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


from autobahn.twisted.wamp import ApplicationSessionFactory
from autobahn.twisted.websocket import WampWebSocketClientFactory         
from twisted.internet.endpoints import clientFromString
from autobahn.wamp import types

class Autobahn_Client(ApplicationSession):
    '''
    classdocs
    '''
    def __init__(self, module_name, parser_file, config=types.ComponentConfig(u"anonymous")):
        self.uRC_MODULE_NAME = module_name
        self.PARSER_FILE = parser_file
        self.LOGGER = None
        self._parser = None
        
        self._pendingAnswers = {}
        self._pendingRPCs = {}
        self._rpcsToComplete = 0
        
        self._subscriptions = dict()
        self._rpcs = {}
        
        ApplicationSession.__init__(self, config=config)
    
    @staticmethod
    def startup_client(implementation, server_url="ws://127.0.0.1:8080/ws", server_name="realm1"):
        runner = ApplicationRunner(server_url, server_name)
        runner.run(implementation)
        
    @staticmethod
    def startup_client_2(implementation, server_url="ws://localhost:8080/ws", server_bindings="tcp:localhost:8080"):
        session_factory = ApplicationSessionFactory()
        session_factory.session = implementation
        
        transport_factory = WampWebSocketClientFactory(session_factory, server_url)

        client = clientFromString(reactor, server_bindings)
        client.connect(transport_factory)
        
        
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
        self.LOGGER.info("client ready, session-ID=" + str(self._session_id))

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
        
    def _handle_RPC(self, function, data):        
        self._rpcsToComplete +=1
        try:
            result = function(data)
            self._rpcsToComplete -= 1
            return result
        except Exception as e:
            self._rpcsToComplete -= 1
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