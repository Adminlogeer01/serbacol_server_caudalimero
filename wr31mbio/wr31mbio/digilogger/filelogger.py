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
    This is the File Logger object, used to log messages to a file in the file system
"""

import os
import traceback

VERSION = "1.08"

class file_logger_handler(object):
    """
        the file logger handler class, does all the work
    """
    def __init__(self, filename, os_ver, level):
        self.log_level = level #reserved/hardset attribute in all handlers
        self.running_os = os_ver #reserved/hardset attribute in all handlers

        self.log_file_max_size = 0
        self.__file_logger_size = -1
        self.filename = filename
        self.file_path = None

        self.digi_os_auto_config()
        self.full_pathname = self.file_path + self.filename

    def digi_os_auto_config(self):
        """
            description:
                figures out the right size of the file based on the OS and tracks it
            args:
                (none)
            returns:
                (none)
            raises:
                (none)
        """
        if self.running_os == "NDS":
            self.file_path = "WEB/python/"
            self.log_file_max_size = 100 * 1024
        elif self.running_os == "SAROS":
            self.file_path = "/user/"
            self.log_file_max_size = 100 * 1024
        elif self.running_os == "DBL":
            self.file_path = "/userfs/WEB/python/"
            self.log_file_max_size = 300 * 1024
        elif self.running_os == "WIN_PC":
            self.file_path = "./"
            self.log_file_max_size = 100 * 1024 * 1024
        else: #unknown, so let's log to where we are
            self.file_path = "./"
            self.log_file_max_size = 100 * 1024

    def log(self, record):
        """
            description:
                logs the messages to a file, handles a rotating log file
            args:
                record - an instantiated log_record class object passed to all the handlers
            returns:
                (none)
            raises:
                (none)
        """
        if self.__file_logger_size < 0:
            try: self.__file_logger_size = os.path.getsize(self.full_pathname)
            except os.error: self.__file_logger_size = 0

        if self.__file_logger_size >= self.log_file_max_size:
            try: os.remove(self.full_pathname + ".0")
            except OSError: pass
            os.rename(self.full_pathname, self.full_pathname + ".0")
            self.__file_logger_size = 0

        try:
            logger_fd = open(self.full_pathname, "a")
            msg = self.format_message(record)
            logger_fd.write(msg + "\n")
            self.__file_logger_size += len(msg + "\n")
        except IOError: print "Unexpected error writing to log file: " + traceback.format_exc()

        if logger_fd: logger_fd.close()

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
            return '[%s] %s, %s - %s\n%s' % (logrecord.asctime,
                                             logrecord.levelname,
                                             logrecord.thread_name,
                                             logrecord.message,
                                             logrecord.traceback_info)

        return '[%s] %s, %s - %s' % (logrecord.asctime,
                                     logrecord.levelname,
                                     logrecord.thread_name,
                                     logrecord.message)
