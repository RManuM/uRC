'''
Created on 12.03.2014

@author: mend_ma
Extracted and adopted from Lucas Graeser -> Autopilot-Software utils.py
'''
import struct
import math
        

#CHAR    = "<b"
UCHAR   = "<B"
SHORT   = "<h"
USHORT  = "<H"
INT     = "<i"
UINT    = "<I"

IMURAW = '\x01'
LLSTATUS = '\x02'
IMUCALC = '\x03'
CAM = '\x63'
X60 = '\x60'
X61 = '\x61'
X62 = '\x62'
X64 = '\x64'
RCDAT = '\x15'
CTRLOUT = '\x11'
GPS = '\x23'
GPSADV = '\x29'
CURWAY = '\x21'
WPT = '\x24'
GOTO = '\x25'
LAUNCH = '\x26'
ENDFLIGHT = '\x27'
COMEHOME = '\x28'
POLL = 0
TRIGGER = 1
CAMDOWN = 2
CAMUP = 3

POLL_FAKTORS = {LLSTATUS:1, IMURAW:2, IMUCALC:4, GPS:128, GPSADV:512, CAM:2048, CURWAY:256}
ACK_MAP = {"0x24":"WPT", "0x25":"GOTO", "0x26":"LAUNCH", "0x27":"ENDFLIGHT", "0x28":"COMEHOME", "0x30":"CAM"}


################################################################################################################

