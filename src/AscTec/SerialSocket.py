'''
Created on 02.07.2014

@author: mend_ma
'''

import serial
import traceback
import threading
from AscTec.Protocol import Message, Command, ACK_MAP
from AscTec.Protocol import CAM, LLSTATUS, IMUCALC, GPS, GPSADV, IMURAW, RCDAT, CTRLOUT, CURWAY, X60, X61, X62, X64
import time
import logging

LOGGER = logging.getLogger("falcon_serial_socket")

BAUDRATE = 57600
DATABITS = 8
STOPBITS = 1
PARITY = "N"

## TODO: make values setable via remote-call
COMPORT = 5
POLL_INTERVALL = 1.5
SENDING_INTERVALL = 0.3
READING_PAUSE = 0.01

class SerialSocket(object):
    '''   This class offers a serial socket and pulls data from the drone   '''
    serial = None
    
    def __init__(self, payload_socket, uav_socket, *args, **argv):
        ## initializing serial data
        self.__baud = BAUDRATE
        self.__comport = COMPORT
        self.__databits = DATABITS
        self.__stopbits = STOPBITS
        self.__parity = PARITY
        
        self.__sendingIntervall = SENDING_INTERVALL
        self.__pollIntervall = POLL_INTERVALL
        
        ## internal state
        self.__onMission = False
        self.connected = False                  ## is the drone connected?
        self.uav_socket = uav_socket            ##  the abstract UAV to emit signals
        self.payload_socket = payload_socket    ##  the abstract UAV to emit signals
        
        self.__sendLock = threading.Lock()      ## lock for handling the sendingbuffer
        self.writeBuffer = list()
    
    ##########################################################################################
    ## Connection handling
    ##########################################################################################
    
    def connectDrone(self, port, autopublish=None, sending_intervall=None, poll_intervall=None):
        ''' Trys to connect a drone to the serial port specified by this class'''
        
        if autopublish is not None:
            self.__autopublish = autopublish
        if sending_intervall is not None:
            self.__sendingIntervall =  sending_intervall
        if poll_intervall is not None:
            self.__pollIntervall =  poll_intervall
            
        error, message = 0, ""
        self.__comport = port
        if not self.connected:
            try:
                ## connect serial
                self.serial = serial.Serial(port=self.__comport,
                                         baudrate=self.__baud,
                                         parity=self.__parity,
                                         stopbits=self.__stopbits,
                                         bytesize=self.__databits)
            except Exception, e:
                LOGGER.error(str(e))
                error = 1
                message = str(e)
        else:
            error = 801
            message = "already connected"
        if not error == 0:
            return {"error_code":error, "error_description":message}
        else:
            self.connected = True
            self.startReceiving()
            self.startSending()
            self.startPolling()
            return {}
    
    def disconnectDrone(self):
        if self.connected:
            try:
                self.connected = False
                if self.serial is not None:
                    self.serial.close()
                    self.serial = None 
            except Exception, e: 
                traceback.print_exc()
                return {"error_code":1, "error_description":str(e)}
        return {}
    
    def startReceiving(self):
        self.receiver = threading.Thread(target=self._readData)
        self.receiver.start()
    
    def startPolling(self):
        self.poller = threading.Thread(target=self._pollData)
        self.poller.start()
    
    def startSending(self):
        self.sender = threading.Thread(target=self._sendData)
        self.sender.start()
        
    def _onConnectionClosed(self):
        ''' Handling a closed connection (expected or unexpected)'''
        self.disconnectDrone()
        self.abstractUAV.em_UAV_CONNECTION_CLOSED()
    
    ##########################################################################################
    ## Reading data (THREAD)
    ##########################################################################################
    
    def _readData(self):
        ''' Reading data from the serial port, interpretation data
        This function needs to be started in a thread''' 
        while self.connected:
            try:
                reading = self.__readLine()
                if reading is not None:
                    msg, msgType = reading
                    if msgType == "MSG":
                        self.__handleData(msg)
                    elif msgType == "ACK":
                        key = "0x"+msg.encode("hex")
                        if ACK_MAP.has_key(key):
                            ackType = ACK_MAP[key]
                        else:
                            ackType = None
                        self.__handleAck(ackType)
                        LOGGER.debug("received: " + ackType + " " + key)
            except Exception, e:
                LOGGER.error("Reading serial-data: " + str(e))
                self.serial.flush()
            time.sleep(READING_PAUSE)
           
        if self.connected == False:
            self._onConnectionClosed()
            
    def __readLine(self):
        result = None
        reading = ""
        while result == None and self.connected:
            try:
                reading += self.serial.read(1)
            except AttributeError, e:
                print str(e)
                break
            if reading[:3] == ">*>" and reading[-3:] == "<#<":
                result = reading[:-3], "MSG"
            elif reading[:2] == ">a" and reading[-2:] == "a<":
                reading = reading[2:-2]
                result = reading, "ACK"
        if self.connected:
            return result
        else:
            return None
        
    def __handleAck(self, ackType):
        if ackType is not None:
            LOGGER.debug("ACK: " + ackType)
            self.payload_socket.handle_ack(ackType)
            self.uav_socket.handle_ack(ackType)
        
    def __handleData(self, reading):
        data_msg = Message(reading)
        msgType = data_msg.msgType
        if msgType == LLSTATUS:
            typeName = "LLSTATUS"
        elif msgType == CAM:
            typeName = "CAM"
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
        
        data = data_msg.msgStruct
        LOGGER.debug("RECEIVED (" + str(typeName) + ")  :" + str(data.encode("hex")))
        
        self.payload_socket.handle_data(data_msg)
        self.uav_socket.handle_data(data_msg)
    
    ##########################################################################################
    ## writing data to serial bus (THREAD)
    ##########################################################################################
    
    def writeData(self, serial_message):
        if self.connected:
            while not self.__sendLock.acquire():
                time.sleep(self.__sendingIntervall/100)
            LOGGER.debug("SENT: " + str(serial_message[3:].encode("hex")))
            self.writeBuffer.append(serial_message)
            self.__sendLock.release()
            return True
        else:
            return False
        
    def __sendNext(self):
        if len(self.writeBuffer) > 0:
            buffered =  self.writeBuffer.pop(0)
            serial_message = buffered
            self.serial.write(serial_message)
        
    def _sendData(self):
        while self.connected:
            while not self.__sendLock.acquire():
                time.sleep(self.__sendingIntervall/10)
            self.__sendNext()
            self.__sendLock.release()
            time.sleep(SENDING_INTERVALL)
        
    
    ##########################################################################################
    ## polling data (THREAD)
    ##########################################################################################
    
    def _pollData(self):
        while self.connected:
            self.writeData(Command.getCmd_poll(LLSTATUS, IMUCALC, GPSADV, CAM))
            if self.__onMission:
                self.writeData(Command.getCmd_poll(CURWAY))
            time.sleep(self.__pollIntervall)
