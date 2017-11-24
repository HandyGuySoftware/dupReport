#####
#
# Module name:  startup.py
# Purpose:      Program initialization and parameter validation functions
# 
# Notes:
#
#####

# Import system modules
import configparser
from configparser import SafeConfigParser 
import os
import os.path
import sys
import configparser
from configparser import SafeConfigParser 
import argparse

# Import dupReport modules
import globs
import startup
import db
import drdatetime
import report

# Get directory path where script is running
def getScriptPath():
    return os.path.dirname(os.path.realpath(sys.argv[0]))

# rcParts tuples
# 1 - section name
# 2 - option name
# 3 - default value
# 4 - is the default value acceptable if not already present in .rc file (true/false)?
rcParts= [
    # [main] section defaults
    ('main','version','{}.{}.{}'.format(globs.version[0],globs.version[1],globs.version[2]), True),
    ('main','dbpath',getScriptPath(), True),
    ('main','logpath',getScriptPath(), True),
    ('main','verbose','1', True),
    ('main','logappend','false', True),
    ('main','subjectregex','^Duplicati Backup report for', True),
    ('main','srcregex','\w*', True),
    ('main','destregex','\w*', True),
    ('main','srcdestdelimiter','-', True),
    ('main','dateformat', 'MM/DD/YYYY', False),
    ('main','timeformat','HH:MM:SS', False),
    
    # [incoming] section defaults
    ('incoming','intransport','imap', False),
    ('incoming','inserver','localhost', False),
    ('incoming','inport','993', False),
    ('incoming','inencryption','tls', False),
    ('incoming','inaccount','someacct@hostmail.com', False),
    ('incoming','inpassword','********', False),
    ('incoming','infolder','INBOX', False),

    # [outgoing] section defaults
    ('outgoing','outserver','localhost', False),
    ('outgoing','outport','587', False),
    ('outgoing','outencryption','tls', False),
    ('outgoing','outaccount','someacct@hostmail.com', False),
    ('outgoing','outpassword','********', False),
    ('outgoing','outsender','sender@hostmail.com', False),
    ('outgoing','outreceiver','receiver@hostmail.com', False),

    # [report] section defaults
    ('report','style','standard', True),
    ('report','groupby','source', True),
    ('report','sortorder','source', True),
    ('report','border','1', True),
    ('report','padding','5', True),
    ('report','reporttitle','Duplicati Backup Summary Report', True),
    ('report','sizedisplay','none', True),
    ('report','showsizedisplay','bytes', True),
    ('report','displaymessages','false', True),
    ('report','displaywarnings','true', True),
    ('report','displayerrors','true', True),
    ('report','subheadbg','#D3D3D3', True),
    ('report','jobmessagebg','#FFFFFF', True),
    ('report','jobwarningbg','#FFFF00', True),
    ('report','joberrorbg','#FF0000', True),

    # [headings] section defaults
    ('headings','Source','Source', True),
    ('headings','Destination','destination', True),
    ('headings','Date','Date', True),
    ('headings','Time','Time', True),
    ('headings','Files','Files', True),
    ('headings','FilesPlusMinus','+/-', True),
    ('headings','Size','Size', True),
    ('headings','SizePlusMinus','+/-', True),
    ('headings','Added','Added', True),
    ('headings','Deleted','Deleted', True),
    ('headings','Modified','Modified', True),
    ('headings','Errors','Errors', True),
    ('headings','Result','Result', True),
    ('headings','JobMessages','Messages', True),
    ('headings','JobWarnings','Warnings', True),
    ('headings','JobErrors','Errors', True),
   ]


