#####
#
# Module name:  options.py
# Purpose:      Manage program options from command line & .rc file
# 
# Notes:
#
#####

# Import Python modules
import configparser
from configparser import SafeConfigParser 
import argparse
import os
import sys

# Import dupreport modules
import log
import drdatetime
import globs

# rcParts tuples
# 1 - section name
# 2 - option name
# 3 - default value
# 4 - is the default value acceptable if not already present in .rc file (true/false)?
rcParts= [
    # [main] section defaults
    ('main','version','{}.{}.{}'.format(globs.version[0],globs.version[1],globs.version[2]), True),
    ('main','dbpath',os.path.dirname(os.path.realpath(sys.argv[0])), True),
    ('main','logpath',os.path.dirname(os.path.realpath(sys.argv[0])), True),
    ('main','verbose','1', True),
    ('main','logappend','false', True),
    ('main','subjectregex','^Duplicati Backup report for', True),
    ('main','srcregex','\w*', True),
    ('main','destregex','\w*', True),
    ('main','srcdestdelimiter','-', True),
    ('main','dateformat', 'MM/DD/YYYY', False),
    ('main','timeformat','HH:MM:SS', False),
    ('main','warnoncollect','false', True),
    ('main','applyutcoffset','false', True),
    ('main','show24hourtime', 'true', True),
    
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
    ('report','style','srcdest', True),
    ('report','sortby','source', True),
    ('report','border','1', True),
    ('report','padding','5', True),
    ('report','reporttitle','Duplicati Backup Summary Report', True),
    ('report','sizedisplay','byte', True),
    ('report','showsizedisplay','true', True),
    ('report','displaymessages','false', True),
    ('report','displaywarnings','true', True),
    ('report','displayerrors','true', True),
    ('report','titlebg','#FFFFFF', True),
    ('report','subheadbg','#D3D3D3', True),
    ('report','noactivitybg','#FF0000', True),
    ('report','jobmessagebg','#FFFFFF', True),
    ('report','jobwarningbg','#FFFF00', True),
    ('report','joberrorbg','#FF0000', True),
    ('report','repeatheaders','false', True),
    ('report','nobackupwarn', '0', True),
    ('report','nbwsubject', 'Backup Warning: #SOURCE##DELIMITER##DESTINATION# Backup Not Seen for #DAYS# Days', True),

    # [headings] section defaults
    ('headings','Source','Source', True),
    ('headings','Destination','Destination', True),
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


# Class to manage all program options
class OptionManager:
    rcFileName = None   # Path to.rc file
    parser = None       # Handle for SafeConfigParser
    cmdLineArgs = None  # Command line arguments, passed from parse_args()
    options = {}        # List of all available program options

    def __init__(self):
        return None

    def openRcFile(self, rcFileSpec):
        globs.log.write(1,'options.openRcFile({})'.format(rcFileSpec))
        if self.rcFileName:     # Rc file already initiailzed. Something is wrong.
            globs.log.write(2, 'RC file {} already initialized. {} is a duplicate request.'.format(self.rcFileName, filespec))
            return False

        try:
            self.parser = configparser.SafeConfigParser()
            self.parser.read(rcFileSpec)
        except configparser.ParsingError as err:
            globs.log.err('RC file parsing error: {} {}\n'.format(rcFileSpec, err))
            globs.log.write(1, 'RC file parsing error: {} {}\n'.format(rcFileSpec, err))
            return False

        self.rcFileName = rcFileSpec
        return True

    # Check if need to upgrade RC file version
    # Returns True if need to upgrade RC file, False if at current version
    def checkRcFileVersion(self):
        globs.log.write(1,'options.checkRcFileVersion()')
        needToUpgrade = False
        currVerNum = 0
        # Get current RC version, if available. 
        if self.parser.has_option('main','version'):
            rcVersion = self.parser.get('main','version')
            verParts = rcVersion.split('.')
            currVerNum = (int(verParts[0]) * 100) + (int(verParts[1]) * 10) + int(verParts[2])
            # Split RC version into component parts
            newVerNum = (globs.version[0] * 100) + (globs.version[1] * 10) + globs.version[2]
            globs.log.write(3,'RC file versions: current={} new={}.'.format(currVerNum, newVerNum))
            if currVerNum < newVerNum: # Need an upgrade
                needToUpgrade = True
            else:   # current version is OK
                needToUpgrade = False
        else:
            # Current RC version not available. Using a really old version of the program, so need to upgrade
            needToUpgrade = True

        globs.log.write(1,'Current version number={}. Need to upgrade rc file? {}'.format(currVerNum, needToUpgrade))
        return needToUpgrade, currVerNum

    # See if RC file has all the parts needed before proceeding with the rest of the program
    # Returns <status>, <newRC>
    # 
    # <newRC> = True if enough RC info has changed to require user config & restart
    # <newRC> = False if program can continue without restart
    def setRcDefaults(self):
        globs.log.write(1,'options.setRcDefaults()')
        if not self.parser:
            globs.log.err('RC file not yet opened. Can not set defaults')
            return False

        globs.log.write(1, 'rc.setDefaults({})'.format(self.rcFileName))

        newRc = False
        # Loop through all the required parts of the RC file. If not there, add them
        for section, option, default, canCont in rcParts:
            if self.parser.has_section(section) == False: # Whole section is missing. Probably a new install.
                globs.log.write(2, 'Adding RC section: [{}]'.format(section))
                self.parser.add_section(section)
                newRc=True
            if self.parser.has_option(section, option) == False: # Option is missing. Might be able to continue if non-critical.
                globs.log.write(2, 'Adding RC option: [{}] {}={}'.format(section, option, default))
                self.parser.set(section, option, default)
                if canCont == False:
                    newRc=True

        self.updateRc()
        globs.log.write(3,'newRc={}'.format(newRc))
        return newRc

    # Read .rc file options
    # Many command line options have .rc equivalents. 
    # Command line options take precedence over .rc file options
    # returns <restart>
    # restart =   False if OK to continue
    # restart =  True if need to restart
    def readRcOptions(self):
        restart = False

        globs.log.write(1, 'options.readRcOptions({})'.format(self.rcFileName))
    
        # Extract sections and options from .rc file
        # Only need [main], [incoming], and [outgoing] sections
        # [report] and [headings] sections will be parsed when report object is initiated (report.py)
        for section in ('main', 'incoming', 'outgoing'):
            for name, value in self.parser.items(section):
                self.options[name] = value

        # Fix some of the datatypes
        self.options['verbose'] = int(self.options['verbose'])  # integer
        self.options['inport'] = int(self.options['inport'])    # integer
        self.options['outport'] = int(self.options['outport'])  # integer
        self.options['logappend'] = self.options['logappend'].lower() in ('true')   # boolean
        self.options['warnoncollect'] = self.options['warnoncollect'].lower() in ('true')   # boolean
        self.options['applyutcoffset'] = self.options['applyutcoffset'].lower() in ('true')   # boolean
        self.options['show24hourtime'] = self.options['show24hourtime'].lower() in ('true')   # boolean
        self.options['purgedb'] = self.options['purgedb'].lower() in ('true')   # boolean

        # Check for valid date format
        if self.options['dateformat'] not in drdatetime.dtFmtDefs:
            globs.log.err('RC file error: Invalid date format: [{}]'.format(self.options['dateformat']))
            restart = True

        # Check for valid time format
        if self.options['timeformat'] not in drdatetime.dtFmtDefs:
            globs.log.err('RC file error: Invalid time format [{}]'.format(self.options['timeformat']))
            restart = True

        # Now, override with command line options
        #
        # Database Path - default stored in globs.dbName
        if self.cmdLineArgs.dbpath != None:  # dbPath specified on command line
            self.options['dbpath'] = '{}/{}'.format(args.dbpath, globs.dbName) 
        elif self.options['dbpath'] == '':  # No command line & not specified in RC file
            self.options['dbpath'] = '{}/{}'.format(os.path.dirname(path, globs.rcName), globs.dbName)
        else:  # Path specified in rc file. Add dbname for full path
            self.options['dbpath'] = '{}/{}'.format(self.options['dbpath'], globs.dbName)

        # Log file path
        if self.cmdLineArgs.logpath != None:  #logPath specified on command line
            self.options['logpath'] = '{}/{}'.format(self.cmdLineArgs.logpath, globs.logName)
        elif self.options['logpath'] == '':  # No command line & not specified in RC file
            self.options['logpath'] = '{}/{}'.format(globs.progPath, globs.logName)
        else:  # Path specified in rc file. Add dbname for full path
            self.options['logpath'] = '{}/{}'.format(self.options['logpath'], globs.logName)

        self.options['version'] = self.cmdLineArgs.Version
        self.options['collect'] = self.cmdLineArgs.collect
        self.options['report'] = self.cmdLineArgs.report
        self.options['nomail'] = self.cmdLineArgs.nomail
        self.options['remove'] = self.cmdLineArgs.remove

        # Check rollback specifications
        self.options['rollback'] = self.cmdLineArgs.rollback
        if self.options['rollback']:
            ret = drdatetime.toTimestamp(self.options['rollback'], self.options['dateformat'], self.options['timeformat'])
            if not ret:
                globs.log.err('Invalid rollback date specification: {}.'.format(self.options['rollback']))
                restart = True

        if self.cmdLineArgs.verbose != None:
            self.options['verbose'] = self.cmdLineArgs.verbose
        if self.cmdLineArgs.purgedb == True:
            self.options['purgedb'] = self.cmdLineArgs.purgedb
        self.options['logappend'] = self.cmdLineArgs.append
        self.options['initdb'] = self.cmdLineArgs.initdb
        
        # Store output files for later use
        self.options['file'] = self.cmdLineArgs.file
        if self.options['file']:
            globs.ofileList = self.options['file']

        globs.log.write(3, 'Parsed config options=[{}]'.format(self.options))
        globs.log.write(1, 'Need to restart? {}'.format(restart))

        return restart


    # save updated RC configuration to .rc file
    def updateRc(self):
        globs.log.write(1, 'options.updateRc()')

        with open(self.rcFileName, 'w') as configfile:
            self.parser.write(configfile)
        return None

    # Get operating parameters from .rc file, overlay with command line options
    def processCmdLineArgs(self):

        globs.log.write(1, 'options.processCmdLineArgs()')

        # Parse command line options with ArgParser library
        argParser = argparse.ArgumentParser(description='dupReport options.')

        argParser.add_argument("-r","--rcpath", help="Path to dupReport config file.", action="store")
        argParser.add_argument("-d","--dbpath", help="Path to dupReport database file.", action="store")
        argParser.add_argument("-l","--logpath", help="Path to dupReport log file. (Default: 'dupReport.log'. Same as [main]logpath= in rc file.", action="store")
        argParser.add_argument("-v", "--verbose", help="Log file verbosity, 0-3. Same as [main]verbose= in rc file.", \
            type=int, action="store", choices=[0,1,2,3])
        argParser.add_argument("-V","--Version", help="dupReport version and program info.", action="store_true")
        argParser.add_argument("-a","--append", help="Append new logs to log file. Same as [main]logappend= in rc file.", action="store_true")
        argParser.add_argument("-s","--size", help="Convert file sizes to megabytes or gigabytes. Options are 'byte', 'mega' 'giga'. \
            Same as [main]sizedisplay= in rc file.", action="store", choices=['mega','giga','byte'])
        argParser.add_argument("-i","--initdb", help="Initialize database.", action="store_true")
        argParser.add_argument("-b","--rollback", help="Roll back datebase to specified date. Format is -b <datetimespec>", action="store")
        argParser.add_argument("-f", "--file", help="Send output to file or stdout. Format is -f <filespec>,<type>", action="append")
        argParser.add_argument("-x", "--nomail", help="Do not send email report. Typically used with -f", action="store_true")
        argParser.add_argument("-m", "--remove", help="Remove a source/destination pair from the database. Format is -m <source> <destination>", nargs=2, action="store")
        argParser.add_argument("-p", "--purgedb", help="Purge emails that are no longer on the server from the database. Same as [main]purgedb=true in rc file.", action="store_true")

        opGroup = argParser.add_mutually_exclusive_group()
        opGroup.add_argument("-c", "--collect", help="Collect new emails only. (Don't run report)", action="store_true")
        opGroup.add_argument("-t", "--report", help="Run summary report only. (Don't collect emails)", action="store_true")

        # Parse the arguments based on the argument definitions above.
        # Store results in 'args'
        self.cmdLineArgs = argParser.parse_args()

        globs.log.write(3, 'Command line parsed. args=[{}]'.format(self.cmdLineArgs))
        
        # Figure out whwre RC file is located
        if self.cmdLineArgs.rcpath is not None:  # RC Path specified on command line
            globs.log.write(2, 'RC path specified on command line')
            rc = '{}/{}'.format(self.cmdLineArgs.rcpath, globs.rcName)
        else: # RC path not specified on command line. use default location
            path = os.path.dirname(os.path.realpath(sys.argv[0]))
            globs.log.write(2, 'RC path not specified on command line. Using default.'.format(path))
            rc = '{}/{}'.format(path, globs.rcName)
        
        self.options['rcfilename'] = rc
        globs.log.write(3, 'RC path=[{}]'.format(self.options['rcfilename']))


    # Get individual .rc file option
    def getRcOption(self, section, option):
        globs.log.write(3, 'options.getRcOption({}, {})'.format(section, option))
        if self.parser.has_option(section, option):
            return self.parser.get(section, option)
        else:
            return None

    # Set individual .rc file option
    def setRcOption(self, section, option, value):
        globs.log.write(1, 'options.setRcOption({}, {}, {})'.format(section, option, value))
        self.parser.set(section, option, value)
        return None

    # Clear individual option in .rc file
    def clearRcOption(self, section, option):
        globs.log.write(1, 'options.clearRcOption({}, {})'.format(section, option))
        self.parser.remove_option(section, option)
        return None

    # Add a new section to the .rc file
    def addRcSection(self, section):
        globs.log.write(1, 'options.addRcSection({})'.format(section))
        self.parser.add_section(section)
        return None

    def getRcSection(self, section):
        globs.log.write(1, 'options.getRcSection({})'.format(section))
        vals = {}

        if self.parser.has_section(section):
            # Read name/value pairs from section
            for name, value in self.parser.items(section):
                vals[name] = value
        else:
            vals = None

        return vals

    def getRcSectionDateTimeFmt(self, src, dest):
        globs.log.write(1, 'options.getRcSectionDateTimeFmt({}, {})'.format(src, dest))

        # Set defaults to global options
        dtfmt = globs.opts['dateformat']
        tmfmt = globs.opts['timeformat']

        # Set name for section
        section = '{}{}{}'.format(src, globs.opts['srcdestdelimiter'],dest)

        # Does [src-dest] dateformat= exist?
        if self.parser.has_option(section, 'dateformat'):
            tmp = self.parser.get(section, 'dateformat')
            if tmp in drdatetime.dtFmtDefs: # Is it a legal date format?
                dtfmt = tmp
            else:
                globs.log.write(2, 'Invalid date format in .rc file, [{}{}{}]: dateformat={}'.format(src, globs.opts['srcdestdelimiter'], dest, tmp))

        # Does [src-dest] timeformat= exist?
        if self.parser.has_option(section, 'timeformat'):
            tmp = self.parser.get(section, 'timeformat')
            if tmp in drdatetime.dtFmtDefs: # Is it a legal time format?
                tmfmt = tmp
            else:
                globs.log.write(2, 'Invalid time format in .rc file, [{}{}{}]: dateformat={}'.format(src, globs.opts['srcdestdelimiter'], dest, tmp))

        return dtfmt, tmfmt
    