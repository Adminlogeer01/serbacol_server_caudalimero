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
    A Digi (device) specific python class tied to logging
    Designed to work on Digi devices, of various python versions (2.4.3, 2.6.1, 2.7.1)
    as well as on a PC
"""

import os
import sys
import time
import thread
import threading
import traceback

LOGGING_LEVELS = {
    "CRITICAL": 50,
    "ERROR": 40,
    "WARN": 30,
    "INFO": 20,
    "DEBUG": 10,
    "NOTSET": 0
}

VERSION = "1.15"

class digilogger(object):
    """
        Main class dedicated to handling logging
    """
    def __init__(self):
        self.handlers = []
        self.running_os = "Unknown"
        self.datefmt = "%m-%d-%Y %H:%M:%S"

        self.identify_os()
        self.__start_time = self.get_time_in_sec() #must be called after OS is indentified
        self.__lock = threading.RLock()
        self.__setup_inspect()

    def add_handler(self, hdlr):
        """
            description:
                adds the specified handler to this logger
            args:
                hdlr - instantiated logger object (filelogger, printlogger, socketlogger, etc)
            returns:
                (none)
            raises:
                (none)
        """
        self.__lock.acquire()
        if hdlr not in self.handlers:
            hdlr.running_os = self.running_os
            self.handlers.append(hdlr)
        self.__lock.release()

    def remove_handler(self, hdlr):
        """
            description:
                removes the specified handler from this logger
            args:
                hdlr - instantiated logger object (filelogger, printlogger, socketlogger, etc)
            returns:
                (none)
            raises:
                (none)
        """
        self.__lock.acquire()
        if hdlr in self.handlers: self.handlers.remove(hdlr)
        self.__lock.release()

    def info(self, msg):
        """
            description:
                INFO courtesy function wrapper around debug_log
                additional information is added to the message in the debug_log function
            args:
                msg - text portion of the message to log
            returns:
                (none)
            raises:
                (none)
        """
        self.debug_log("INFO", msg)

    def warn(self, msg):
        """
            description:
                WARN courtesy function wrapper around debug_log
                additional information is added to the message in the debug_log function
            args:
                msg - text portion of the message to log
            returns:
                (none)
            raises:
                (none)
        """
        self.debug_log("WARN", msg)

    def error(self, msg):
        """
            description:
                ERROR courtesy function wrapper around debug_log
                additional information is added to the message in the debug_log function
            args:
                msg - text portion of the message to log
            returns:
                (none)
            raises:
                (none)
        """
        self.debug_log("ERROR", msg)

    def debug(self, msg):
        """
            description:
                DEBUG courtesy function wrapper around debug_log
                additional information is added to the message in the debug_log function
            args:
                msg - text portion of the message to log
            returns:
                (none)
            raises:
                (none)
        """
        self.debug_log("DEBUG", msg)

    def debug_log(self, msg_type, msg):
        """
            description:
                heart of the logging class, formats the message and sends it to all the registered callbacks
            args:
                msg_type - the type of message, described in the LOGGING_LEVELS dictionary. Used to determine if
                    an interface should log the message or not, as well as for trackback information being added
                    to the ERROR and CRITICAL logs
                msg - text portion of the message to log
            returns:
                (none)
            raises:
                (none)
        """
        self.__lock.acquire()
        for logger_hdlr in self.handlers:
            if LOGGING_LEVELS[msg_type.upper()] >= logger_hdlr.log_level: break
        else: #exit out early before we do anything if there's nothing to actually log
            self.__lock.release()
            return

        new_record = log_record(msg_type, msg, self.get_time_in_sec(), self.datefmt)
        if msg_type == "ERROR" or msg_type == "CRITICAL":
            new_record.traceback_info = traceback.format_exc()
        for logger_hdlr in self.handlers:
            if new_record.levelno >= logger_hdlr.log_level: 
                logger_hdlr.log(new_record)
        self.__lock.release()

    def get_time_in_sec(self):
        """
            description:
                when no time is set in the system in SAROS, time can behave oddly, so let's use clock time instead
            args:
                (none)
            returns:
                (none)
            raises:
                (none)
        """
        return_time = time.time()
        if self.running_os == "SAROS":
            if return_time < 1403276273 or return_time >= 2147483648: return_time = time.clock()
        return return_time

    def identify_os(self):
        """
            description:
                Sets the OS we are currently running on
                Probably should be in a utility library versus this one
            args:
                (none)
            returns:
                (none)
            raises:
                (none)
        """
        if sys.platform.startswith('digiSarOS'): self.running_os = "SAROS"
        elif sys.platform.startswith('digiconnect'): self.running_os = "NDS"
        elif sys.platform.startswith('win32'): self.running_os = "WIN_PC"
        elif sys.platform.startswith('linux') and os.path.isdir('/userfs') and os.path.isfile('/etc/version'):
            #Try to detect if this is DBL or not
            if '\nDEL' in open('/etc/version', 'r').read(): self.running_os = "DBL"
            else: self.running_os = "LINUX"
        else: self.running_os = "UNKNOWN"

    def __setup_inspect(self):
        """
            description:
                We need to be able to get the frame we're in for debugging,
                this sets up that in relation to the OS we're on
            args:
                (none)
            returns:
                (none)
            raises:
                (none)
        """
        try:
            from inspect import stack
            self.get_current_frame = lambda: _get_last_context(stack(), True)
        except ImportError: self.get_current_frame = _get_current_frame_except


_LOGGERS = {}  # mutable global mapping of named loggers


def get_logger(name="root", show_debug_output=True):
    """Emulates the standard library's `getLogger` function for allowing
    global access to the same logger objects accross different modules

    NOTE: assumes usage of `standard_setup` function

    >>> logger = get_logger()  # root logger
    >>> special_logger = get_logger("special")
    >>> thesame_logger = get_logger("special")
    >>> special_logger is thesame_logger  # True
    >>> yetanother_log = getLogger("special")  # stdlib API compatibility
    >>> yetanother_log is special_logger  # True
    """
    if name not in _LOGGERS:
        _LOGGERS[name] = standard_setup(show_debug_output)
    return _LOGGERS[name]


getLogger = get_logger  # for API compatibility with stdlib's `logging`


def standard_setup(show_debug_output=True):
    """
        description:
            standard way to setup the digilogger
        args:
            (none)
        returns:
            an instiantiated digilogger object
        raises:
            (none)
    """
    logger = digilogger()

    from filelogger import file_logger_handler
    file_logger = file_logger_handler("debug.log", logger.running_os, LOGGING_LEVELS["INFO"])
    logger.add_handler(file_logger)

    if show_debug_output:
        from printlogger import print_logger_handler
        print_logger = print_logger_handler(LOGGING_LEVELS["DEBUG"])
        logger.add_handler(print_logger)

    return logger


class log_record(object):
    """
        This log record class is a modified version of the logRecord from
        the standard logging library developed by Vinay Sajip (2001-2010)

        A log_record instance represents an event being logged.

        log_record instances are created every time something is logged. They
        contain all the information pertinent to the event being logged. The
        main information passed in is in msg and args, which are combined
        using str(msg) % args to create the message field of the record. The
        record also includes information such as when the record was created,
        the source line where the logging call was made, and any exception
        information to be logged.
    """
    asctime = ""
    message = ""
    levelname = ""
    levelno = -1
    created = -1
    thread = ""
    thread_name = ""
    traceback_info = None
    def __init__(self, level, message, time_val, datefmt):
        self.asctime = time.strftime(datefmt, time.localtime(time_val))
        self.message = message
        self.levelname = level
        self.levelno = LOGGING_LEVELS[level.upper()]
        self.created = time_val
        self.thread = thread.get_ident()
        if hasattr(threading, "current_thread"):
            self.thread_name = threading.current_thread().name
        else:
            self.thread_name = threading.currentThread()

def _get_last_context(stack_list, using_inspect=False):
    """
        description:
            This function searches a given stack for the last
            call before entering the logging module
        args:
            (none)
        returns:
            returns a tuple of information, file executing, line number, function name
        raises:
            (none)
    """
    last_call = stack_list[-1][0]
    if using_inspect:
        # The inspect module return a stack frame with a different layout than traceback
        last_call = stack_list[0][1]
        for item in stack_list:
            if item[1] != last_call:
                return os.path.basename(item[1]), item[2], item[3]

    for item in reversed(stack_list):
        if item[0] != last_call:
            return item[0], item[1], item[2]

    return ("(unknown file)", 0, "(unknown function)")

def _get_current_frame_except():
    """
        description:
            gets the current frame and returns it
        args:
            (none)
        returns:
            return a tuple that represents the current frame
        raises:
            (none)
    """
    try: raise Exception
    except: stack_list = traceback.extract_stack()
    return _get_last_context(stack_list)

__all__ = ["digilogger"]
