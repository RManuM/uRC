'''
Created on 14.07.2014

@author: mend_ma
'''
from generic.python.websocket.Autobahn_Client import Autobahn_Client
import logging
from autobahn.wamp import types
from autobahn.twisted.choosereactor import install_reactor

class Sensor_WebSocket(Autobahn_Client):
    '''
    classdocs
    '''
    def __init__(self, config=types.ComponentConfig(u"anonymous")):
        PARSER_FILE = "../config/definitions.xml"
        uRC_MODULE_NAME = "AscTec_Falcon"
        Autobahn_Client.__init__(self, uRC_MODULE_NAME, PARSER_FILE, config=config)
    
        self._serial = None
    
    def _initSubscriptions(self):
        Autobahn_Client._initSubscriptions(self)
        
    def _initRpcs(self):
        Autobahn_Client._initRpcs(self)
        self.__initRPCs_sensor()
        
    def __initRPCs_sensor(self):
        self._rpcs["uRC.sensor.TRIGGER."+self.uRC_MODULE_NAME] = self.on_trigger
        self._rpcs["uRC.sensor.STATUS.GET."+self.uRC_MODULE_NAME] = self.on_status_get
        self._rpcs["uRC.sensor.PROPS.GET."+self.uRC_MODULE_NAME] = self.on_props_get
        self._rpcs["uRC.sensor.PROPS.SET."+self.uRC_MODULE_NAME] = self.on_props_set
   
    def _startupComponents(self):
        Autobahn_Client._startupComponents(self)
        
    def on_trigger(self, data):
        pass
    
    def on_status_get(self, data):
        pass
    
    def on_props_get(self, data):
        pass
    
    def on_props_set(self, data):
        pass
        
        
if __name__ == "__main__":
    reactor = install_reactor()
    logging.basicConfig(level=logging.INFO)
    Autobahn_Client.startup_client_2(Sensor_WebSocket)
    reactor.run()