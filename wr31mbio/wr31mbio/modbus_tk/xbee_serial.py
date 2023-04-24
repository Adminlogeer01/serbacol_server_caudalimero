import digixbee
import logging
import binascii
import time

LOGGER = logging.getLogger()
BROADCAST = '[00:00:00:00:00:00:ff:ff]!'

class xbee_serial(object):
    def __init__(self, logger, timeout, endpoint=0xE8, baudrate=9600, destination=BROADCAST):
        self.xb = digixbee.standard_setup(logger)
        self.endpoint = endpoint
        self.baudrate = baudrate
        self.timeout = timeout
        self.destination = destination
        self.opened = False
        self.portstr = "xbee_serial"

    def isOpen(self):
        return self.opened

    def open(self):
        if not self.xb.endpoint_is_bound(self.endpoint):
            self.xb.bind_xbee(self.endpoint)
        self.opened = True

    def close(self):
        # self.xb.unbind_xbee(self.endpoint)
        self.opened = False

    def flushInput(self):
        pass

    def flushOutput(self):
        pass

    def read(self, requested_size, timeout=20):
        start_time = time.time()
        buf = ""
        while buf == "" and (time.time() - start_time) < timeout:
            recv_from_xbee = self.xb.recv_xbee_packet(self.endpoint)
            if recv_from_xbee:
                buf = recv_from_xbee.raw_data
        LOGGER.debug("read buffer: %s" % binascii.hexlify(buf))
        return buf

    def write(self, data):
        if self.opened:
            LOGGER.debug("write buffer: %s" % (binascii.hexlify(data)))
            self.xb.send_xbee_msg(self.destination, data, self.endpoint)
        else:
            self.open()
            self.xb.send_xbee_msg(self.destination, data, self.endpoint)
