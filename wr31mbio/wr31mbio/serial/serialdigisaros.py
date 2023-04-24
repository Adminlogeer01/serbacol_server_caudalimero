#!/usr/bin/env python
# Python Serial Port Extension for Win32, Linux, BSD, Jython
# module for serial IO for POSIX compatible systems, like Linux
# see __init__.py
#
# (C) 2001-2008 Chris Liechti <cliechti@gmx.net>
# this is distributed under a free software license, see license.txt
#
# parts based on code from Grant B. Edwards  <grante@visi.com>:
#  ftp://ftp.visi.com/users/grante/python/PosixSerial.py
# references: http://www.easysw.com/~mike/serial/serial.html


import sys, os, struct, select, errno, telnetlib, time
from serialutil import *

def device(port):
    return 'ASY/0%d' % port

class Serial(SerialBase):
    """Serial port class implementation for SarOS. Serial port configuration 
    is done through RCI querys. It runs on Digi SarOS devices."""

    PROMPT_USERNAME = "Username:"
    PROMPT_PASSWORD = "Password:"
    END_LINE = "\r\n"
    
    AT_BAUD_RATES = {"Autobaud" :"0", 
                     460800     :"1",
                     230400     :"2",
                     115200     :"3",
                     57600      :"4",
                     38400      :"5",
                     19200      :"6",
                     9600       :"7",
                     4800       :"8",
                     2400       :"9",
                     1200       :"10",
                     600        :"11",
                     300        :"12",
                     }
    AT_BYTESIZES = (SEVENBITS, EIGHTBITS)
    AT_PARITIES = (PARITY_NONE, PARITY_EVEN, PARITY_ODD)
    
    AT_CMD_SELECT_PORT      = "AT\PORT="
    AT_CMD_CONFIG_BAUDRATE  = "ATS31="
    AT_CMD_CONFIG_FLOW      = "AT&K"
    AT_CMD_CONFIG_BYTES     = "ATS23="
    AT_CMD_SAVE_CONFIG      = "AT&W"

    def __init__(self,
                 port = None,           # number of device, numbering starts at
                                        # zero. if everything fails, the user
                                        # can specify a device string, note
                                        # that this isn't portable anymore
                                        # port will be opened if one is specified
                 baudrate=9600,         # baud rate
                 bytesize=EIGHTBITS,    # number of data bits
                 parity=PARITY_NONE,    # enable parity checking
                 stopbits=STOPBITS_ONE, # number of stop bits
                 timeout=None,          # set a timeout value, None to wait forever
                 xonxoff=False,         # enable software flow control
                 rtscts=False,          # enable RTS/CTS flow control
                 writeTimeout=None,     # set a timeout for writes
                 dsrdtr=False,          # None: use rtscts setting, dsrdtr override if True or False
                 interCharTimeout=None, # Inter-character timeout, None to disable
                 username="username",   # the username of the Telnet session
                 password="password"    # the password to configure the Telnet session
                 ):
        self.username = username
        self.password = password
        super(Serial, self).__init__(port, baudrate, bytesize, parity, 
                                     stopbits, timeout, xonxoff, rtscts, 
                                     writeTimeout, dsrdtr, interCharTimeout)

    def open(self):
        """Open port with current settings. This may throw a SerialException
           if the port cannot be opened."""
        if self._port is None:
            raise SerialException("Port must be configured before it can be used.")
        self.fd = None
        self.mout = 0
        #open
        try:
            self.fd = open(self.portstr, "rw")
        except Exception, msg:
            self.fd = None
            raise SerialException("Could not open port %s: %s" % (self.makeDeviceName(self._port), msg))
        
        try:
            self._reconfigurePort()
        except:
            self.fd.close()
            self.fd = None
        else:
            self._isOpen = True
        
    def _reconfigurePort(self):
        """Set communication parameters on opened port."""
        if self.fd is None:
            raise SerialException("Can only operate on a valid port handle")
        
        # Open a Telnet session to configure the serial port.
        try:
            telnet_session = telnetlib.Telnet("127.0.0.1", 23)
        except Exception, msg:
            raise SerialException("Could not configure port: %s" %msg)
        
        # Check if the Telnet server needs authentication.
        data = telnet_session.read_until(self.PROMPT_USERNAME, 2)
        if data.find(self.PROMPT_USERNAME) != -1:
            telnet_session.write(self.username + self.END_LINE)
            data += telnet_session.read_until(self.PROMPT_PASSWORD, 2)
            telnet_session.write(self.password + self.END_LINE)
        
        # Configure the serial port sending AT parameters.
        # Select the serial port to configure.
        telnet_session.write(self.AT_CMD_SELECT_PORT + 
                             str(self.getPort()) + 
                             self.END_LINE)
        time.sleep(0.1)
        # Configure the baud rate.
        telnet_session.write(self.AT_CMD_CONFIG_BAUDRATE + 
                             str(self._getBaudRate(self.baudrate)) + 
                             self.END_LINE)
        time.sleep(0.1)
        # Configure the flow control.
        telnet_session.write(self.AT_CMD_CONFIG_FLOW + 
                             str(self._getFlowControl(self.rtscts, 
                                                      self.xonxoff)) + 
                             self.END_LINE)
        time.sleep(0.1)
        # Configure the data bits and parity.
        telnet_session.write(self.AT_CMD_CONFIG_BYTES + 
                             str(self._getBitsAndParity(self.bytesize, 
                                                        self.parity)) + 
                             self.END_LINE)
        time.sleep(0.1)
        # Save the configuration.
        telnet_session.write(self.AT_CMD_SAVE_CONFIG + 
                             self.END_LINE)
        time.sleep(0.1)
        
        telnet_session.close()

    def _getBaudRate(self, baudrate):
        """Return the value corresponding to the baud rate:
            0  = Autobaud
            1  = 460800
            2  = 230400
            3  = 115200
            4  = 57600
            5  = 38400
            6  = 19200
            7  = 9600
            8  = 4800
            9  = 2400
            10 = 1200
            11 = 600
            12 = 300"""
        if baudrate in self.AT_BAUD_RATES:
            return self.AT_BAUD_RATES[baudrate]
        else:
            return self.AT_BAUD_RATES[9600]

    def _getFlowControl(self, rtscts, xonxoff):
        """Return the value to configure the flow control:
            0=No flow control
            1=Hardware flow control
            2=Software flow control
            3=Use both"""
        if rtscts and xonxoff:
            return 3
        elif xonxoff:
            return 2
        elif rtscts:
            return 1
        else:
            return 0

    def _getBitsAndParity(self, bytesize, parity):
        """Return the value corresponding to the number of bits and parity:
            0=8,N
            1=7,O
            2=7,E
            3 not used
            4 not used
            5=8,O
            6=8,E"""
        if (not bytesize in self.AT_BYTESIZES or 
            not parity in self.AT_PARITIES):
            # Return the standard configuration: 8,N
            return 0
        
        if bytesize == EIGHTBITS:
            if parity == PARITY_NONE:
                return 0
            elif parity == PARITY_EVEN:
                return 6
            elif parity == PARITY_ODD:
                return 5
            else:
                return 0
        elif bytesize == SEVENBITS:
            if parity == PARITY_EVEN:
                return 2
            elif parity == PARITY_ODD:
                return 1
            else:
                return 2
        else:
            return 0

    def close(self):
        """Close port"""
        if self._isOpen:
            if self.fd is not None:
                close(self.fd)
                self.fd = None
            self._isOpen = False

    def makeDeviceName(self, port):
        return device(port)

    #  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -

    def inWaiting(self):
        """returns the number of bytes waiting to be read"""
        raise NotImplementedError  

    def read(self, size=1):
        """Read size bytes from the serial port. If a timeout is set it may
           return less characters as requested. With no timeout it will block
           until the requested number of bytes is read."""
        if self.fd is None: 
            raise portNotOpenError
        
        read = ''
        if size > 0:
            while len(read) < size:
                #print "\tread(): size",size, "have", len(read)    #debug
                ready,_,_ = select.select([self.fd],[],[], self._timeout)
                if not ready:
                    break   #timeout
                buf = self.fd.read(size-len(read))
                read += buf
                if (self._timeout >= 0 or self._interCharTimeout > 0) and not buf:
                    break  #early abort on timeout
        return read

    def write(self, data):
        """Output the given string over the serial port."""
        if self.fd is None: 
            raise portNotOpenError
        if not isinstance(data, str):
            raise TypeError('expected str, got %s' % type(data))
        
        try:
            if self._writeTimeout is not None and self._writeTimeout > 0:
                _,ready,_ = select.select([],[self.fd],[], self._writeTimeout)
                if not ready:
                    raise writeTimeoutError
            self.fd.write(data)
            self.fd.flush()
        except OSError,v:
            if v.errno != errno.EAGAIN:
                raise

    def flush(self):
        """Flush of file like objects. In this case, wait until all data
           is written."""
        # Not implemented on this platform
        raise NotImplementedError  

    def flushInput(self):
        """Clear input buffer, discarding all that is in the buffer."""
        # Not implemented on this platform
        pass    
        #raise NotImplementedError  

    def flushOutput(self):
        """Clear output buffer, aborting the current output and
        discarding all that is in the buffer."""
        # Not implemented on this platform
        pass
        #raise NotImplementedError  

    def sendBreak(self, duration=0.25):
        """Send break condition. Timed, returns to idle state after given duration."""
        # Not implemented on this platform
        raise NotImplementedError  

    def setBreak(self, level=1):
        """Set break: Controls TXD. When active, to transmitting is possible."""
        # Not implemented on this platform
        raise NotImplementedError  

    def setRTS(self, level=1):
        """Set terminal status line: Request To Send"""
        # Not implemented on this platform
        raise NotImplementedError  

    def setDTR(self, level=1):
        """Set terminal status line: Data Terminal Ready"""
        # Not implemented on this platform
        raise NotImplementedError  

    def getCTS(self):
        """Read terminal status line: Clear To Send"""
        # Not implemented on this platform
        raise NotImplementedError  

    def getDSR(self):
        """Read terminal status line: Data Set Ready"""
        # Not implemented on this platform
        raise NotImplementedError  

    def getRI(self):
        """Read terminal status line: Ring Indicator"""
        # Not implemented on this platform
        raise NotImplementedError  

    def getCD(self):
        """Read terminal status line: Carrier Detect"""
        # Not implemented on this platform
        raise NotImplementedError  

    # - - platform specific - - - -

    def drainOutput(self):
        """internal - not portable!"""
        # Not implemented on this platform
        raise NotImplementedError  

    def fileno(self):
        """For easier of the serial port instance with select.
           WARNING: this function is not portable to different platforms!"""
        if self.fd is None: raise portNotOpenError
        return self.fd.fileno()

if __name__ == '__main__':
    s = Serial(0,
                 baudrate=19200,        #baudrate
                 bytesize=EIGHTBITS,    #number of databits
                 parity=PARITY_EVEN,    #enable parity checking
                 stopbits=STOPBITS_ONE, #number of stopbits
                 timeout=3,             #set a timeout value, None for waiting forever
                 xonxoff=0,             #enable software flow control
                 rtscts=0,              #enable RTS/CTS flow control
               )
    s.setRTS(1)
    s.setDTR(1)
    s.flushInput()
    s.flushOutput()
    s.write('hello')
    print repr(s.read(5))
    #print s.inWaiting()
    del s

