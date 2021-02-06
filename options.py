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
from getpass import getpass

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
    # [0] Section   [1] Option          [2] Default                                                                 [3]is the default value acceptable                  [4] Message to print on what went wrong
    #                                                                                                               if not already present in .rc file (true/false)?

    # [main] section defaults
    ('main',        'rcversion',        '{}.{}.{}'.format(globs.rcVersion[0],globs.rcVersion[1],globs.rcVersion[2]),True),
    ('main',        'dbpath',           os.path.dirname(os.path.realpath(sys.argv[0])),                             True),
    ('main',        'logpath',          os.path.dirname(os.path.realpath(sys.argv[0])),                             True),
    ('main',        'verbose',          '5',                                                           True),
    ('main',        'logappend',        'false',                                                                    True),
    ('main',        'subjectregex',     '^Duplicati Backup report for',                                             True),
    ('main',        'srcregex',         '\w*',                                                                      True),
    ('main',        'destregex',        '\w*',                                                                      True),
    ('main',        'srcdestdelimiter', '-',                                                                        True),
    ('main',        'dateformat',       'MM/DD/YYYY',                                                               False),
    ('main',        'timeformat',       'HH:MM:SS',                                                                 False),
    ('main',        'warnoncollect',    'false',                                                                    True),
    ('main',        'applyutcoffset',   'true',                                                                     True),
    ('main',        'show24hourtime',   'true',                                                                     True),
    ('main',        'purgedb',          'false',                                                                    True),
    ('main',        'showprogress',     '0',                                                                        True),
    ('main',        'masksensitive',    'true',                                                                     True),
    ('main',        'emailservers',     'incoming, outgoing',                                                       True),
    ('main',        'syslog',           '',                                                                         True),
    ('main',        'sysloglevel',      '5',                                                                        True),
    
    # [incoming] section defaults
    ('incoming',    'protocol',       'imap',                                                                       False),
    ('incoming',    'server',         'localhost',                                                                  False),
    ('incoming',    'port',           '993',                                                                        False),
    ('incoming',    'encryption',     'tls',                                                                        False),
    ('incoming',    'account',        'someacct@hostmail.com',                                                      False),
    ('incoming',    'password',       '********',                                                                   False),
    ('incoming',    'folder',         'INBOX',                                                                      False),
    ('incoming',    'keepalive',      'false',                                                                      True),
    ('incoming',    'unreadonly',     'false',                                                                      True),
    ('incoming',    'markread',       'false',                                                                      True),
    ('incoming',    'authentication', 'basic',                                                                      True),

    # [outgoing] section defaults
    ('incoming',    'protocol',      'smtp',                                                                        False),
    ('outgoing',    'server',        'localhost',                                                                   False),
    ('outgoing',    'port',          '587',                                                                         False),
    ('outgoing',    'encryption',    'tls',                                                                         False),
    ('outgoing',    'account',       'someacct@hostmail.com',                                                       False),
    ('outgoing',    'password',      '********',                                                                    False),
    ('outgoing',    'keepalive',     'false',                                                                       True),
    ('outgoing',    'sender',        'sender@hostmail.com',                                                         False),
    ('outgoing',    'sendername',    'Email Sender',                                                                False),
    ('outgoing',    'receiver',      'receiver@hostmail.com',                                                       False),
    ('outgoing',    'authentication','basic',                                                                       True),

    # [report] section defaults
    ('report',      'layout',           'srcdest, noactivity, lastseen',                                            True),
    ('report',      'columns',           'source:Source, destination:Destination, date:Date, time:Time, duration:Duration, dupversion:Version, examinedFiles:Files, examinedFilesDelta:+/-, sizeOfExaminedFiles:Size, fileSizeDelta:+/-, addedFiles:Added, deletedFiles:Deleted, modifiedFiles:Modified, filesWithError:File Errors, parsedResult:Result, messages:Messages, warnings:Warnings, errors:Errors, logdata:Log Data', True),
    ('report',      'title',            'Duplicati Backup Summary Report',                                          True),
    ('report',      'titlebg',          '#FFFFFF',                                                                  True),
    ('report',      'border',           '1',                                                                        True),
    ('report',      'padding',          '5',                                                                        True),
    ('report',      'sizedisplay',      'byte',                                                                     True),
    ('report',      'repeatcolumntitles', 'true',                                                                   True),
    ('report',      'suppresscolumntitles', 'false',                                                                 True),
    ('report',      'durationzeroes',   'true',                                                                     True),
    ('report',      'displaymessages',  'false',                                                                    True),
    ('report',      'jobmessagebg',     '#FFFFFF',                                                                  True),
    ('report',      'displaywarnings',  'true',                                                                     True),
    ('report',      'jobwarningbg',     '#FFFF00',                                                                  True),
    ('report',      'displayerrors',    'true',                                                                     True),
    ('report',      'joberrorbg',       '#FF0000',                                                                  True),
    ('report',      'displaylogdata',   'true',                                                                     True),
    ('report',      'truncatemessage',  '0',                                                                        True),
    ('report',      'truncatewarning',  '0',                                                                        True),
    ('report',      'truncateerror',    '0',                                                                        True),
    ('report',      'truncatelogdata',  '0',                                                                        True),
    ('report',      'joblogdatabg',     '#FF0000',                                                                  True),
    ('report',      'nobackupwarn',     '0',                                                                        True),
    ('report',      'nbwsubject',       'Backup Warning: #SOURCE##DELIMITER##DESTINATION# Backup Not Seen for #DAYS# Days', True),
    ('report',      'groupheadingbg',   '#D3D3D3',                                                                  True),
    ('report',      'normaldays',       '5',                                                                        True),
    ('report',      'normalbg',         '#FFFFFF',                                                                  True),
    ('report',      'warningdays',      '20',                                                                       True),
    ('report',      'warningbg',        '#FFFF00',                                                                  True),
    ('report',      'errorbg',          '#FF0000',                                                                  True),
    ('report',      'weminline',        'false',                                                                    True),
    ('report',      'includeruntime',   'true',                                                                     True),
    ('report',      'failedonly',       'False',                                                                    True),
    ('report',      'showoffline',      'False',                                                                     True),

    # [srcdest] sample specification
    ('srcdest',     'type',             'report',                                                                   True),
    ('srcdest',     'title',            'Duplicati Backup Summary Report - By Source/Destination',                  True),
    ('srcdest',     'groupby',          'source:ascending, destination:ascending',                                  True),
    ('srcdest',     'groupheading',     'Source: #SOURCE# - Destination: #DESTINATION#',                            True),
    ('srcdest',     'columns',          'date:Date, time:Time, dupversion:Version, duration:Duration, examinedFiles:Files, examinedFilesDelta:+/-, sizeOfExaminedFiles:Size, fileSizeDelta:+/-, addedFiles:Added, deletedFiles:Deleted, modifiedFiles:Modified, parsedResult:Result, messages:Messages, warnings:Warnings, errors:Errors, logdata:Log Data', True),
    ('srcdest',     'columnsort',       'date:ascending, time:ascending',                                           True),

    # [bysrc] sample specification
    ('bysrc',     'type',               'report',                                                                   True),
    ('bysrc',     'title',              'Duplicati Backup Summary Report - By Source',                              True),
    ('bysrc',     'groupby',            'source : ascending',                                                       True),
    ('bysrc',     'groupheading',       'Source: #SOURCE#',                                                         True),
    ('bysrc',     'columns',            'destination:Destiation, date:Date, time:Time, dupversion:Version, duration:Duration, examinedFiles:Files, examinedFilesDelta:+/-, sizeOfExaminedFiles:Size, fileSizeDelta:+/-, addedFiles:Added, deletedFiles:Deleted, modifiedFiles:Modified, parsedResult:Result, messages:Messages, warnings:Warnings, errors:Errors, logdata:Log Data', True),
    ('bysrc',     'columnsort',         'destination:ascending, date:ascending, time:ascending',                    True),

    # [bydest] sample specification
    ('bydest',     'type',             'report',                                                                    True),
    ('bydest',     'title',            'Duplicati Backup Summary Report - By Destination',                          True),
    ('bydest',     'groupby',          'destination:ascending',                                                     True),
    ('bydest',     'groupheading',     'Destination: #DESTINATION#',                                                     True),
    ('bydest',     'columns',          'source:Source, date:Date, time:Time, dupversion:Version, duration:Duration, examinedFiles:Files, examinedFilesDelta:+/-, sizeOfExaminedFiles:Size, fileSizeDelta:+/-, addedFiles:Added, deletedFiles:Deleted, modifiedFiles:Modified, parsedResult:Result, messages:Messages, warnings:Warnings, errors:Errors, logdata:Log Data', True),
    ('bydest',     'columnsort',       'source:ascending, date:ascending, time:ascending',                          True),

    # [bydate] sample specification
    ('bydate',     'type',             'report',                                                                    True),
    ('bydate',     'title',            'Duplicati Backup Summary Report - By Date',                                 True),
    ('bydate',     'groupby',          'date:ascending',                                                            True),
    ('bydate',     'groupheading',     'Date: #DATE#',                                                              True),
    ('bydate',     'columns',          'time:Time, source:Source, destination:Destination, dupversion:Version, duration:Duration, examinedFiles:Files, examinedFilesDelta:+/-, sizeOfExaminedFiles:Size, fileSizeDelta:+/-, addedFiles:Added, deletedFiles:Deleted, modifiedFiles:Modified, parsedResult:Result, messages:Messages, warnings:Warnings, errors:Errors, logdata:Log Data', True),
    ('bydate',     'columnsort',       'time:ascending',                                                            True),

    # No activity & last seen reports
    ('noactivity', 'type',              'noactivity',                                                               True),
    ('noactivity', 'title',             'Non-Activity Report',                                                      True),
    ('lastseen',   'type',              'lastseen',                                                                 True),
    ('lastseen',   'title',             'Backup Sets Last Seen',                                                    True),

    # Default apprise section
    ('apprise',    'enabled',           'false',                                                                    True),
    ('apprise',    'services',          '',                                                                         True),
    ('apprise',    'bodytruncate',      '0',                                                                        True),
    ('apprise',    'msglevel',          'warning',                                                                  True),
    ('apprise',    'body',              'Completed at #COMPLETETIME#: #RESULT# - Warning: #WARNMSG# Error: #ERRMSG#',   True)
    ]

