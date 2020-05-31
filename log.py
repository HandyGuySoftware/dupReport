#####
#
# Module name:  log.py
# Purpose:      Manage logging functions for dupReport
# 
# Notes:
#
#####

# Import system modules
import sys
import globs
import os
import datetime
import logging
import socket
from logging.handlers import SysLogHandler


# Class to handle log management
class LogHandler:
    def __init__(self):
        self.logFile = None             # Handle to log file, when opened
        self.defLogLevel = globs.SEV_NOTICE   # Default logging level. Will get updated when log is opened
        self.tmpFile = None             # Temp file to hold log output before log file is opened.
        self.tmpLogPath = globs.progPath + '/' + globs.logName    # Path for temp log
        self.hostname = socket.gethostname()
        self.syslog = {
            'logger': None,
            'host': None,
            'port': 514, 
            'level': globs.SEV_NOTICE,
            'handler': None
            }

        return None

    def openLog(self, path = None, append = False, level = globs.SEV_DEBUG):
        if self.logFile is not None:    # Another log file is open. Need to close it first
            self.logFile.close()

        self.defLogLevel = level

        if path is not None:    # Path provided. Open log file for write or append

            # Issue #148. We opened the default log file (self.tmpLogPath) to start collecting logs until we found the real name in the .rc file.
            # If it turns out that the actual log file (passwd in via the 'path' parameter') is the same as the temporary file, just keep using that.
            # Else, open the log file & copy the temp log contents into it.
            if os.path.normpath(os.path.normcase(self.tmpLogPath)) != os.path.normpath(os.path.normcase(path)):     # Are the two paths different?
                globs.log.write(globs.SEV_DEBUG, function='Log', action='openLog', msg='Log file {} different than tmp file {}. Copying data.'.format(path, self.tmpLogPath))
                try:
                    if append is True:
                        self.logFile = open(path,'a', encoding="utf-8")
                    else:
                        self.logFile = open(path,'w', encoding="utf-8")
                    # Now,copy any existing data from the temp file
                    if self.tmpFile is not None:
                        self.tmpFile.close()
                        self.tmpFile = open(self.tmpLogPath, 'r')
                        tmpData = self.tmpFile.read()
                        self.logFile.write(tmpData)
                        self.logFile.flush()
                        self.tmpFile.close()
                        os.remove(self.tmpLogPath)
                        self.tmpFile = None
                except (OSError, IOError):
                    e = sys.exc_info()[0]
                    globs.log.write(globs.SEV_ERROR, function='Log', action='openLog', msg='Error opening log file {}: {}'.format(path, e))
                    sys.stderr.write('Error opening log file {}: {}\n'.format(path, e))

        if globs.opts['syslog'] != '':
            syslogparts = globs.opts['syslog'].split(':')
            self.syslog['host'] = syslogparts[0]
            if len(syslogparts) == 2:   # Syslog port specified.
                self.syslog['port'] = int(syslogparts[1])

            if globs.opts['sysloglevel'] not in range(8):  # Severity levels are 0-7
                globs.log.write(globs.SEV_ERROR, function='Log', action='openLog', msg='Invalid syslog level specified: {}. Reverting to level 5 (SEV_NOTICE)'.format(globs.opts['sysloglevel']))
            else:
                self.syslog['level'] = globs.opts['sysloglevel']

            globs.log.write(globs.SEV_DEBUG, function='Log', action='openLog', msg='Opening syslog connection to {}:{}'.format(self.syslog['host'], self.syslog['port']))
            try:
                self.syslog['logger'] = logging.getLogger()
                self.syslog['logger'].setLevel(self.syslog['level'])
                self.syslog['handler'] = SysLogHandler(address=(self.syslog['host'], self.syslog['port']), facility = 16)
                self.syslog['logger'].addHandler(self.syslog['handler'])
                self.syslog['logger'].propagate = False   
            except :
                e = sys.exc_info()[0]
                globs.log.write(globs.SEV_ERROR, function='Log', action='connect:syslog', msg='Error connecting to syslog sever {}:{}. Most likely an incorrect server or port was specified. Msg: {}'.format(self.syslog['host'], self.syslog['port'], e))
                self.syslog['handler'] = None

        return None

    def closeLog(self):
        if self.syslog['handler'] != None:
            self.write(globs.SEV_NOTICE, function='Log', action='closeLog', msg='Closing syslog connection')
            self.syslog['handler'].close

        if self.logFile is not None:    # Another log file is open. Need to close it first
            self.logFile.close()
        self.logFile = None

        return None;

    # Write log info to stderr
    def err(self, msg):
        if (msg is not None) and (msg != ''):
            sys.stderr.write('ERROR: {}\n'.format(msg))
            sys.stderr.flush()
        return None

    # Write log info to stdout
    def out(self, msg, newline=True):
        if (msg is not None) and (msg != ''):
            sys.stdout.write(msg)
            if newline:
                sys.stdout.write('\n')
            sys.stdout.flush()
        return None

    def writeSyslog(self, level, msg):

        newMsg = msg
        
        # Syslog messages have to be less than 1K in length.
        if len(msg) > 999:
            newMsg = msg[:999]
            self.write(globs.SEV_DEBUG, function='log', action='writeSyslog', msg='Truncating syslog message')

        if level <= self.syslog['level']:               # Check that we're writing to an appropriate logging level
            if level <= globs.SEV_CRITICAL:
                self.syslog['logger'].critical(newMsg)
            elif level <= globs.SEV_ERROR:
                self.syslog['logger'].error(newMsg)
            elif level <= globs.SEV_WARNING:
                self.syslog['logger'].warning(newMsg)
            elif level <= globs.SEV_INFO:
                self.syslog['logger'].info(newMsg)
            elif level <= globs.SEV_DEBUG:
                self.syslog['logger'].debug(newMsg)

        return None


    # Write log info to log file
    # Log Format = [TIMESTAMP][SEVERITY][FUNCTION][ACTION]<MESSAGE>
    def write(self, level, function='-', action='-', msg='' ):

        if self.logFile is not None:
            logTarget = self.logFile
        else:
            # Log file hasn't been opened yet. Send output to temp file
            if self.tmpFile is None:
                # Open a temp file to hold the output
                self.tmpFile = open(self.tmpLogPath, 'w')
            logTarget = self.tmpFile

        if (msg is not None) and (msg != ''):   # Non-empty message. Good to go...
            logData = '[{}][{}][{}][{}]{}'.format(datetime.datetime.now().isoformat(), globs.sevlevels[level][0], function, action, msg)

            # Write to program log
            if level <= self.defLogLevel:               # Check that we're writing to an appropriate logging level
                logTarget.write(logData)
                logTarget.write('\n')
                logTarget.flush()          # Protect against buffered log data getting lost due to program crash

            # Write to syslog, if necessary
            if self.syslog['handler'] != None:
                self.writeSyslog(level, logData)

        return None

