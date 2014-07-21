'''
Created on 17.07.2014

@author: mend_ma
'''
import serial
import threading
import logging

TIME_SLICE = 0.001

BAUDRATE = 57600
DATABITS = 8
STOPBITS = 1
PARITY = "N"

LOGGER = logging.getLogger("SERIAL")

class SocketWrapper(serial.Serial):
    def __init__(self, port, baudrate=BAUDRATE, parity=PARITY, stopbits=STOPBITS):
        serial.Serial.__init__(self, port=port, baudrate=baudrate, parity=parity, stopbits=stopbits)
        
        self._receiveBuffer = []
        self._sendingBuffer = []
        
        self.__sendBufferLock = threading.Lock()      ## lock for handling the sendingbuffer
        self.__sendBufferNotifyer = threading.Event()      ## lock for handling the sendingbuffer
        
        self.__rcvBufferLock = threading.Lock()
        self.__rcvBufferNotifyer = threading.Event() 
        
        self.__serialLock = threading.Lock() 
        self.__serialNotifyer = threading.Event()
        
        self._connected = True
        
        self.startReceiving()
        self.startSending()
    
    #########################################################################
    ### Starting Threads
    #########################################################################
        
    def startReceiving(self):
        self.receiver = threading.Thread(target=self._readData)
        self.receiver.start()
    
    def startSending(self):
        self.sender = threading.Thread(target=self._sendData)
        self.sender.start() 
    
    #########################################################################
    ### External Controll
    #########################################################################
    
    def read_byte(self):
        self.__waitfor(self.__rcvBufferLock, self.__rcvBufferNotifyer)
        if len(self._receiveBuffer) > 0:
            byte = self._receiveBuffer.pop(0)
        else:
            byte = ""
        self.__release(self.__rcvBufferLock, self.__rcvBufferNotifyer)
        return byte
    
    def write_message(self, serial_string):
        if self._connected:
            self.__waitfor(self.__sendBufferLock, self.__sendBufferNotifyer)
            self._sendingBuffer.append(serial_string)
            self.__release(self.__sendBufferLock, self.__sendBufferNotifyer)
            LOGGER.debug("SENT: " + str(serial_string.encode("hex")))
            return True
        else:
            return False
        
    def flush(self, *args, **kwargs):
        self._receiveBuffer = []
        return serial.Serial.flush(self, *args, **kwargs)
        
    def close(self):
        self._connected = False
        serial.Serial.close(self)
    
    #########################################################################
    ### Receiving data (Threading)
    #########################################################################
           
    def _readData(self):
        ''' Reading data from the _serial port, interpretation data
        This function needs to be started in a thread''' 
        while self._connected:
            reading = None
            self.__waitfor(self.__serialLock, self.__serialNotifyer)
            try:
                reading = self.read(1)
            except Exception, e:
                LOGGER.error("Reading _serial-data: " + str(e))
                self.flush()
            self.__release(self.__serialLock, self.__serialNotifyer)
            
            self.__waitfor(self.__rcvBufferLock, self.__rcvBufferNotifyer)
            if reading is not None:
                self._receiveBuffer.append(reading)
            self.__release(self.__rcvBufferLock, self.__rcvBufferNotifyer)
        
    #########################################################################
    ### Sending data (Threading)
    #########################################################################
        
    def __sendNext(self):
        if len(self._sendingBuffer) > 0:
            buffered =  self._sendingBuffer.pop(0)
            serial_message = buffered
            self.write(serial_message)
            self.flush()
        
    def _sendData(self):
        while self._connected:
            self.__waitfor(self.__sendBufferLock, self.__sendBufferNotifyer)
            self.__sendNext()
            self.__release(self.__sendBufferLock, self.__sendBufferNotifyer)
            
    #########################################################################
    ### Managing connection
    #########################################################################
    
    def __waitfor(self, lock, notifyer):
        while not lock.acquire():
            notifyer.wait()
        notifyer.clear()
        
    def __release(self, lock, notifyer):
        notifyer.set()
        lock.release()
            
    def __del__(self):
        LOGGER.info("closing serial")
        self.close()