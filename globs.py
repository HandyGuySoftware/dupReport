#####
#
# Module name:  globs.py
# Purpose:      Global object repository for use by dupReport program
# 
#####


# Import dupReport modules

# Define version info
version=[2,1,0]     # Program Version
status='Beta 1'
dbVersion=[1,0,1]   # Required DB version
copyright='Copyright (c) 2017 Stephen Fried for HandyGuy Software.'

# Define global variables
dbName='dupReport.db'               # Default database name
logName='dupReport.log'             # Default log file name
rcName='dupReport.rc'               # Default configuration file name
db = None                           # Global database object
dateFormat = None                   # Global date format - can be overridden per backup set
timeFormat = None                   # Global time format - can be overridden per backup set
report = None                       # Gobal report object
ofileList = None                    # List of output files
optionManager = None                # Option Manager
opts = None                         # Global program options
progPath = None                     # Path to script files

# Text & format fields for report email
emailText=[]      # List of email text components
emailFormat=[]    # Corresponding list of emial components print formats

# Global variables referencing objects in other modules
log = None              # Log file handling
inServer = None      # Inbound email server
outServer =  None     # Outbound email server