class Command:
    """
    The Command class provides instances that transform L{Waypoint}s and command identifiers into
        hexadecimal byte structures according to the protocol given by the octocopter's producer I{AscTec}.
    """
    def __init__(self,cmdType,wpt=None):
        self.cmdType = cmdType
        self.wpt = wpt       
    
    @staticmethod
    def getCmd_poll(*list_of_poll_ids):
        cmdStruct = ">*>p"
        poll_id = 0
        for entry in list_of_poll_ids:
            if POLL_FAKTORS.has_key(entry):
                poll_id += POLL_FAKTORS[entry]
        cmdStruct += struct.pack(USHORT,poll_id)
        return cmdStruct
    
    @staticmethod
    def getCmd_setCam(pitch, roll):
        cmdStruct = ">*>d0"
        
        camstatus = 0x0100 #0x02: tilt compensation disabled (muss 0x0100 anstatt 0 sein seit HL-Firmware 2.24)
        camstatus = int(camstatus)
        desired_angle_pitch = int(pitch*1000)
        desired_angle_roll = int(roll*1000)
        checksum = (int("aaaa",16)+camstatus+desired_angle_pitch+desired_angle_roll)%65536
        
        camstatus   =           struct.pack(SHORT,camstatus)
        desired_angle_pitch   = struct.pack(INT,desired_angle_pitch)
        desired_angle_roll   =  struct.pack(INT,desired_angle_roll)
        checksum    =           struct.pack(USHORT,checksum)

        cmdStruct = cmdStruct+camstatus+checksum+desired_angle_pitch+desired_angle_roll
        return cmdStruct
    
    @staticmethod
    def getCmd_triggerCam():
        cmdStruct = ">*>t"
        return cmdStruct
    
    @staticmethod
    def getCmd_goto(maxSpeed,timeToStay,acc,lng,lat,heading,height):
        cmdStruct = ">*>wg"
        waypointStruct = Command._getWaypointStruct(maxSpeed,timeToStay,acc,lng,lat,heading,height,autoTrigger=False)
        return cmdStruct + waypointStruct
    
    @staticmethod
    def getCmd_launch():
        cmdStruct = ">*>wl"
        return cmdStruct
    
    @staticmethod
    def getCmd_endFlight():
        cmdStruct = ">*>we"
        return cmdStruct
    
    @staticmethod
    def getCmd_comeHome():
        cmdStruct = ">*>wh"
        return cmdStruct
            
    @staticmethod
    def getCmd_uploadTarget(maxSpeed,timeToStay,acc,lng,lat,heading,height,
                             autoTrigger=False): ## time in [s], distance in [m]koordinates in[degree]
        cmdStruct = ">*>ws"
        waypointStruct = Command._getWaypointStruct(maxSpeed,timeToStay,acc,lng,lat,heading,height,
                             autoTrigger)
        return cmdStruct + waypointStruct
    
    @staticmethod
    def _getWaypointStruct(maxSpeed,timeToStay,acc,lng,lat,heading,height,autoTrigger):
        wpnum       = 1
        if autoTrigger:
            flags   = int("0x37",0)
        else:
            flags   = int("0x17",0)
        maxSpeed    = maxSpeed*10
        time        = int(timeToStay*100)
        acc         = int(acc*1000)
        lng         = int(lng*10000000)
        lat         = int(lat*10000000)
        heading     = int(heading*1000)
        height      = int(height*1000)
        checksum    = (int("aaaa",16)+heading+height+time+lng+lat+maxSpeed+acc+flags+wpnum)%65536
        
        wpnum       = struct.pack(UCHAR,wpnum)
        dummy       = "\x00\x00\x00" ##struct.pack(UCHAR, dummy) ##"\x00\x00\x00"
        flags       = struct.pack(UCHAR,flags)
        maxSpeed    = struct.pack(UCHAR,maxSpeed)
        time        = struct.pack(USHORT,time)
        acc         = struct.pack(USHORT,acc)
        checksum    = struct.pack(USHORT,checksum)
        lng         = struct.pack(INT,lng)
        lat         = struct.pack(INT,lat)
        heading     = struct.pack(INT,heading)
        height      = struct.pack(INT,height)
        
        cmdStruct = wpnum+dummy+flags+maxSpeed+time+acc+checksum+lng+lat+heading+height
    
        return cmdStruct
    
    def getCmdStruct(self):
        """
        Returns a byte structure according to the Command type.
        @return: hexadecimal byte structure
        """
        ### this function should not be used, use the static ones instead
        if self.cmdType == GOTO:
            cmdID = ">*>wg"
        elif self.cmdType == LAUNCH:
            cmdID = ">*>wl"
        elif self.cmdType == ENDFLIGHT:
            cmdID = ">*>we"
        elif self.cmdType == COMEHOME:
            cmdID = ">*>wh"
        elif self.cmdType == WPT:
            cmdID = ">*>ws"
        elif self.cmdType == POLL:
            cmdID = ">*>p"
        elif self.cmdType == CAMDOWN:  
            cmdID = ">*>d0"
        elif self.cmdType == CAMUP:  
            cmdID = ">*>d0"
        elif self.cmdType == TRIGGER:
            cmdID = ">*>t"
            
        cmdStruct = cmdID
        
        if self.cmdType == POLL:
            flag = struct.pack(USHORT,389)
            cmdStruct = cmdStruct+flag
        elif self.cmdType == CAMDOWN:
            camstatus = 0x0100 #0x02: tilt compensation disabled (muss 0x0100 anstatt 0 sein seit HL-Firmware 2.24)
            camstatus = int(camstatus)
            desired_angle_pitch = 90000
            desired_angle_roll = 0
            checksum = (int("aaaa",16)+camstatus+desired_angle_pitch+desired_angle_roll)%65536
            
            camstatus   =           struct.pack(SHORT,camstatus)
            desired_angle_pitch   = struct.pack(INT,desired_angle_pitch)
            desired_angle_roll   =  struct.pack(INT,desired_angle_roll)
            checksum    =           struct.pack(SHORT,checksum)

            cmdStruct = cmdStruct+camstatus+checksum+desired_angle_pitch+desired_angle_roll
        
        elif self.cmdType == CAMUP:
            camstatus = 0x0100 #0x02: tilt compensation disabled (muss 0x0100 anstatt 0 sein seit HL-Firmware 2.24)
            camstatus = int(camstatus)
            desired_angle_pitch = 0
            desired_angle_roll = 0
            try:
                checksum = (int("aaaa",16)+camstatus+desired_angle_pitch+desired_angle_roll)%65536
            except:
            
                print "checksum-error:" + str(checksum)
            
            camstatus   =           struct.pack(SHORT,camstatus)
            desired_angle_pitch   = struct.pack(INT,desired_angle_pitch)
            desired_angle_roll   =  struct.pack(INT,desired_angle_roll)
            checksum    =           struct.pack(SHORT,checksum)

            cmdStruct = cmdStruct+camstatus+checksum+desired_angle_pitch+desired_angle_roll
        
        elif self.cmdType in [GOTO,LAUNCH,ENDFLIGHT,COMEHOME,WPT]:
            if self.wpt == None:
                raise "Before creating this cmdStruct you have to assign a Waypoint-object to attribute 'wpt'"
            wpnum       = 1
            flags       = int(self.wpt.flags)
            maxSpeed    = 100
            time        = int(self.wpt.time*100)
            acc         = int(self.wpt.acc*1000)
            lng         = int(self.wpt.lng*10000000)
            lat         = int(self.wpt.lat*10000000)
            heading     = int(self.wpt.heading*1000)
            height      = int(self.wpt.ele*1000)
            checksum    = (int("aaaa",16)+heading+height+time+lng+lat+maxSpeed+acc+flags+wpnum)%65536
            
            wpnum       = struct.pack(UCHAR,wpnum)
            dummy       = "\x00\x00\x00"
            flags       = struct.pack(UCHAR,flags)
            maxSpeed    = struct.pack(UCHAR,maxSpeed)
            time        = struct.pack(USHORT,time)
            acc         = struct.pack(USHORT,acc)
            checksum    = struct.pack(USHORT,checksum)
            lng         = struct.pack(INT,lng)
            lat         = struct.pack(INT,lat)
            heading     = struct.pack(INT,heading)
            height      = struct.pack(INT,height)
            
            cmdStruct = cmdStruct+wpnum+dummy+flags+maxSpeed+time+acc+checksum+lng+lat+heading+height
        
        return cmdStruct
    
