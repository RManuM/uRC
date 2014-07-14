'''
Created on 14.07.2014

@author: mend_ma
'''
from generic.python.websocket.Autobahn_Client import Autobahn_Client

class Autobahn_Socket_AscTec(Autobahn_Client):
    '''
    classdocs
    '''
    PARSER_FILE = "../config/definitions.xml"
    uRC_MODULE_NAME = "AscTec_Falcon"
    
    def _initSubscriptions(self):
        Autobahn_Client._initSubscriptions(self)
        
    def _initRpcs(self):
        Autobahn_Client._initRpcs(self)
        self._rpcs["uRC.sensor.TRIGGER."+self.uRC_MODULE_NAME] = self.handleRPC
        self._rpcs["uRC.sensor.STATUS.GET."+self.uRC_MODULE_NAME] = self.handleRPC
        self._rpcs["uRC.sensor.PROPS.GET."+self.uRC_MODULE_NAME] = self.handleRPC
        self._rpcs["uRC.sensor.PROPS.SET."+self.uRC_MODULE_NAME] = self.handleRPC
   
    def _startupComponents(self):
        Autobahn_Client._startupComponents(self)