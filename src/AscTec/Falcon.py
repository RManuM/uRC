'''
Created on 16.07.2014

@author: mend_ma
'''
from AscTec.Serial_Socket import Serial_Socket
from AscTec.Serial_Protocol import Command
from AscTec.Serial_Protocol import CAM, LLSTATUS, IMUCALC, GPS, GPSADV, IMURAW, RCDAT, CTRLOUT, CURWAY, X60, X61, X62, X64


import logging
from autobahn.twisted.choosereactor import install_reactor
from generic.python.websocket.Autobahn_Client import Autobahn_Client

COMPORT = 3

class Falcon(object):
    '''
    classdocs
    '''
    
    __instance = None
    
    @staticmethod
    def instance():
        if Falcon.__instance is None:
            Falcon.__instance = Falcon()
        return Falcon.__instance
    
    def __init__(self):
        '''
        Constructor
        '''
        self._serial_socket = Serial_Socket(self)
        self._sensor_websocket = None
        
        ## properties
        self._cam_props = {"pitch":0, "roll":0, "yaw":0}
        self._cam_status = {"triggering":False}
        
        self._ready = False
        
        self.LOGGER = logging.getLogger("Falcon-Data-Handler")
        
    def connectUAV(self, port):
        if self._sensor_websocket is not None:
            try:
                self._serial_socket.connectDrone(port)
            except:
                self.setReady(False)
                self.LOGGER.error("no serialsocket available on port {}".format(port))
            else:
                self.setReady(True)
        else:
            self.LOGGER.error("No Sensor-Websocket registered")
            
    def setReady(self, ready):
        print "setting ready: {}".format(ready)
        self._ready = ready
        
    def ready(self):
        return self._ready
        
    def register_sensorSocket(self, socket):
        self._sensor_websocket = socket
        self.connectUAV(COMPORT)
        
    ####################################### SLOTS for requests from Websocket (Camera)
    
    def trigger(self):
        if self.ready():
            cmd = Command.getCmd_triggerCam()
            self._serial_socket.writeData(cmd)
            return True ## TODO: ack when ack from drone? or when send? BUT ACK!
        else:
            print "TRIGGER <<fallback>>"
            return True
        
    def getStatus(self):
        if self.ready():
            pass
            ## TODO: actually implement fkt
        else:
            print "GET_STATUS <<fallback>>"
    
    def getProps(self):
        if self.ready():
            pass ## Nothing to do here, because values are getting polled from the UAV
        else:
            print "GET_PROPS <<fallback>>"
        pitch, roll, yaw =  self._cam_props["pitch"], self._cam_props["roll"], self._cam_props["yaw"]
        return pitch, roll, yaw
    
    def setProps(self, pitch, roll, yaw):
        if self.ready():
            cmd = Command.getCmd_setCam(pitch, roll)
            self._serial_socket.writeData(cmd)
            return True ## TODO: ack when ack from drone? or when send? BUT ACK!
        else:
            self._cam_props["pitch"], self._cam_props["roll"], self._cam_props["yaw"] = pitch, roll, yaw
            pitch, roll, yaw = self.getProps()
            self._sensor_websocket.em_props(pitch, roll, yaw)
            print "SET_PROPS <<fallback>>"
            return True
        
    ####################################### Handling answers from Serialsocket
        
        
    def handle_ack(self, ackType):
        print "ack rcv"
        
    def handle_data(self, msgType, msg):
        if msgType == LLSTATUS:
            typeName = "LLSTATUS"
        elif msgType == CAM:
            typeName = "CAM"
            pitch, roll, yaw = msg["pitch"], msg["roll"], 0.0
            self._cam_props["pitch"] = pitch
            self._cam_props["roll"] = roll
            self._cam_props["yaw"] = yaw
            self._sensor_websocket.em_props(pitch, roll, yaw)
        elif msgType == GPS:
            typeName = "GPS"
        elif msgType == GPSADV:
            typeName = "GPSADV"
        elif msgType == IMUCALC:
            typeName = "IMUCALC"
        elif msgType == RCDAT:
            typeName = "RCDAT"
        elif msgType == IMURAW:
            typeName = "IMURAW"
        elif msgType == CTRLOUT:
            typeName = "CTRLOUT"
        elif msgType == CURWAY:
            typeName = "CURWAY"
        elif msgType == X60:
            typeName = "X60"
        elif msgType == X61:
            typeName = "X61"
        elif msgType == X62:
            typeName = "X62"
        elif msgType == X64:
            typeName = "X64"
        else:
            typeName = "OTHER"
            
        self.LOGGER.debug("handled msg-type: " + str(typeName))
        
        
if __name__ == "__main__":
    reactor = install_reactor()
    logging.basicConfig(level=logging.INFO)
    falcon = Falcon.instance()
    
    from AscTec.Sensor_WebSocket import Sensor_WebSocket
    Autobahn_Client.startup_client_2(Sensor_WebSocket)
    
    reactor.run()