# Class to manage all program options
class OptionManager:
    rcFileName = None   # Path to.rc file
    parser = None       # Handle for SafeConfigParser
    cmdLineArgs = None  # Command line arguments, passed from parse_args()
    needGuidedSetup = False
    options = {}        # List of all available program options

    def __init__(self):
        globs.log.write(globs.SEV_NOTICE, function='Options', action='OptionManager', msg='Initializing option manager.')
        return None

    # Determine if masking is required based on value of command line option
    # Only needed until RC file is processed. After that the options[] list will determine if need to mask
    def maskPath(self):
        mask = True
        if self.cmdLineArgs.nomasksensitive:
            mask = False
        return mask
   
    def openRcFile(self, rcFileSpec):
        globs.log.write(globs.SEV_NOTICE, function='Options', action='openRcFile', msg='Opening .rc file {}'.format(globs.maskData(rcFileSpec, self.maskPath())))
        if self.rcFileName:     # Rc file already initiailzed. Something is wrong.
            globs.log.write(globs.SEV_NOTICE, function='Options', action='openRcFile', msg='RC file {} already initialized. {} is a duplicate request.'.format(self.rcFileName, globs.maskData(rcFileSpec, self.maskPath())))
            return False
        try:
            self.parser = configparser.SafeConfigParser(interpolation=None)
            self.parser.read(rcFileSpec)
        except configparser.ParsingError as err:
            globs.log.write(globs.SEV_ERROR, function='Options', action='openRcFile', msg='RC file parsing error: {} {}\n'.format(globs.maskData(rcFileSpec, self.maskPath()), err))
            return False

        self.rcFileName = rcFileSpec    # Store RC file path
        return True

    # Check if need to upgrade RC file version
    # Returns True if need to upgrade RC file, False if at current version
    def checkRcFileVersion(self):
        needToUpgrade = False   # Assume .rc file is up to date
        currVerNum = 0

        # Get current RC version, if available. 
        if self.parser.has_option('main','version'):        # Old rc version name (pre-v2.2.7)
            rcVersion = self.parser.get('main','version')
        elif self.parser.has_option('main','rcversion'):    # New rc version name (post-v2.2.7)
            rcVersion = self.parser.get('main','rcversion')
        else:
            # Current RC version not available. Using a really old version of the program, so need to upgrade
            needToUpgrade = True

        # Got the RC version, not see if it's the current one
        if needToUpgrade == False:
            verParts = rcVersion.split('.')
            currVerNum = (int(verParts[0]) * 100) + (int(verParts[1]) * 10) + int(verParts[2])
            # Split RC version into component parts
            newVerNum = (globs.rcVersion[0] * 100) + (globs.rcVersion[1] * 10) + globs.rcVersion[2]
            globs.log.write(globs.SEV_DEBUG, function='Options', action='checkRcFileVersion', msg='RC file versions: current={} new={}.'.format(currVerNum, newVerNum))
            if currVerNum < newVerNum: # .rc file need an upgrade
                needToUpgrade = True

        globs.log.write(globs.SEV_NOTICE, function='Options', action='checkRcFileVersion', msg='Current version number={}. Need to upgrade rc file? {}'.format(currVerNum, needToUpgrade))
        return needToUpgrade, currVerNum

    # See if RC file has all the parts needed before proceeding with the rest of the program
    # Returns <status>, <newRC>
    # 
    # <newRC> = True if enough RC info has changed to require user config & restart
    # <newRC> = False if program can continue without restart
    def setRcDefaults(self):
        globs.log.write(globs.SEV_NOTICE, function='Options', action='setRcDefaults', msg='Setting .rc file defaults')
        errlist = []

        if not self.parser:
            globs.log.write(globs.SEV_NOTICE, function='Options', action='setRcDefaults', msg='RC file not yet opened. Can not set defaults.')
            return False

        defaultsOK = True       # Is the file configuration OK?
        needUpdate = False      # Do we need to update/refresh the file

        # Loop through all the required parts of the RC file. If not there, add them
        # First, check the emailserver option to see if it is there. If so, do not set [incoming] and [outgoing] sections
        hasEmailServers = self.parser.has_option('main','emailservers')

        for section, option, default, canCont in rcParts:
            if section in ['incoming', 'outgoing'] and hasEmailServers == True:   # No need to default email servers
                continue
            
            if not self.parser.has_section(section): # Whole section is missing.
                globs.log.write(globs.SEV_DEBUG, function='Options', action='setRcDefaults', msg='Adding RC section: [{}]'.format(section))
                self.parser.add_section(section)
                needUpdate = True

            if not self.parser.has_option(section, option): # Option is missing. Might be able to continue if non-critical.
                globs.log.write(globs.SEV_DEBUG, function='Options', action='setRcDefaults', msg='Adding RC option: [{}] {}={}'.format(section, option, default))
                self.parser.set(section, option, default)
                needUpdate = True
                if canCont == False:
                    errlist.append('[{}]{}={} option added. Please update with valid information.\n'.format(section, option, default))
                    defaultsOK = False

        globs.log.write(globs.SEV_NOTICE, function='Options', action='setRcDefaults', msg='needUpdate = {} defaultsOK={}'.format(needUpdate, defaultsOK))

        if self.needGuidedSetup:
            globs.log.write(globs.SEV_NOTICE, function='Options', action='setRcDefaults', msg='Running guided setup.')
            guidedSetupOptions = self.guidedSetup()
            globs.log.write(globs.SEV_NOTICE, function='Options', action='setRcDefaults', msg='Updating guided setup options.')
            for section in guidedSetupOptions.keys():
                for option in guidedSetupOptions[section]:
                    self.parser.set(section, option, guidedSetupOptions[section][option])
            defaultsOK = True

        if needUpdate or self.needGuidedSetup:
            self.updateRc()
        if not defaultsOK:
            globs.log.err('Errors found in .rc file.')
            for i in range(len(errlist)):
                globs.log.err(errlist[i])
                globs.log.write(globs.SEV_ERROR, function='Options', action='setRcDefaults', msg=errlist[i])
        return defaultsOK

    # Read .rc file options
    # Many command line options have .rc equivalents. 
    # Command line options take precedence over .rc file options
    # returns <restart>
    # restart =   False if OK to continue
    # restart =  True if need to restart
    def readRcOptions(self):
        globs.log.write(globs.SEV_NOTICE, function='Options', action='readRcOptions', msg='Reading .rc file options')
        restart = False

        # Extract sections and options from .rc file
        # Only need [main] section
        # [<email], [report] and associated sections will be parsed when email & report objects are initiated
        for name, value in self.parser.items('main'):
            self.options[name] = value

        # Fix some of the datatypes
        for item in ('verbose', 'showprogress', 'sysloglevel'):  # integers
            self.options[item] = int(self.options[item])

        for item in ('logappend', 'warnoncollect', 'applyutcoffset', 'show24hourtime', 'purgedb', 'masksensitive'):  # boolean
            self.options[item] = self.options[item].lower() in ('true')

        # Check for valid date format
        if self.options['dateformat'] not in drdatetime.dtFmtDefs:
            globs.log.write(globs.SEV_ERROR, function='Options', action='readRcOptions', msg='RC file error: Invalid date format: [{}]\n'.format(self.options['dateformat']))
            restart = True

        # Check for valid time format
        if self.options['timeformat'] not in drdatetime.dtFmtDefs:
            globs.log.write(globs.SEV_ERROR, function='Options', action='readRcOptions', msg='RC file error: Invalid time format [{}]\n'.format(self.options['timeformat']))
            restart = True

        # Set default path for RC file. Command line may override this.
        self.options['rcpath'] = globs.progPath + '/' + globs.rcName
        
        # Now, override with command line options
        # Database, rc file, and log file paths - default stored in globs.dbName
        configList = [  [self.cmdLineArgs.dbpath, 'dbpath', globs.dbName], 
                        [self.cmdLineArgs.rcpath, 'rcpath', globs.rcName], 
                        [self.cmdLineArgs.logpath, 'logpath', globs.logName]
                     ]

        for option, optName, globName in configList:
            if option != None:  # option specified on command line
                globs.log.write(globs.SEV_DEBUG, function='Options', action='readRcOptions', msg='Option {} specified on command line.'.format(optName))
                self.options[optName] = self.processPath(option, globName)
            elif optName in self.options and self.options[optName] == '':  # No command line & not specified in RC file. Use default path & filename
                self.options[optname] = self.processPath(globs.progPath, globName)
            else:  # Path specified in rc file. Add file name if necessary for full path
                self.options[optName] = self.processPath(self.options[optName], globName)

        # Mask Sensitive Data
        if self.cmdLineArgs.masksensitive: # Force sensitive data masking
            self.options['masksensitive'] = True
        elif self.cmdLineArgs.nomasksensitive: # Force sensitive data unmasking
            self.options['masksensitive'] = False

        self.options['version'] = self.cmdLineArgs.Version
        self.options['collect'] = self.cmdLineArgs.collect
        self.options['report'] = self.cmdLineArgs.report
        self.options['nomail'] = self.cmdLineArgs.nomail
        self.options['remove'] = self.cmdLineArgs.remove
        self.options['stopbackupwarn'] = self.cmdLineArgs.stopbackupwarn
        self.options['validatereport'] = self.cmdLineArgs.validatereport
        self.options['layout'] = self.cmdLineArgs.layout

        # Check rollback specifications
        self.options['rollback'] = self.cmdLineArgs.rollback
        self.options['rollbackx'] = self.cmdLineArgs.rollbackx
        # Check for valid rollback specifications
        # Can be specified as:
        # MM/DD/YYYY (or a valid variation) - roll back to beginning of specified day (00:00:00)
        # MM/DD/YYYY HH:MM:SS               - Roll back to specific date and time
        # Xs,Xm,Xh,Xd,Xw                    - Subtract X seconds, months, hours, days, weeks from current time (regardless of timestamps in DB)
        for rb in ['rollback', 'rollbackx']:
            if self.options[rb] != None: 
                if drdatetime.checkValidDateTimeSpec(self.options[rb], self.options['dateformat'], self.options['timeformat']) == False:
                    # It's not a standard date/time spec and not a timedelta spec
                    globs.log.write(globs.SEV_ERROR, function='Options', action='readRcOptions', msg='Invalid rollback date specification: {}.\n'.format(self.options[rb]))
                    globs.closeEverythingAndExit(1)

        # Misc command line arguments
        if self.cmdLineArgs.verbose != None:
            self.options['verbose'] = self.cmdLineArgs.verbose
        if self.cmdLineArgs.purgedb == True:
            self.options['purgedb'] = self.cmdLineArgs.purgedb
        if self.cmdLineArgs.append == True: # ONly override logappend if specified on the command line, else take whatever's in the rc file
            self.options['logappend'] = self.cmdLineArgs.append
        if self.cmdLineArgs.emailservers != None:
            self.options['emailservers'] = self.cmdLineArgs.emailservers
        self.options['initdb'] = self.cmdLineArgs.initdb
        
        # Store output files for later use
        # Create ofileList[] - list of output files
        # Consists of tuples of (<filespec>,<emailSpec>)
        # Filespec is "<filename,type>". <emailSpec> is True (attach file as email) or False (dont).
        globs.ofileList = []
        if self.cmdLineArgs.file:
            for spec in self.cmdLineArgs.file:
                globs.ofileList.append((spec, False))
        if self.cmdLineArgs.fileattach:
            for spec in self.cmdLineArgs.fileattach:
                globs.ofileList.append((spec, True))

        # Print config to log. Mask out appropriate data
        for opName in self.options:
            if opName in ('rcfilename', 'dbpath', 'logpath', 'inserver', 'inaccount', 'inpassword', 'outserver', 'outaccount', 'outpassword', 'outsender', 'outsendername', 'outreceiver'): # Mask sensitive data fields
                globs.log.write(globs.SEV_DEBUG, function='Options', action='readRcOptions', msg='Parsed config option [{}]=[{}]'.format(opName, globs.maskData(self.options[opName], self.options['masksensitive'])))
            else:
                globs.log.write(globs.SEV_DEBUG, function='Options', action='readRcOptions', msg='Parsed config option [{}]=[{}]'.format(opName, self.options[opName]))

        globs.log.write(globs.SEV_NOTICE, function='Options', action='readRcOptions', msg='Need to restart? {}'.format(restart))
        return restart


    # save updated RC configuration to .rc file
    def updateRc(self):
        globs.log.write(globs.SEV_NOTICE, function='Options', action='updateRc', msg='Updating .rc file')

        with open(self.rcFileName, 'w') as configfile:
            self.parser.write(configfile)
        return None

    # Get operating parameters from .rc file, overlay with command line options
    def processCmdLineArgs(self):
        globs.log.write(globs.SEV_NOTICE,  function='Options', action='processCmdLineArgs', msg='Processing command line arguments.')

        # Parse command line options with ArgParser library
        argParser = argparse.ArgumentParser(description='dupReport options.')

        argParser.add_argument("-a","--append", help="Append new logs to log file. Same as [main]logappend= in rc file.", action="store_true")
        argParser.add_argument("-b","--rollback", help="Roll back datebase to specified date. Format is -b <datetimespec>", action="store")
        argParser.add_argument("-B","--rollbackx", help="Roll back datebase to specified date, then exit program. Format is -b <datetimespec>", action="store")

        opGroup1 = argParser.add_mutually_exclusive_group()
        opGroup1.add_argument("-c", "--collect", help="Collect new emails only. (Don't run report)", action="store_true")
        opGroup1.add_argument("-t", "--report", help="Run summary report only. (Don't collect emails)", action="store_true")

        argParser.add_argument("-d","--dbpath", help="Path to dupReport database file.", action="store")
        argParser.add_argument("-e","--emailservers", help="List of incoming (IMAP & POP3) and outgoing (SMTP) servers to use.", action="store")
        argParser.add_argument("-f", "--file", help="Send output to file or stdout. Format is -f <filespec>,<type>", action="append")
        argParser.add_argument("-F", "--fileattach", help="Same as -f, but also send file as attchment.", action="append")

        opGroup2 = argParser.add_mutually_exclusive_group()
        opGroup2.add_argument("-g","--guidedsetup", help="Force program to re-run the guided setup for new users.", action="store_true")
        opGroup2.add_argument("-G","--noguidedsetup", help="Do not run guided setup even if there is no .rc file.", action="store_true")

        argParser.add_argument("-i","--initdb", help="Initialize database.", action="store_true")

        opGroup3 = argParser.add_mutually_exclusive_group()
        opGroup3.add_argument("-k", "--masksensitive", help="Mask sentitive data in log file. Overrides \"masksensitive\" option in rc file.", action="store_true")
        opGroup3.add_argument("-K", "--nomasksensitive", help="Don't mask sentitive data in log file. Overrides \"masksensitive\" option in rc file.", action="store_true")

        argParser.add_argument("-l","--logpath", help="Path to dupReport log file. (Default: 'dupReport.log'. Same as [main]logpath= in rc file.", action="store")
        argParser.add_argument("-m", "--remove", help="Remove a source/destination pair from the database. Format is -m <source> <destination>", nargs=2, action="store")
        argParser.add_argument("-o", "--validatereport", help="Validate the report options for accuracy then exit the program.", action="store_true")
        argParser.add_argument("-p", "--purgedb", help="Purge emails that are no longer on the server from the database. Same as [main]purgedb=true in rc file.", action="store_true")
        argParser.add_argument("-r","--rcpath", help="Path to dupReport config file.", action="store")
        argParser.add_argument("-s","--size", help="Convert file sizes to megabytes or gigabytes. Options are 'byte', 'mb' 'gb'. \
            Same as [report]sizedisplay= in rc file.", action="store", choices=['mb','gb','byte'])
        argParser.add_argument("-v", "--verbose", help="Log file verbosity, 0-7. Same as [main]verbose= in rc file.", \
            type=int, action="store", choices=[0,1,2,3,4,5,6,7])
        argParser.add_argument("-V","--Version", help="dupReport version and program info.", action="store_true")
        argParser.add_argument("-w", "--stopbackupwarn", help="Suppress sending of unseen backup warning emails. Overrides all \"nobackupwarn\" options in rc file.", action="store_true")
        argParser.add_argument("-x", "--nomail", help="Do not send email report. Typically used with -f", action="store_true")
        argParser.add_argument("-y", "--layout", help="Run the specified reports during the program run.", action="store")

        # Parse the arguments based on the argument definitions above.
        # Store results in 'args'
        try:
            self.cmdLineArgs = argParser.parse_args()
        except:
            e = sys.exc_info()[0]
            globs.log.write(globs.SEV_ERROR, function='Options', action='readRcOptions', msg='Argument parser error: {}'.format(e))
            globs.closeEverythingAndExit(1)

        globs.log.write(globs.SEV_NOTICE, function='Options', action='processCmdLineArgs', msg='rcpath = [{}]'.format(globs.maskData(self.cmdLineArgs.rcpath, True)))
        globs.log.write(globs.SEV_NOTICE, function='Options', action='processCmdLineArgs', msg='dbpath = [{}]'.format(globs.maskData(self.cmdLineArgs.dbpath, True)))
        globs.log.write(globs.SEV_NOTICE, function='Options', action='processCmdLineArgs', msg='logpath = [{}]'.format(globs.maskData(self.cmdLineArgs.logpath, True)))
        globs.log.write(globs.SEV_NOTICE, function='Options', action='processCmdLineArgs', msg='verbose = [{}]'.format(self.cmdLineArgs.verbose))
        globs.log.write(globs.SEV_NOTICE, function='Options', action='processCmdLineArgs', msg='Version = [{}]'.format(self.cmdLineArgs.Version))
        globs.log.write(globs.SEV_NOTICE, function='Options', action='processCmdLineArgs', msg='append = [{}]'.format(self.cmdLineArgs.append))
        globs.log.write(globs.SEV_NOTICE, function='Options', action='processCmdLineArgs', msg='size = [{}]'.format(self.cmdLineArgs.size))
        globs.log.write(globs.SEV_NOTICE, function='Options', action='processCmdLineArgs', msg='initdb = [{}]'.format(self.cmdLineArgs.initdb))
        globs.log.write(globs.SEV_NOTICE, function='Options', action='processCmdLineArgs', msg='rollback = [{}]'.format(self.cmdLineArgs.rollback))
        globs.log.write(globs.SEV_NOTICE, function='Options', action='processCmdLineArgs', msg='rollbackx = [{}]'.format(self.cmdLineArgs.rollbackx))
        globs.log.write(globs.SEV_NOTICE, function='Options', action='processCmdLineArgs', msg='file = [{}]'.format(self.cmdLineArgs.file))
        globs.log.write(globs.SEV_NOTICE, function='Options', action='processCmdLineArgs', msg='fileattach = [{}]'.format(self.cmdLineArgs.fileattach))
        globs.log.write(globs.SEV_NOTICE, function='Options', action='processCmdLineArgs', msg='guidedsetup= [{}]'.format(self.cmdLineArgs.guidedsetup))
        globs.log.write(globs.SEV_NOTICE, function='Options', action='processCmdLineArgs', msg='noguidedsetup= [{}]'.format(self.cmdLineArgs.noguidedsetup))
        globs.log.write(globs.SEV_NOTICE, function='Options', action='processCmdLineArgs', msg='nomail = [{}]'.format(self.cmdLineArgs.nomail))
        globs.log.write(globs.SEV_NOTICE, function='Options', action='processCmdLineArgs', msg='remove = [{}]'.format(self.cmdLineArgs.remove))
        globs.log.write(globs.SEV_NOTICE, function='Options', action='processCmdLineArgs', msg='purgedb = [{}]'.format(self.cmdLineArgs.purgedb))
        globs.log.write(globs.SEV_NOTICE, function='Options', action='processCmdLineArgs', msg='stopbackupwarn = [{}]'.format(self.cmdLineArgs.stopbackupwarn))
        globs.log.write(globs.SEV_NOTICE, function='Options', action='processCmdLineArgs', msg='collect = [{}]'.format(self.cmdLineArgs.collect))
        globs.log.write(globs.SEV_NOTICE, function='Options', action='processCmdLineArgs', msg='report = [{}]'.format(self.cmdLineArgs.report))
        globs.log.write(globs.SEV_NOTICE, function='Options', action='processCmdLineArgs', msg='masksensitive = [{}]'.format(self.cmdLineArgs.masksensitive))
        globs.log.write(globs.SEV_NOTICE, function='Options', action='processCmdLineArgs', msg='nomasksensitive = [{}]'.format(self.cmdLineArgs.nomasksensitive))
        globs.log.write(globs.SEV_NOTICE, function='Options', action='processCmdLineArgs', msg='validatereport = [{}]'.format(self.cmdLineArgs.validatereport))
        globs.log.write(globs.SEV_NOTICE, function='Options', action='processCmdLineArgs', msg='layout = [{}]'.format(self.cmdLineArgs.layout))
        globs.log.write(globs.SEV_NOTICE, function='Options', action='processCmdLineArgs', msg='emailservers = [{}]'.format(self.cmdLineArgs.emailservers))
    
        # Figure out where RC file is located
        if self.cmdLineArgs.rcpath is not None:  # RC Path specified on command line
            globs.log.write(globs.SEV_NOTICE, function='Options', action='processCmdLineArgs', msg='RC path specified on command line.')
            rc = self.cmdLineArgs.rcpath
            if os.path.isdir(rc): # directory specified only. Add default file name
                rc += '/{}'.format(globs.rcName)
        else: # RC path not specified on command line. use default location
            globs.log.write(globs.SEV_NOTICE, function='Options', action='processCmdLineArgs', msg='RC path not specified on command line. Using default.')
            rc = '{}/{}'.format(globs.progPath, globs.rcName)
        self.options['rcfilename'] = rc

        globs.log.write(globs.SEV_NOTICE, function='Options', action='processCmdLineArgs', msg='Final RC path=[{}]'.format(globs.maskData(self.options['rcfilename'], self.maskPath())))
        return None

    # Get individual .rc file option
    def getRcOption(self, section, option):
        globs.log.write(globs.SEV_NOTICE, function='Options', action='getRcOption', msg='Retrieving .rc option: [{}]{}='.format(section, option))
        if self.parser.has_option(section, option):
            return self.parser.get(section, option)
        else:
            return None

    # Set individual .rc file option
    def setRcOption(self, section, option, value):
        globs.log.write(globs.SEV_NOTICE, function='Options', action='setRcOption', msg='Setting .rc option: [{}]{}={}'.format(section, option, value))
        self.parser.set(section, option, value)
        return None

    # Clear individual option in .rc file
    def clearRcOption(self, section, option):
        globs.log.write(globs.SEV_NOTICE, function='Options', action='clearRcOption', msg='Deleting .rc option: [{}]{}='.format(section, option))
        self.parser.remove_option(section, option)
        return None

    # Add a new section to the .rc file
    def addRcSection(self, section):
        globs.log.write(globs.SEV_NOTICE, function='Options', action='addRcSection', msg='Adding .rc section: [{}]'.format(section))
        self.parser.add_section(section)
        return None

    def getRcSection(self, section):
        globs.log.write(globs.SEV_NOTICE, function='Options', action='getRcSection', msg='Retrieving .rc section: [{}]'.format(section))
        vals = {}

        if self.parser.has_section(section):
            # Read name/value pairs from section
            for name, value in self.parser.items(section):
                vals[name] = value
        else:
            vals = None
        return vals

    def hasSection(self, section):
        globs.log.write(globs.SEV_NOTICE, function='Options', action='hasSection', msg='Check if .rc file has [{}] section'.format(section))

        retval=False
        if self.parser.has_section(section):
            retval=True
        globs.log.write(globs.SEV_DEBUG, function='Options', action='hasSection', msg='Does section [{}] exist? {}'.format(section, retval))
        return retval


    def clearRcSection(self, section):
        globs.log.write(globs.SEV_DEBUG, function='Options', action='clearRcSection', msg='Deleting .rc section [{}]'.format(section))
        self.parser.remove_section(section)
        return None

    def getRcSectionDateTimeFmt(self, src, dest):
        globs.log.write(globs.SEV_DEBUG, function='Options', action='getRcSectionDateTimeFmt', msg='Getting Date/Time format for .rc section [{}{}{}]'.format(src, globs.opts['srcdestdelimiter'],dest))

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
                globs.log.write(globs.SEV_NOTICE, function='Options', action='getRcSectionDateTimeFmt', msg='Invalid date format in .rc file, [{}{}{}]: dateformat={}'.format(src, globs.opts['srcdestdelimiter'], dest, tmp))

        # Does [src-dest] timeformat= exist?
        if self.parser.has_option(section, 'timeformat'):
            tmp = self.parser.get(section, 'timeformat')
            if tmp in drdatetime.dtFmtDefs: # Is it a legal time format?
                tmfmt = tmp
            else:
                globs.log.write(globs.SEV_NOTICE, function='Options', action='getRcSectionDateTimeFmt', msg='Invalid time format in .rc file, [{}{}{}]: dateformat={}'.format(src, globs.opts['srcdestdelimiter'], dest, tmp))

        globs.log.write(globs.SEV_DEBUG, function='Options', action='getRcSectionDateTimeFmt', msg='Correct date format=[{}]  Correct time format=[{}]'.format(dtfmt, tmfmt))
        return dtfmt, tmfmt

    # Strips trailing slash character from a path specification if one exists
    def processPath(self, path, fName):
        basename = os.path.basename(path)
        dirname = os.path.dirname(path)
        isDir = os.path.isdir(path)

        if isDir:   # Path is clearly a directory (w/no file name component). Join it with the fName & return it
            joined = os.path.join(path, fName)
            return joined

        if path == '':  # no path, use the default path & join it with fName
            joined = os.path.join(globs.progPath, fName)
            return joined
        return path     #Assume it's a full filespec. Return it and the OS will raise an error if it tries to open it & can't


    # Guided Setup for New Users
    def guidedSetupHelper(self, prompt='', default='', secure = False, choices = None, convertUpper = False, convertLower=False):

        ready = False
        while not ready:
            if not secure:
                response = input('{} [{}]: '.format(prompt, default))
            else:
                response = getpass('{} [{}]: '.format(prompt, default))
            if response == '':
                response = default
            if convertUpper:
                response = str.upper(response)
            elif convertLower:
                response = str.lower(response)

            if choices == None:     # Loop until you get a correct input form the given choices
                break

            if response not in choices:
                print("Invalid response. Please try again.")
            else:
                ready = True
        return response
    
    def guidedSetup(self):
        globs.log.write(globs.SEV_NOTICE, function='Options', action='guidedSetup', msg='Running guided setup for .rc file')

        if not self.needGuidedSetup:
            globs.log.write(globs.SEV_NOTICE, function='Options', action='guidedSetup', msg='Guided setup not required.')
            return None

        options = {'main': {}, 'report': {}, 'incoming': {}, 'outgoing': {}}

        print("Welcome to the dupReport guided setup.")
        print("Here we'll collect some basic information from you to help configure the program.")
        print("Let's get started...\n")
        
        # Date format
        print("Valid date formats in dupReport are:")
        for key in drdatetime.dtFmtDefs.keys():
            if key != 'HH:MM:SS':
                print('\t{}'.format(key))
        options['main']['dateformat'] = self.guidedSetupHelper(prompt='Please enter the date format for your locale', default='MM/DD/YYYY', choices=drdatetime.dtFmtDefs.keys(), convertUpper=True)
        usesyslog = self.guidedSetupHelper(prompt='Do you use a syslog server or log aggregator where you want the dupReport logs sent', default='n', choices=['y','n'], convertLower=True)
        if usesyslog == 'y':
            options['main']['syslog'] = self.guidedSetupHelper(prompt='Enter the server name/ip and port of your syslog server', default='localhost:514')
        else:
            options['main']['syslog'] = ''

        options['report']['sizedisplay'] = self.guidedSetupHelper(prompt='Do you want file sizes displayed in bytes, megabytes, or gigabytes (enter \'byte\', \'mb\', or \'gb\')', default='byte', choices=['byte','mb', 'gb'], convertLower=True)

        # Incoming mail server
        print("\nNow we'll need information about your \'incoming\' email server.")
        print("This is the email server where your Duplicati job results are sent. dupReport will collect emails from this server and analyze them.")
        print("You can use more than one incoming server with dupReport, but for now we'll collect information for just one.")
        options['incoming']['protocol'] = self.guidedSetupHelper(prompt='Does the \'incoming\' server use IMAP or POP3', default='imap', choices=['imap','pop3'], convertLower=True)
        options['incoming']['server'] = self.guidedSetupHelper(prompt='Please provide an IP address or DNS name for the \'incoming\' server', default='localhost')
        options['incoming']['port'] = self.guidedSetupHelper(prompt='Please provide a port number for the \'incoming\' server', default='993')
        if self.guidedSetupHelper(prompt='Does the \'incoming\' server use SSL/TLS encryption', default='Y', choices=['Y','N'], convertUpper=True) == 'Y':
            options['incoming']['encryption'] = 'tls'
        else:
            options['incoming']['encryption'] = 'none'
        options['incoming']['account'] = self.guidedSetupHelper(prompt='Please enter the user ID used to log into the \'incoming\' server', default='youremail@emailservice.com')
        options['incoming']['password'] = self.guidedSetupHelper(prompt='Please enter the password used to log into the \'incoming\' server', default='secretpassword', secure=True)
        options['incoming']['folder'] = ''
        if options['incoming']['protocol'] == 'imap':
            options['incoming']['folder'] = self.guidedSetupHelper(prompt='Please enter the IMAP folder name to where Duplicati emails are stored on the \'incoming\' server', default='Inbox')

        # Outgoing mail server
        print("\nNow we'll need information about your \'outgoing\' email server.")
        print("This is the email server that dupReport will use to send the results of its analysis.")
        print("You can use more than one outgoing server with dupReport, but for now we'll collect information for just one.")
        options['outgoing']['protocol'] = 'smtp'
        options['outgoing']['server'] = self.guidedSetupHelper(prompt='Please provide an IP address or DNS name for the \'outgoing\' server', default='localhost')
        options['outgoing']['port'] = self.guidedSetupHelper(prompt='Please provide a port number for the \'outgoing\' server', default='587')
        if self.guidedSetupHelper(prompt='Does the \'outgoing\' server use SSL/TLS encryption', default='Y', choices=['Y','N'], convertUpper=True) == 'Y':
            options['outgoing']['encryption'] = 'tls'
        else:
            options['outgoing']['encryption'] = 'none'
        options['outgoing']['account'] = self.guidedSetupHelper(prompt='Please enter the user ID used to log into the \'outgoing\' server', default='youremail@emailservice.com')
        options['outgoing']['password'] = self.guidedSetupHelper(prompt='Please enter the password used to log into the \'outgoing\' server', default='secretpassword', secure=True)
        options['outgoing']['sender'] = self.guidedSetupHelper(prompt='What email address should be used for the sender', default='youremail@emailservice.com')
        options['outgoing']['sendername'] = self.guidedSetupHelper(prompt='What is the \'friendly name\' of the outgoing email sender', default='Your Name')
        options['outgoing']['receiver'] = self.guidedSetupHelper(prompt='Who should the outgoing emails be sent to', default='receiver@emailservice.com')


        print("\nOK, all set. We've recorded your responses and (hopefully) the program will work perfectly now.")
        print('If it doesn\'t, you can change the configuration in the .rc file located at {}\n'.format(self.rcFileName))

        return options