#####################################################################################################################

class Message:
    """
    The Message class provides instances that transform received byte structures into parameters
        that can be processed according to the protocol given by the octocopter's producer I{AscTec}.
    """
    def __init__(self,byteString=None, data_dict=None):
        if byteString is not None:
            try:
                self.msgStruct,self.msgType = self.checkHeader(byteString)
            except Exception, e:
                raise Exception("Message-Error!", str(e))
        else:
            raise Exception("One of byte or dict must be set!")
            
    def checkHeader(self,byteString):
        """
        Checks header of the byte structure. Checks the crc16 checksum of the received Message.
        @param byteString: complete byte structure
        @type byteString: byte structure
        """
        if not (byteString[:3]==">*>"):
            #return False
            raise Exception("Incomplete Message!!!"+byteString)
        lengthOfStruct = struct.unpack(USHORT,byteString[3:5])[0]
        if not lengthOfStruct == len(byteString[6:-2]):
            #return False
            print "Length: "+str(lengthOfStruct)+"/"+str(len(byteString[6:-2]))
            raise Exception("Length of MsgStruct not correct!!!")
        msgStruct = byteString[6:-2]
        msgType = byteString[5:6]
        if not self.crc16(msgStruct)==byteString[-2:]:
            #return False
            raise Exception("CRC16 not correct!!!") 
            
        return msgStruct,msgType
    
    def getParams(self):
        """
        Returns the parameters according to the Message type.
        @return: possible:
            - float heading, float height (type: C{IMUCALC})
            - float batt1Volt, float batt2Volt, float motorsOnTime (type: C{LLSTATUS})
            - float lat, float lng (type: C{GPS})
            - float dist, bool wptReached (type: C{CURWAY})
        """
        result = dict()
        if self.msgType == IMUCALC:
            result["heading"]     = float(struct.unpack(INT,self.msgStruct[-32:-28])[0])/1000
            result["height"]      = float(struct.unpack(INT,self.msgStruct[-16:-12])[0])/1000
            
        elif self.msgType == LLSTATUS:
            batt1Volt   = float(struct.unpack(SHORT,self.msgStruct[:2])[0])/1000
            batt2Volt   = float(struct.unpack(SHORT,self.msgStruct[2:4])[0])/1000
            flying      = self.msgStruct[11]
            motorsOnTime   = float(struct.unpack(SHORT,self.msgStruct[-2:])[0])
            result = {"battery_voltage_1":batt1Volt, "battery_voltage_2":batt2Volt, 
                    "flying":flying, "motors_on":motorsOnTime}
            
        elif self.msgType == GPS:
            result["latitude"]          = float(struct.unpack(INT,self.msgStruct[:4])[0])/10000000
            result["longitude"]         = float(struct.unpack(INT,self.msgStruct[4:8])[0])/10000000 
            result["height"]            = float(struct.unpack(INT,self.msgStruct[8:12])[0])/1000 #in m
            result["speed_x"]           = float(struct.unpack(INT,self.msgStruct[12:16])[0])/1000 #in m/s
            result["speed_y"]           = float(struct.unpack(INT,self.msgStruct[16:20])[0])/1000 #in m/s
            result["heading"]               = float(struct.unpack(INT,self.msgStruct[20:24])[0])/1000 #in deg
            result["horizontal_accuracy"]   = float(struct.unpack(UINT,self.msgStruct[24:28])[0])/1000 #in m
            result["vertical_accuracy"]     = float(struct.unpack(UINT,self.msgStruct[28:32])[0])/1000 #in m
        
        elif self.msgType == CURWAY:
            dist        = float(struct.unpack(USHORT,self.msgStruct[-2:])[0])/10
            wptReached  = (True if struct.unpack(USHORT,self.msgStruct[-4:-2])[0]==7 else False)
            result = {"distance":dist, "wptReached":wptReached}

        elif self.msgType == CAM:
            #print self.msgStruct.encode("hex")
            camangle        = float(struct.unpack(SHORT,self.msgStruct[8:10])[0])/100 
            rollAngle       = None #float(struct.unpack(SHORT,self.msgStruct[10:12])[0])/100 
            #if struct.unpack(INT,self.msgStruct[0:4])[0]==0: ### an dieser Stelle wird urberprueft, ob es sich um eine normale message handelt, oder so eine sondermessage bei der kein camangle enthalten ist.
            if not (abs(camangle) >= 200.0): ## excluding packages containing non-relevant information
                result =  {"pitch":camangle, "roll":rollAngle}#camangle
            
        elif self.msgType == X60: # Link-Quality
            rxL = self.msgStruct[0]
            rxR = self.msgStruct[1]
            txNackL = self.msgStruct[2]
            txNackR = self.msgStruct[3]
            txAckL = self.msgStruct[4]
            txAckR = self.msgStruct[5]
            rssiInvL = ord(self.msgStruct[6])
            rssiInvR = ord(self.msgStruct[7])#int(self.msgStruct[7])
            if rssiInvL < rssiInvR:
                rssiInv = rssiInvL
            else:
                rssiInv = rssiInvR
            rssi = (100 - float(rssiInv))/64
            rssisin = math.sin(math.pi/2*rssi)*100
            
            result = {"rxL":rxL,"rxR":rxR,"txNackL":txNackL,
                      "txNackR":txNackR,"txAckL":txAckL,"txAckR":txAckR, "rssisin":rssisin}
            
        elif self.msgType == X61:
            pass
            
        elif self.msgType == X62:
            flyTime_and_unknown_bits = int(struct.unpack(SHORT,self.msgStruct[0:2])[0])
            #print "Flugzeit:" + str(float(flyTime_and_unknown_bits)/60)
            result = {"flyTime_and_unknown_bits":flyTime_and_unknown_bits}
            
        elif self.msgType == X64:
            pass
        
        #print self.msgType.encode("hex"), ":", self.msgStruct.encode("hex")
        
        return result
    
    def crc16(self,byteString):
        """
        Calculates the crc16 checksum of the received Message.
        @param byteString: complete byte structure
        @type byteString: byte structure
        @return: int crc16 value
        """
        crc = int('ff',16)
        for data in byteString:
            data = ord(data)
            data ^= (crc & int('ff',16))
            data ^= (data<<4)%256
            crc = ((data<<8)%65536 | ((crc>>8)&int('ff',16)))^((data>>4)%256)^((data<<3)%65536)
        return struct.pack(USHORT,crc)
    
    
ackSlots = [False,False,False,False,False,False,False,
False,False,False,False,False,False,False,False,False,False,
False,False,False,False,False,False,False,False,False,False,False,
False,False,False,False,False,False,False,False,False,
False,False,False,False,False] 
##acknowledge-slots for WPT-, GOTO-, LAUNCH-, ENDFLIGHT-, COMEHOME-,
## ???, ???, ???, ???,???,???,???,CamDown-cmds, ...,CamUp-cmds
    