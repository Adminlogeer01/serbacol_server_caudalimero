############################################################################
#                                                                          #
# Copyright (c)2014, Digi International (Digi). All Rights Reserved.       #
#                                                                          #
# Permission to use, copy, modify, and distribute this software and its    #
# documentation, without fee and without a signed licensing agreement, is  #
# hereby granted, provided that the software is used on Digi products only #
# and that the software contain this copyright notice,  and the following  #
# two paragraphs appear in all copies, modifications, and distributions as #
# well. Contact Product Management, Digi International, Inc., 11001 Bren   #
# Road East, Minnetonka, MN, +1 952-912-3444, for commercial licensing     #
# opportunities for non-Digi products.                                     #
#                                                                          #
# DIGI SPECIFICALLY DISCLAIMS ANY WARRANTIES, INCLUDING, BUT NOT LIMITED   #
# TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A          #
# PARTICULAR PURPOSE. THE SOFTWARE AND ACCOMPANYING DOCUMENTATION, IF ANY, #
# PROVIDED HEREUNDER IS PROVIDED "AS IS" AND WITHOUT WARRANTY OF ANY KIND. #
# DIGI HAS NO OBLIGATION TO PROVIDE MAINTENANCE, SUPPORT, UPDATES,         #
# ENHANCEMENTS, OR MODIFICATIONS.                                          #
#                                                                          #
# IN NO EVENT SHALL DIGI BE LIABLE TO ANY PARTY FOR DIRECT, INDIRECT,      #
# SPECIAL, INCIDENTAL, OR CONSEQUENTIAL DAMAGES, INCLUDING LOST PROFITS,   #
# ARISING OUT OF THE USE OF THIS SOFTWARE AND ITS DOCUMENTATION, EVEN IF   #
# DIGI HAS BEEN ADVISED OF THE POSSIBILITY OF SUCH DAMAGES.                #
#                                                                          #
############################################################################

"""
    This is the TCP Socket Logger object, used to log messages via a raw TCP connection
"""

import socket
from collections import deque

VERSION = "1.05"

class tcp_socket_logger_handler(object):
    """
        the socket logger handler, does all the work
    """
    def __init__(self, level, hostname, port, stored_max=100):
        self.log_level = level
        self.running_os = None

        self.hostname = hostname
        self.port = port
        self.client_socket = None
        self.stored_messages_max_size = stored_max
        self.outstanding_message = None

        self.stored_messages = deque(maxlen=self.stored_messages_max_size)

    def setup_socket(self):
        """
            description:
                simple function to setup the socket connection
            args:
                (none)
            returns:
                bool True if we think we can now use the socket connection, or bool False if we can not
            raises:
                (none)
        """
        if not self.client_socket:
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.client_socket.settimeout(2)
            try: 
                self.client_socket.connect((self.hostname, self.port))
                self.client_socket.setblocking(0)
            except socket.timeout: return False 
            except socket.error:
                self.client_socket.close()
                self.client_socket = None
                return False
        return True

    def log(self, record):
        """
            description:
                logs the messages to a tcp socket connection
                trys to connect if not currently connected
                handles communciation in a non-blocking fashion
                prunes oldest messages first if we start to run out of space
            args:
                record - an instantiated log_record class object passed to all the handlers
            returns:
                (none)
            raises:
                (none)
        """
        self.stored_messages.append(self.format_message(record))
        if self.setup_socket():
            while True:
                try:
                    if not self.stored_messages: break
                    next_message_to_send = self.stored_messages.pop()
                    print "\n\n\n{0}\n\n\n".format(next_message_to_send)
                    self.client_socket.send(next_message_to_send)
                    if self.outstanding_message: self.outstanding_message = None
                except socket.timeout:
                    if not self.outstanding_message: self.outstanding_message = next_message_to_send
                    else: self.outstanding_message += next_message_to_send
                    break
                except socket.error:                 
                    if self.outstanding_message: self.stored_messages.appendleft(self.outstanding_message)
                    self.stored_messages.appendleft(next_message_to_send)
                    self.client_socket.close()
                    self.client_socket = None
                    break

        if len(self.stored_messages) > self.stored_messages_max_size: self.stored_messages.popleft()

    def format_message(self, logrecord):
        """
            description:
                formats the message string properly, meant to be customizable per logger
            args:
                logrecord - an instantiated log_record class object passed to all the handlers
            returns:
                a well formatted message to be logged
            raises:
                (none)
        """
        if logrecord.traceback_info and logrecord.traceback_info != "None\n":
            return '[%s] %s, %s - %s\r%s\r\n' % (logrecord.asctime,
                                                 logrecord.levelname,
                                                 logrecord.thread_name,
                                                 logrecord.message,
                                                 logrecord.traceback_info)

        return '[%s] %s, %s, - %s\r\n' % (logrecord.asctime,
                                          logrecord.levelname,
                                          logrecord.thread_name,
                                          logrecord.message)
