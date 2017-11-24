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

class LogHandler:
    def __init__(self):
        self.logFile = None
        self.suppressFlag = False
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
        if self.suppressFlag:       # Suppress lof output even if logging is set
            return None
        
        if self.logFile is None:  # Log file hasn't been opened yet. Write to stdout
            self.out(msg)
            return None

        if (msg is not None) and (msg != ''):   # Non-empty message. Good to go...
            if level <= self.defLogLevel:               # Check that we're writing to an appropriate logging level
                self.logFile.write(msg)
                self.logFile.write('\n')
                self.logFile.flush()            # Protect against buffered log data getting lost due to program crash
        return None

    # Temporarily suppress all logging
    def suppress(self):
        self.suppressFlag = True
        return None

    # Remove temporary logging suppression
    def unSuppress(self):
        self.suppressFlag = False
        return None
