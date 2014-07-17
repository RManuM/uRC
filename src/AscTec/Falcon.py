'''
Created on 16.07.2014

@author: mend_ma
'''
from AscTec.Serial_Protocol import Command, ACK_MAP, Message
from AscTec.Serial_Protocol import CAM, LLSTATUS, IMUCALC, GPS, GPSADV, IMURAW, RCDAT, CTRLOUT, CURWAY, X60, X61, X62, X64

import logging
from autobahn.twisted.choosereactor import install_reactor
from generic.python.serial.SocketWrapper import SocketWrapper
from autobahn.twisted.websocket import WampWebSocketClientFactory
from twisted.internet.endpoints import clientFromString

COMPORT = 0

class Serialhandler(object):
    '''
    classdocs
    '''
    
    def __init__(self, comport):
        '''
        Constructor
        '''
        self.LOGGER = logging.getLogger("Falcon-Data-Handler")
        try:
            self._serial = SocketWrapper(comport)
        except:
            self._serial = None
            self.LOGGER.error("serial could not be connected")
            
        self._sensor_websocket = None
        
        ## properties
        self._cam_props = {"pitch":0, "roll":0, "yaw":0}
        self._cam_status = {"triggering":False}
        
        self._ready = False
        
        self.LOGGER.info("Datahandler started")
            
    def setReady(self, ready):
        self._ready = ready
        
    def ready(self):
        return self._ready
        
    def register_sensorSocket(self, socket):
        self._sensor_websocket = socket
        if self._serial is not None:
            self.setReady(True)
        
    ####################################### SLOTS for requests from Websocket (Camera)
    
    def trigger(self):
        if self.ready():
            cmd = Command.getCmd_triggerCam()
            self._serial.write_message(cmd.get_binary())
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
            self._serial.write_message(cmd.get_binary())
            return True ## TODO: ack when ack from drone? or when send? BUT ACK!
        else:
            self._cam_props["pitch"], self._cam_props["roll"], self._cam_props["yaw"] = pitch, roll, yaw
            pitch, roll, yaw = self.getProps()
            self._sensor_websocket.em_props(pitch, roll, yaw)
            print "SET_PROPS <<fallback>>"
            return True
        
    ####################################### Handling answers from Serialsocket
      
    def _readData(self):
        ''' Reading data from the _serial port, interpretation data
        This function needs to be started in a thread''' 
        while self._connected:
            reading = self._readLine()
            if reading is not None:
                msg, msgType = reading
                if msgType == "MSG":
                    self.handle_data(Message(msg))
                elif msgType == "ACK":
                    key = "0x"+msg.encode("hex")
                    if ACK_MAP.has_key(key):
                        ackType = ACK_MAP[key]
                    else:
                        ackType = None
                    self.handle_ack(ackType)
            
    def _readLine(self):
        result = None
        reading = ""
        while result == None:
            try:
                reading += self._serial.read(1)
            except AttributeError, e:
                print str(e)
                break
            if reading[:3] == ">*>" and reading[-3:] == "<#<":
                result = reading[:-3], "MSG"
            elif reading[:2] == ">a" and reading[-2:] == "a<":
                reading = reading[2:-2]
                result = reading, "ACK"
        return result
        
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
    server_url="ws://localhost:8080/ws"
    server_bindings="tcp:localhost:8080"
    
    ## starting up falcon socket!
    from AscTec.Sensor_WebSocket import Sensor_WebSocket_Factory
    falcon = Serialhandler(COMPORT)
    sensor_session = Sensor_WebSocket_Factory(falcon)
    transport_factory = WampWebSocketClientFactory(sensor_session, server_url)
    client = clientFromString(reactor, server_bindings)
    client.connect(transport_factory)
    
    reactor.run()