#             
#             
#             
#     ##########################################################################################
#     ## PAYLOAD
#     ##########################################################################################
#     
#     def setCamAngle(self, pitch, roll, request):
#         LOGGER.info("Setting angle to (pitch/roll): (" + str(pitch) + "/" + str(roll) + ")")
#         key = "CAM"
#         if not self.__pending_acks.has_key(key):
#             self.__pending_acks[key] = request
#             self.writeData(Command.getCmd_setCam(pitch, roll))
#         else:
#             self.payload_socket.ack_error(request, 1, "waiting for cam to execute")
#         self.writeData(Command.getCmd_poll())
#         
#     def getCamAngle(self):
#         pitch = self.drone_cam["pitch"]
#         roll = self.drone_cam["roll"]
#         return pitch, roll
#     
#     def trigger(self, request):
#         message = Command.getCmd_triggerCam()
#         LOGGER.info("Triggering CAM")
#         self.writeData(message, request)
#         
#             
#     ##########################################################################################
#     ## UAV
#     ##########################################################################################
#     
#     ## status
#     def getStatus(self):
#         ## FIXME: this status is more experimental. for real status specification take your time
#         if self.drone_status["battery_voltage_1"] is not None and self.drone_status["battery_voltage_2"] is not None:
#             baLevel = float(self.drone_status["battery_voltage_1"]) + float(self.drone_status["battery_voltage_2"])
#             baLevel = baLevel /2
#             return {"mode":self.drone_status["flightMode"], "batteryLevel":baLevel, 
#                     "timeUp":self.drone_status["up_time"]}
#         else:
#             return None
#         
#     ## position
#     def getPosition(self):
#         """
#             Returns: lat, lon, height, yaw
#         """
#         return self.drone_gpsData["latitude"], self.drone_gpsData["longitude"], self.drone_gpsData["height"], self.drone_gpsData["heading"]
#         
#     ## targeting
#     def setTarget(self, target, request):
#         self._target = target
#         ## setting cam
#         pitch = float(request.get("body","cam", "pitch"))
#         roll = float(request.get("body","cam", "roll"))
#         self.setCamAngle(pitch, roll, request)
#         
#         ## setting waypoint FIXME: setting some values not statically
#         LOGGER.info("Setting target.")
#         maxSpeed= 10 ## in m/s
#         timeToStay=1 ## in s
#         acc=2 ## in m
#         lng=float(target["lon"])
#         lat=float(target["lat"])
#         heading=float(target["heading"])
#         height=float(target["alt"])
#         flags = str(request.get("body", "cam", "trigger")).lower() == "true"
#         command = Command.getCmd_uploadTarget(maxSpeed, timeToStay, acc, lng, lat, heading, height, flags)
#         self.writeData(command)
#         key = "WPT"
#         if not self.__pending_acks.has_key(key):
#             self.__pending_acks[key] = request
#         self.__onMission = True
#                 
#     def getTarget(self):
#         return self._target
#     
#     ## Flight control!
#     def launch(self, target, request):
#         """ Setting the current home-position"""
#         command = Command.getCmd_endFlight()
#         self.writeData(command)
#         key = "LAUNCH"
#         if not self.__pending_acks.has_key(key):
#             self.__pending_acks[key] = request
#         self.__onMission = True
#         LOGGER.info(key)
#         
#     def endFlight(self, request):
#         """ ends a flight"""
#         command = Command.getCmd_endFlight()
#         self.writeData(command)
#         key = "ENDFLIGHT"
#         if not self.__pending_acks.has_key(key):
#             self.__pending_acks[key] = request
#         self.__onMission = True
#         LOGGER.info(key)
#     
#     def comeHome(self, request):
#         """flies to the current home-position"""
#         command = Command.getCmd_endFlight()
#         self.writeData(command)
#         key = "COMEHOME"
#         if not self.__pending_acks.has_key(key):
#             self.__pending_acks[key] = request
#         self.__onMission = True
#         LOGGER.info(key)
#     
#     def goto(self, target, request):
#         """keeping the target but moving to a different point for resuming"""
#         command = Command.getCmd_endFlight()
#         self.writeData(command)
#         key = "GOTO"
#         if not self.__pending_acks.has_key(key):
#             self.__pending_acks[key] = request
#         self.__onMission = True
#         LOGGER.info(key)
#             
#     def checkWaypointReached(self, data):
#         """ Checks, whether a waypoint is reached and executed till the end"""
#         wptReached = data["wptReached"]
#         if wptReached:
#             LOGGER.info("Waypoint reached")
#             self.abstractUAV.em_UAV_SI_TARGET_REACHED()
#             self.__onMission = False
#             self._target = None
#         else:
#             LOGGER.info("Distance to waypoint: " + str(data["distance"]))