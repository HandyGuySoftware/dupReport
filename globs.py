#####
#
# Module name:  globs.py
# Purpose:      Global object repository for use by dupReport program
# 
#####

import os

# Define version info
version=[3,0,1]     # Program Version
status='Release'
dbVersion=[3,0,0]   # Required DB version
rcVersion=[3,1,0]   # Required RC version
copyright='Copyright (c) 2017-2020 Stephen Fried for Handy Guy Software.'

# Define global variables
dbName='dupReport.db'               # Default database name
logName='dupReport.log'             # Default log file name
rcName='dupReport.rc'               # Default configuration file name
db = None                           # Global database object
dateFormat = None                   # Global date format - can be overridden per backup set
timeFormat = None                   # Global time format - can be overridden per backup set
report = None                       # Global report object
ofileList = None                    # List of output files
optionManager = None                # Global Option Manager
emailManager = None                 # Global email server management
opts = None                         # Global program options
progPath = None                     # Path to script files
appriseObj = None                   # dupApprise instance

# Text & format fields for report email
emailText=[]      # List of email text components
emailFormat=[]    # Corresponding list of emial components print formats

# Global variables referencing objects in other modules
log = None              # Log file handling
inServer = None         # Inbound email server
outServer =  None       # Outbound email server

# Define logging levels
SEV_EMERGENCY = 0
SEV_ALERT = 1
SEV_CRITICAL = 2
SEV_ERROR = 3
SEV_WARNING = 4
SEV_NOTICE = 5
SEV_INFO = 6
SEV_DEBUG = 7

sevlevels = [
    ('EMERGENCY', SEV_EMERGENCY),
    ('ALERT', SEV_ALERT), 
    ('CRITICAL', SEV_CRITICAL),
    ('ERROR', SEV_ERROR), 
    ('WARNING', SEV_WARNING),
    ('NOTICE', SEV_NOTICE),
    ('INFO', SEV_INFO),
    ('DEBUG', SEV_DEBUG)
    ]

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
    
    log.write(SEV_NOTICE, function='Globs', action='closeEverythingAndExit', msg='Closing everything...')
    if emailManager != None:
        if len(emailManager.incoming) != 0:
            for server in emailManager.incoming:
                log.write(SEV_NOTICE, function='Globs', action='closeEverythingAndExit', msg='Closing inbound email server: {}'.format(emailManager.incoming[server].name))
                emailManager.incoming[server].close()
        if len(emailManager.incoming) != 0:
            for i in range(len(emailManager.outgoing)):
                log.write(SEV_NOTICE, function='Globs', action='closeEverythingAndExit', msg='Closing outbound email server: {}'.format(emailManager.outgoing[i].name))
                emailManager.outgoing[i].close()
    if db is not None:
        log.write(SEV_NOTICE, function='Globs', action='closeEverythingAndExit', msg='Closing database file.')
        db.dbClose()
    if log is not None:
        log.write(SEV_NOTICE, function='Globs', action='closeEverythingAndExit', msg='Closing log file.')
        log.closeLog()

    os._exit(errcode)