# Initializer for Startup class. 
# Returns True if config options require a restart
# Returns False if program can continue (no config options reset
# Returns None if error
class Startup:
    def __init__(self):
        globs.log.write(1, 'Startup.__init__()')
        self.rcFileName = None
        return None

    # See if RC file has all the parts needed before proceeding with the rest of the program
    # Returns <status>, <newRC>
    # 
    # <status> = True if need to run upgrade program
    # <status>=False if current RC version is OK
    # 
    # newRC = True of enough RC info has changed to require user config & restart
    # newRC = False if program can continue without restart
    def rcInitialize(self,rcName):

        newRc = False       # Flag to see if any RC parts have changed
        upgrade = False     # Return Status
        
        globs.log.write(1, 'Startup.rcInitialize({})'.format(rcName))

        if self.rcFileName:     # Rc file already initiailzed. Something is wrong.
            globs.log.write(2, 'RC file {} already initialized. {} is a duplicate request.'.format(self.rcFileName, rcName))
            return False, False

        try:
            rcParser = configparser.SafeConfigParser()
            rcParser.read(rcName)
        except configparser.ParsingError as err:
            globs.log.err('RC file parsing error: {}\n'.format(err.args[0]))
            globs.log.write(1, 'RC file parsing error: {}\n'.format(err.args[0]))
            return True, True  # Abort program. Can't continue with RC error

        # Get current RC version, if available. 
        if rcParser.has_option('main','version'):
            rcVersion = rcParser.get('main','version')

            # Split RC version intom component parts
            verParts = rcVersion.split('.')
            currVerNum = (int(verParts[0]) * 100) + (int(verParts[1]) * 10) + int(verParts[2])
            newVerNum = (globs.version[0] * 100) + (globs.version[1] * 10) + globs.version[2]
            if currVerNum < newVerNum:
                upgrade = True
                newRc = True
                return upgrade, newRc
        else:       # Current RC version not available. Using a really old version of the program, so need to upgrade
            return True, True

        # Loop through all the required parts of the RC file. If not there, add them
        for section, option, default, canCont in rcParts:
            if rcParser.has_section(section) == False: # Whole section is missing. Probably a new install.
                globs.log.write(2, 'Adding RC section: [{}]'.format(section))
                rcParser.add_section(section)
                newRc=True
            if rcParser.has_option(section, option) == False: # Option is missing. Might be able to continue if non-critical.
                globs.log.write(2, 'Adding RC option: [{}] {}={}'.format(section, option, default))
                rcParser.set(section, option, default)
                if canCont == False:
                    newRc=True

        # save updated RC configuration to a file
        with open(rcName, 'w') as configfile:
            rcParser.write(configfile)
        return upgrade, newRc


    # Process command-line options
    def parseCommandLine(self):
        globs.log.write(1, 'Startup.parseCommandLine()')

        # Parse command line options with ArgParser library
        argParser = argparse.ArgumentParser(description='dupReport options.')

        argParser.add_argument("-r","--rcpath", help="Path to dupReport config file.", action="store")
        argParser.add_argument("-d","--dbpath", help="Path to dupReport database file.", action="store")
        argParser.add_argument("-v", "--verbose", help="Log file verbosity, 0-3. Same as [main]verbose= in rc file.", \
            type=int, action="store", choices=[0,1,2,3])
        argParser.add_argument("-V","--version", help="dupReport version and program info.", action="store_true")
        argParser.add_argument("-l","--logpath", help="Path to dupReport log file. (Default: 'dupReport.log'. Same as [main]logpath= in rc file.", action="store")
        argParser.add_argument("-a","--append", help="Append new logs to log file. Same as [main]logappend= in rc file.", action="store_true")
        argParser.add_argument("-m", "--mega", help="Convert file sizes to megabytes or gigabytes. Options are 'byte', 'mega' 'giga'. \
            Same as [main]sizereduce= in rc file.", action="store", choices=['mega','giga','byte'])
        argParser.add_argument("-i", "--initdb", help="Initialize database.", action="store_true")

        opGroup = argParser.add_mutually_exclusive_group()
        opGroup.add_argument("-c", "--collect", help="Collect new emails only. (Don't run report)", action="store_true")
        opGroup.add_argument("-t", "--report", help="Run summary report only. (Don't collect emails)", action="store_true")

        # Parse the arguments based on the argument definitions above.
        # Store results in 'args'
        args = argParser.parse_args()

        globs.log.write(3, 'Command line parsed. args=[{}]'.format(args))
        return args


    # Read .rc file options
    # Many command line options have .rc equivalents. 
    # Command line options take precedence over .rc file options
    # returns <restart>, <option list>
    # restart =   False if OK to continue
    # restart =  True if need to restart
    # Message = additional information
    def parseRcFile(self,rcPath, args):
        opts = {}
        restart = False

        globs.log.write(1, 'Startup.parseRcFile({})'.format(rcPath))
    
        try:
            rcConfig = SafeConfigParser()
            rv=rcConfig.read(rcPath)
        except configparser.ParsingError as err:
            globs.log.err('RC file parsing error: {}\n'.format(err.args[0]))
            globs.log.write(1, 'RC file parsing error: {}\n'.format(err.args[0]))
            return True, None, 'RC'  # Abort program. Can't continue with RC error

        # Extract sections and options from .rc file
        # Only need main, incoming, and outgoing sections
        # report and headings sections will be parsed when report object is initiated (report.py)
        for section in ('main', 'incoming', 'outgoing'):
            for name, value in rcConfig.items(section):
                opts[name] = value

        # Fix some of the datatypes
        opts['verbose'] = int(opts['verbose'])  # integer
        #opts['border'] = int(opts['border'])    # integer
        #opts['padding'] = int(opts['padding'])  # integer
        opts['inport'] = int(opts['inport'])    # integer
        opts['outport'] = int(opts['outport'])  # integer
        opts['logappend'] = opts['logappend'].lower() in ('true')   # boolean

        # Check for valid date format
        if opts['dateformat'] not in drdatetime.dtFmtDefs:
            globs.log.err('RC file error: Invalid date format: [{}]'.format(opts['dateformat']))
            restart = True

        # Check for valid time format
        if opts['timeformat'] not in drdatetime.dtFmtDefs:
            globs.log.err('RC file error: Invalid time format [{}]'.format(opts['timeformat']))
            restart = True

        # Now, override with command line options
        # Database Path - default stored in globs.dbName
        if args.dbpath != None:  #dbPath specified on command line
            opts['dbpath'] = '{}/{}'.format(args.dbpath, globs.dbName) 
        elif opts['dbpath'] == '':  # No command line & not specified in RC file
            opts['dbpath'] = '{}/{}'.format(getScriptPath(), globs.dbName)
        else:  # Path specified in rc file. Add dbname for full path
            opts['dbpath'] = '{}/{}'.format(opts['dbpath'], globs.dbName)

        # Log file path
        if args.logpath != None:  #logPath specified on command line
            opts['logpath'] = '{}/{}'.format(args.logpath, globs.logName)
        elif opts['logpath'] == '':  # No command line & not specified in RC file
            opts['logpath'] = '{}/{}'.format(getScriptPath, globs.logName)
        else:  # Path specified in rc file. Add dbname for full path
            opts['logpath'] = '{}/{}'.format(opts['logpath'], globs.logName)

        opts['rcpath'] = rcPath

        opts['version'] = args.version
        opts['collect'] = args.collect
        opts['report'] = args.report
        if args.verbose != None:            # Only override if specified on command line
            opts['verbose'] = args.verbose
        opts['logappend'] = args.append
        opts['initdb'] = args.initdb

        # Perform some basic RC file logic tests

        globs.log.write(3, 'Parsed config options=[{}]'.format(opts))
        return restart, opts

    # Master options initializer. Called by __main__
    # Returns True if OK to proceed
    # Returns False if need to restart program
    def initOptions(self):
        globs.log.write(1, 'Startup.initOptions()')

        # Start by parsing command line.
        # We're specifically looking for dbPath or rcPath.
        # We'll deal with the rest later.
        cmdLineArgs = self.parseCommandLine()

        # Get operating parameters from .rc file, overlay with command line options
        if cmdLineArgs.rcpath:  # RC Path specified on command line
            globs.log.write(2, 'RC path specified on command line')
            rc = '{}/{}'.format(cmdLineArgs.rcpath, globs.rcName)
        else: # RC path not specified on command line. use default location
            globs.log.write(2, 'RC path not specified on command line. Using default.'.format(getScriptPath()))
            rc = '{}/{}'.format(getScriptPath(), globs.rcName)
        globs.opts['rcpath'] = rc
        globs.log.write(3, 'RC path=[{}]'.format(globs.opts['rcpath']))

        needToExit=False   # Will be true if rc file or db file needs changing
        # Check RC file structure. Add sections/options as necessary
        restart, newRc = self.rcInitialize(rc)
        if restart:
            globs.log.err('RC file {} is out of date. Need to run dupUpgrade.py program to update config files.'.format(rc))
            needToExit = True
        elif newRc:
            globs.log.err('RC file {} has changed. Plese edit file with proper configuration, then re-run program'.format(rc))
            needToExit = True
        
        # RC file is structurally correct. Now need to parse config options for global use. 
        # Assign resulting congfig options to global variable so they can be accesses everywhere
        if not needToExit:
            restart, globs.opts = self.parseRcFile(rc, cmdLineArgs)
            if restart:
                globs.log.err('Structural problem with RC file {} has changed. Plese edit file with proper configuration, then re-run program'.format(rc))
                needToExit = True

        # Next, let's check if the DB exists or needs initializing
        # Either db file does not yet exist or forced db initialization
        if not needToExit:
            if ((os.path.isfile(globs.opts['dbpath']) is not True) or (globs.opts['initdb'] is True)):
                globs.log.write(1, 'Database {} needs initializing.'.format(globs.opts['dbpath']))
                globs.db = db.Database(globs.opts['dbpath'])
                globs.db.dbInitialize()
                globs.log.write(1, 'Database {} initialized. Continue processing.'.format(globs.opts['dbpath']))
                needToExit=False
            else:   # Check for DB version
                globs.db = db.Database(globs.opts['dbpath'])
                maj, min, sub = globs.db.currentVersion()
                currVerNum = (maj * 100) + (min * 10) + sub
                newVerNum = (globs.dbVersion[0] * 100) + (globs.dbVersion[1] * 10) + globs.dbVersion[2]
                if currVerNum < newVerNum:
                    globs.log.err('Database file RC file {} is out of date. Need to run dupUpgrade.py program to update database.'.format(globs.opts['dbpath']))
                    needToExit = True
            globs.db.dbClose()

        globs.report = report.Report()
        
        if needToExit:
            globs.log.write(1, 'Program initialization complete. Need to exit.')
        else:      
            globs.log.write(1, 'Program initialization complete. Continuing program.')

        return needToExit

