'''
Created on 14.07.2014

@author: mend_ma
'''
from generic.python.websocket.Autobahn_Client import Autobahn_Client
import logging
from autobahn.wamp import types
from autobahn.twisted.choosereactor import install_reactor
from autobahn.twisted.wamp import ApplicationSessionFactory

class Sensor_WebSocket(Autobahn_Client):
    '''
    classdocs
    '''
    def __init__(self, config=types.ComponentConfig(u"anonymous")):
        PARSER_FILE = "../config/definitions.xml"
        uRC_MODULE_NAME = "AscTec_Falcon"
        Autobahn_Client.__init__(self, uRC_MODULE_NAME, PARSER_FILE, config=config)
    
    def _initSubscriptions(self):
        Autobahn_Client._initSubscriptions(self)
        
    def _initRpcs(self):
        Autobahn_Client._initRpcs(self)
        sID = str(self._session_id)
        self._rpcs["uRC.sensor.TRIGGER."+sID] = self.on_trigger
        self._rpcs["uRC.sensor.STATUS.GET."+sID] = self.on_status_get
        self._rpcs["uRC.sensor.PROPS.GET."+sID] = self.on_props_get
        self._rpcs["uRC.sensor.PROPS.SET."+sID] = self.on_props_set
   
    def _startupComponents(self):
        Autobahn_Client._startupComponents(self)
        self._falconInstance = self._falcon()
    
    def _falcon(self):
        if self.factory.falcon_handler:
            self.factory.falcon_handler.register_sensorSocket(self)
            return self.factory.falcon_handler
        else:
            self.LOGGER.error("no Falcon-Management-Class given!")
            return None
    
    def on_trigger(self, data):
        def fkt(data):
            if self._parser.parse("uRC.sensor.TRIGGER", data):
                return self._falcon().trigger()
            else:
                raise Exception("no valid data")
        return self._handle_RPC(fkt, data)
    
    def on_status_get(self, data):
        def fkt(data):
            if self._parser.parse("uRC.sensor.STATUS.GET", data):
                ## FIXME: pack return params to struct
                return self._falcon().getStatus()
            else:
                raise Exception("no valid data")
        return self._handle_RPC(fkt, data)
    
    def on_props_get(self, data):
        def fkt(data):
            if self._parser.parse("uRC.sensor.PROPS.GET", data):
                pitch, roll, yaw = self._falcon().getProps()
                return {"orientation":{"pitch":pitch, "roll":roll, "yaw":yaw}}
            else:
                raise Exception("no valid data")
        return self._handle_RPC(fkt, data)
    
    def on_props_set(self, data):
        def fkt(data):
            if self._parser.parse("uRC.sensor.PROPS.SET", data):
                if data.has_key("orientation"):
                    orientation = data["orientation"]
                    pitch, roll, yaw = orientation["pitch"],  orientation["roll"],  orientation["yaw"]
                    return self._falcon().setProps(pitch, roll, yaw)
                else:
                    raise Exception("this module requires orientation")
            else:
                raise Exception("no valid data")
        return self._handle_RPC(fkt, data)
        
    def em_trigger_complete(self):
        self.publish("uRC.sensor.TRIGGER.COMPLETED")
    
    def em_trigger_error(self, code, message):
        res = {"error_code":code, "error_message":message}
        self.publish("uRC.sensor.TRIGGER.ERROR", res)
    
    def em_props(self, pitch, roll, yaw):
        res =  {"orientation":{"pitch":pitch, "roll":roll, "yaw":yaw}}
        self.publish("uRC.sensor.PROPS", res)
    
    def em_status(self, triggering):
        ## TODO: this method is obviously missing
        pass
    
class Sensor_WebSocket_Factory(ApplicationSessionFactory):
    session = Sensor_WebSocket
    def __init__(self, falcon_handler):
        ApplicationSessionFactory.__init__(self)
        self.falcon_handler = falcon_handler
        
        
if __name__ == "__main__":
    reactor = install_reactor()
    logging.basicConfig(level=logging.INFO)
    Autobahn_Client.startup_client_2(Sensor_WebSocket)
    reactor.run()