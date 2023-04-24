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
    This is the Print Logger object, used to log messages to STDOUT
"""

VERSION = "1.05"

class print_logger_handler(object):
    """
        the print logger handler, does all the work
    """
    def __init__(self, level):
        self.log_level = level #reserved/hardset attribute in all handlers
        self.running_os = None #reserved/hardset attribute in all handlers

    def log(self, record):
        """
            description:
                logs the messages to a STDOUT
            args:
                record - an instantiated log_record class object passed to all the handlers
            returns:
                (none)
            raises:
                (none)
        """
        print self.format_message(record)

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

        return '[%s] %s, %s, - %s' % (logrecord.asctime,
                                      logrecord.levelname,
                                      logrecord.thread_name,
                                      logrecord.message)