# Initialize options in the program
# Return True if program can continue
# Return False if enough changed in the .rc file that program needs to stop
def initOptions():
    globs.log.write(globs.SEV_NOTICE, function='Options', action='initOptions', msg='Initializing global program options.')

    # Create OptionManager instance
    oMgr = OptionManager()

    # Parse command line options
    oMgr.processCmdLineArgs()
    if oMgr.cmdLineArgs.guidedsetup:
        oMgr.needGuidedSetup = True

    # Prepare the .rc file for processing
    oMgr.openRcFile(oMgr.options['rcfilename'])   
    
    # Check if .rc file needs upgrading
    needToUpgrade, currRcVersion = oMgr.checkRcFileVersion()
    if needToUpgrade is True and os.path.isfile(oMgr.options['rcfilename']):
        globs.log.write(globs.SEV_NOTICE, function='Options', action='initOptions', msg='RC file is out of date. Needs update from version {} to version {}{}{}.'.format(currRcVersion, globs.rcVersion[0], globs.rcVersion[1], globs.rcVersion[2]))
        import convert
        convert.convertRc(oMgr, currRcVersion)
        globs.log.write(globs.SEV_NOTICE, function='Options', action='initOptions', msg='RC file has been updated to the latest version.')
    
    # If the current .rc version is 0 there is no .rc file. Flag need to run guided setup (unless explicitly told not to)
    if currRcVersion == 0 and not oMgr.cmdLineArgs.noguidedsetup:
        oMgr.needGuidedSetup = True
    
        # Check .rc file structure to see if all proper fields are there. If False, something needs attention.
    if oMgr.setRcDefaults() is False:
        globs.log.write(globs.SEV_NOTICE, function='Options', action='initOptions', msg='RC file {} has changed or has an unrecoverable error. Please edit file with proper configuration, then re-run program'.format(oMgr.options['rcfilename']))
        return False

    # RC file is structurally correct. Now need to parse rc options for global use. 
    if oMgr.readRcOptions() is True:  # Need to restart program (.rc file needs editing)
        return False

    # Set global variables for OptionManager and program options
    # A bit "un-pure', but makes programming much easier
    globs.optionManager = oMgr
    globs.opts = oMgr.options

   # If output files are specified on the command line (-f), make sure their specification is correct
    if validateOutputFiles() is False:
        return False

    globs.log.write(globs.SEV_NOTICE, function='Options', action='initOptions', msg='Option initialization complete. Continuing program.')
    return True

# Determine if output files specified on command line (-f or -F) have proper format spec
# Specification is -f <file>,<format>
# <format> can be 'html', 'txt', or 'csv'
def validateOutputFiles():
    canContinue = True

    # See where the output files are going
    if globs.ofileList:    # Potential list of output files specified on command line
        for fspec in globs.ofileList:
            fsplit = fspec[0].split(',')   
            if len(fsplit) != 2:
                globs.log.write(globs.SEV_NOTICE, function='Options', action='validateOutputFiles', msg='Invalid output file specificaton: {}. Correct format is <filespec>,<format>. Please check your command line parameters.'.format(fsplit))
                canContinue = False
            elif fsplit[1] not in ('html','txt', 'csv', 'json'):
                globs.log.write(globs.SEV_NOTICE, function='Options', action='validateOutputFiles', msg='Output file {}: Invalid output file format specificaton: {}. Please check your command line parameters.'.format(fsplit[0], fsplit[1]))
                canContinue = False

    return canContinue

