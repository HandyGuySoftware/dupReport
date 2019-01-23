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

# Class to handle log management
class LogHandler:
    def __init__(self):
        self.logFile = None         # Handle to log file, when opened
        self.suppressFlag = False   # Do we want to suppress log output? (Relic from older versions)
        self.defLogLevel = 3        # Default logging level. Will get updated when log is opened
        self.tmpFile = None         # Temp file to hold log output before log file is opened.
        self.tmpLogPath = '{}/{}'.format(globs.progPath, globs.tmpName)    # Path fo rtemp log
        return None

    def openLog(self, path = None, append = False, level = 1):
        if self.logFile is not None:    # Another log file is open. Need to close it first
            self.logFile.close()
        self.defLogLevel = level
        if path is not None:    # Path provided. Open log file for write or append
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
                    self.tmpFile.close()
                    os.remove(self.tmpLogPath)
                    self.tmpFile = None
            except (OSError, IOError):
                sys.stderr.write('Error opening log file: {}\n'.format(path))

        return None

    def closeLog(self):
        if self.logFile is not None:    # Another log file is open. Need to close it first
            self.logFile.close()
        self.logFile = None
        return None;

    # Write log info to stderr
    def err(self, msg):
        if (msg is not None) and (msg != ''):
            sys.stderr.write(msg)
            sys.stderr.write('\n')
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

    # Write log info to log file
    def write(self, level, msg):
        if self.suppressFlag:       # Suppress log output even if logging is set
            return None
        
        if self.logFile is not None:
            logTarget = self.logFile
        else:
            # Log file hasn't been opened yet. Send output to temp file
            if self.tmpFile is None:
                # Open a temp file to hold the output
                self.tmpFile = open(self.tmpLogPath, 'w')
            logTarget = self.tmpFile

        if (msg is not None) and (msg != ''):   # Non-empty message. Good to go...
            if level <= self.defLogLevel:               # Check that we're writing to an appropriate logging level
                logTarget.write(msg)
                logTarget.write('\n')
                logTarget.flush()          # Protect against buffered log data getting lost due to program crash
        return None

    # Temporarily suppress all logging
    # This is useful if info gets sent to the log before the log file is opened.
    # This was made obsolete in V2.1 with the creation of the temporary file
    # Kept around in case it becomes useful later
    def suppress(self):
        self.suppressFlag = True
        return None

    # Remove temporary logging suppression
    def unSuppress(self):
        self.suppressFlag = False
        return None
