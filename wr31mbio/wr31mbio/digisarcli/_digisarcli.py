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
    A nice library to handle sarcli communication, to make sure we can talk to the cli properly
"""

import sarcli

VERSION = "1.04"

class digisarcli(object):
    """
        class that handles the sarcli communication
    """
    def __init__(self, logger):
        self.logger = logger
        self.cli = None
        self.open_cli()

    def open_cli(self):
        """
            description:
                opens the TransPort cli
            args:
                (none)
            returns:
                (none)
            raises:
                (none)
        """
        try:
            if self.cli: self.close_cli()
            self.cli = sarcli.open()
        except: self.logger.error("Error opening CLI")

    def close_cli(self):
        """
            description:
                closes the transport cli. should be called before this class loses scope
                    i.e. should be called if script exits gracefully
            args:
                (none)
            returns:
                (none)
            raises:
                (none)
        """
        try: self.cli.close()
        except: pass
        self.cli = None

    def read_command_line(self, maximum_retry_count=3, response_as_string=False):
        """
            description:
                reads data from the command line, useful for long running commands
            args:
                maximum_retry_count - the number of times to retry before giving up
                response_as_string
            returns:
                a tuple containing:
                    a boolean true/false to indicate success/failure of reading from the command line

                    a list of of lines returned from the cli (makes it comprable to digicli)
                    **or**
                    a string returned by the cli (breaks compatibility with digicli)
            raises:
                (none)
        """
        if not self.cli: self.open_cli()

        for attempt in range(maximum_retry_count):
            try:
                response_string = self.cli.read()
                self.logger.debug("Received SARCLI Response: " + response_string)
                if not response_as_string:
                    return True, response_string.split("\n")
                else:
                    return True, response_string
            except:
                self.logger.error("[%d] Parser Command Raw Read Error" % attempt)
                self.open_cli()

        if not response_as_string:
            return False, []
        return False, ""

    def send_command_get_response(self, command, maximum_retry_count=3, response_as_string=False):
        """
            description:
                sends a command directly to the cli and gathers the response
            args:
                command - the cli command to execute on the cli interface of the TransPort
                maximum_retry_count - the number of times to retry before giving up
            returns:
                a tuple containing:
                    a boolean true/false to indicate success/failure of reading from the command line
                    a list of of lines returned from the cli (makes it comprable to digicli)
            raises:
                (none)
        """
        if not self.cli: self.open_cli()

        self.logger.debug("Sending SARCLI Command: " + command)
        for attempt in range(maximum_retry_count):
            try:
                self.cli.write(command)
                return self.read_command_line(maximum_retry_count, response_as_string)
            except:
                self.logger.error("[%d] Parser Command Raw Write Error" % attempt)
                self.open_cli()

        return False, []

    def command_to_dict(self, command, splitter=":", maximum_retry_count=3):
        """
            description:
                takes in a cli command and will convert the response to a dictionary
            args:
                command - the cli command to execute on the cli interface of the TransPort
                splitter - the string to use to split the returned lines into key value pairings
                maximum_retry_count - the number of times to retry before giving up
            returns:
                a dictionary of key value pairs based on what was found, very useful for certain
                commands like 'modemstat ?'
            raises:
                (none)
        """
        status, lines = self.send_command_get_response(command, maximum_retry_count)
        if not status: return {}

        temp_dict = {}
        for line in lines:
            if line.find(splitter) >= 0:
                part = line.strip().split(splitter)
                temp_dict[part[0].strip().lower().replace(" ", "_")] = part[1].strip()
        return temp_dict
