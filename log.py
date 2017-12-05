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

class LogHandler:
    def __init__(self):
        self.logFile = None
        self.suppressFlag = False
        self.tmpFile = None
        return None

    def openLog(self, path = None, append = False, level = 1):
        if self.logFile is not None:    # Another log file is open. Need to close it first
            self.logFile.close()
        self.defLogLevel = level
        if path is not None:    # Path provided. Open log file for write or append
            try:
                if append is True:
                    self.logFile = open(path,'a')
                else:
                    self.logFile = open(path,'w')
                # Now,copy any existing data from the temp file
                self.tmpFile.close()
                self.tmpFile = open(globs.tmpName, 'r')
                tmpData = self.tmpFile.read()
                self.logFile.write(tmpData)
                self.tmpFile.close()
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
        return None

    # Write log info to stdout
    def out(self, msg):
        if (msg is not None) and (msg != ''):
            sys.stdout.write(msg)
            sys.stdout.write('\n')
        return None

    # Write log info to log file
    def write(self, level, msg):
        if self.suppressFlag:       # Suppress log output even if logging is set
            return None
        
        if self.logFile is not None:
            logTarget = self.logFile
        else:
            # Log file hasn't been opened yet. 
            if self.tmpFile is None:
                # Open a temp file to hold the output
                self.tmpFile = open(globs.tmpName, 'w')
                self.defLogLevel = 3
            logTarget = self.tmpFile

        if (msg is not None) and (msg != ''):   # Non-empty message. Good to go...
            if level <= self.defLogLevel:               # Check that we're writing to an appropriate logging level
                logTarget.write(msg)
                logTarget.write('\n')
                logTarget.flush()          # Protect against buffered log data getting lost due to program crash
        return None

    # Temporarily suppress all logging
    def suppress(self):
        self.suppressFlag = True
        return None

    # Remove temporary logging suppression
    def unSuppress(self):
        self.suppressFlag = False
        return None
