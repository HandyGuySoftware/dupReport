#####
#
# Module name:  globs.py
# Purpose:      Global object repository for use by dupReport program
# 
#####


# Import dupReport modules
import log
import dremail
import globs

# Define version info
version=[2,1,0]     # Program Version
status='Beta 1'
dbVersion=[1,0,1]   # Required DB version
copyright='Copyright (c) 2017 Stephen Fried for HandyGuy Software.'

# Define global variables
opts={}                             # Parsed and read options from command line & .rc file
dbName='dupReport.db'               # Default database name
logName='dupReport.log'             # Default log file name
rcName='dupReport.rc'               # Default configuration file name
db = None                           # Global database object
dateFormat = None                   # Global date format - can be overridden per backup set
timeFormat = None                   # Global time format - can be overridden per backup set
report = None                       # Gobal report object

# Text & format fields for report email
emailText=[]      # List of email text components
emailFormat=[]    # Corresponding list of emial components print formats

# Global variables referencing objects in other modules
log = log.LogHandler()              # Log file handling
inServer = dremail.EmailServer()      # Inbound email server
outServer = dremail.EmailServer()     # Outbound email server
