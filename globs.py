#####
#
# Module name:  globs.py
# Purpose:      Global object repository for use by dupReport program
# 
#####

import os

# Define version info
version=[2,2,12]     # Program Version
status='Release'
dbVersion=[1,0,3]   # Required DB version
rcVersion=[3,0,0]   # Required RC version
copyright='Copyright (c) 2020 Stephen Fried for HandyGuy Software.'

# Define global variables
dbName='dupReport.db'               # Default database name
logName='dupReport.log'             # Default log file name
rcName='dupReport.rc'               # Default configuration file name
tmpName = 'duplog.tmp'
db = None                           # Global database object
dateFormat = None                   # Global date format - can be overridden per backup set
timeFormat = None                   # Global time format - can be overridden per backup set
report = None                       # Global report object
ofileList = None                    # List of output files
optionManager = None                # Option Manager
opts = None                         # Global program options
progPath = None                     # Path to script files
appriseObj = None                   # dupApprise instance

# Text & format fields for report email
emailText=[]      # List of email text components
emailFormat=[]    # Corresponding list of emial components print formats

# Global variables referencing objects in other modules
log = None              # Log file handling
inServer = None      # Inbound email server
outServer =  None     # Outbound email server


# Mask sensitive data in log files
# Replace incoming string with string of '*' the same length of the original
def maskData(inData, force = False):
    if inData is None:  # Empty input or global options haven't been processed yet. Return unmasked input.
        return inData
    elif force:                         # Mask regardless of what parameter says. Useful if masking before options are processed.
        return "*" * len(inData)
    elif opts is None:
        return inData
    elif 'masksensitive' in opts and opts['masksensitive'] is True:
        return "*" * len(inData)        # Mask data.
    else:
        return inData                   # Return unmasked input

# Close everything and exit cleanly
def closeEverythingAndExit(errcode):
    
    log.write(1,'Closing everything...')

    if inServer is not None:
        log.write(1,'Closing inbound email server...')
        inServer.close()
    if outServer is not None:
        log.write(1,'Closing outbound email server...')
        outServer.close()
    if db is not None:
        log.write(1,'Closing database file...')
        db.dbClose()
    if log is not None:
        log.write(1,'Closing log file...')
        log.closeLog()

    os._exit(errcode)
