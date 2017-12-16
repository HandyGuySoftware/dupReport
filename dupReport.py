#!/usr/bin/env python3

######
#
# Program name: dupReport.py
# Purpose:      Print summary reports from Duplicati backup service
# Author:       Stephen Fried for Handy Guy Software
# Copyright:    2017, release under MIT license. See LICENSE file for details
# 
#####

# Import system modules
import time
import sys
import os

# Import dupReport modules
import globs
import db
import log
import report
import options
import dremail

# Print program verersion info
def versionInfo():
    globs.log.out('\n-----\ndupReport: A summary email report generator for Duplicati.')
    globs.log.out('Program Version {}.{}.{} {}'.format(globs.version[0], globs.version[1], globs.version[2], globs.status))
    globs.log.out('Database Version {}.{}.{}'.format(globs.dbVersion[0], globs.dbVersion[1], globs.dbVersion[2]))
    globs.log.out('{}'.format(globs.copyright))
    globs.log.out('Distributed under MIT License. See LICENSE file for details.')
    globs.log.out('\nFollow dupReport on Twitter @dupreport\n-----\n')
    return None

# Initialize options in the program
# Return True if program can continue
# Return False if enough changed in the .rc file that program needs to stop
def initOptions():
    globs.log.write(1, 'initOptions()')

    # Set program path

    # Create OptionManager instance
    oMgr = options.OptionManager()
    # Parse command line options
    globs.log.write(1,'Processing command line...')
    oMgr.processCmdLineArgs()
    # Prepare the .rc file for processing
    oMgr.openRcFile(oMgr.options['rcfilename'])   
    
    # Check if .rc file needs upgrading
    needToUpgrade, currRcVersion = oMgr.checkRcFileVersion()
    if needToUpgrade is True and os.path.isfile(oMgr.options['rcfilename']):
        globs.log.out('RC file {} is out of date. Needs update from version {} to version {}{}{}.'.format(oMgr.options['rcfilename'], currRcVersion, globs.version[0], globs.version[1], globs.version[2]))
        import convert
        convert.convertRc(oMgr, currRcVersion)
        globs.log.out('RC file {} has been updated to the latest version.'.format(oMgr.rcFileName))
    
    # Check .rc file structure to see if all proper fields are there
    if oMgr.setRcDefaults() is True:
        globs.log.out('RC file {} has changed. Plese edit file with proper configuration, then re-run program'.format(oMgr.options['rcfilename']))
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

    # Check if the DB exists or needs initializion
    # Check if either db file does not yet exist or forced db initialization
    globs.db = db.Database(globs.opts['dbpath'])
    if globs.opts['initdb'] is True:    
        # Forced initialization from command line
        globs.log.write(1, 'Database {} needs initializing.'.format(globs.opts['dbpath']))
        globs.db.dbInitialize()
        globs.log.write(1, 'Database {} initialized. Continue processing.'.format(globs.opts['dbpath']))
    else:   # Check for DB version
        needToUpgrade, currDbVersion = globs.db.checkDbVersion()
        if needToUpgrade is True:
            import convert
            globs.log.out('Need to upgrade database {} from version {} to version {}{}{}'.format(globs.opts['dbpath'], currDbVersion, globs.dbVersion[0], globs.dbVersion[1], globs.dbVersion[2]))
            convert.convertDb(currDbVersion)
            globs.db.dbClose()
            globs.log.out('Database file {} has been updated to the latest version.'.format(globs.opts['dbpath']))

    globs.db.dbClose() # Done with DB for now. We'll reopen it properly later.
    globs.log.write(1, 'Program initialization complete. Continuing program.')

    return True

# Determine if output files specified on command line (-f or -F) have proper format spec
# Specification is -f <file>,<format>
# <format> can be 'html', 'txt', or 'csv'
def validateOutputFiles():
    canContinue = True

    # See where the output files are going
    if globs.ofileList:    # Potential list of output files specified on command line
        for fspec in globs.ofileList:
            fsplit = fspec.split(',')   
            if len(fsplit) != 2:
                globs.log.err('Invalid output file specificaton: {}. Correct format is <filespec>,<format>. Please check your command line parameters.'.format(fsplit))
                canContinue = False
            elif fsplit[1] not in ('html','txt', 'csv'):
                globs.log.err('Output file {}: Invalid output file format specificaton: {}. Please check your command line parameters.'.format(fsplit[0], fsplit[1]))
                canContinue = False

    return canContinue


if __name__ == "__main__":

    # Set program home directory
    globs.progPath = os.path.dirname(os.path.realpath(sys.argv[0]))

    # Open a LogHandler object. 
    # We don't have a log file named yet, but we still need to capture output information
    # See LogHandler class description for more details
    globs.log = log.LogHandler()
    globs.log.write(1,'******** dupReport Log - Start: {}'.format(time.asctime(time.localtime(time.time()))))
    globs.log.write(1,'Python version {}'.format(sys.version))
    globs.log.write(3,'Program Path={}'.format(globs.progPath))
    # Check if we're running a compatible version of Python. Must be 3.0 or higher
    if sys.version_info.major < 3:
        globs.log.err('dupReport requires Python 3.0 or higher to run. Your installation is on version {}.{}.{}.\nPlease install a newer version of Python.'.format(sys.version_info.major, sys.version_info.minor, sys.version_info.micro))
        globs.closeEverythingAndExit(1)
    
    # This routine suppresses log output until proper log file is established. 
    # Used for debugging before the use of a tmp file in LogHandler was implemented
    # Kept around because it doesn't take up much space and it might come in useful again
    #globs.log.suppress()

    # Start Program Timer
    startTime = time.time()

    # Initialize program options
    # This includes command line options and .rc file options
    canContinue = initOptions() 
    if not canContinue: # Something changed in the .rc file that needs manual editing
        globs.closeEverythingAndExit(0)

    # If we're not suppressing, we don't need to unsupress
    #globs.log.unSuppress()

    # Looking for version info on command line? (-V)
    if globs.opts['version']:   # Print version info & exit
        versionInfo()
        globs.closeEverythingAndExit(0)

    # Open log file (finally!)
    globs.log.openLog(globs.opts['logpath'], globs.opts['logappend'], globs.opts['verbose'])

    # Open SQLITE database
    globs.db = db.Database(globs.opts['dbpath'])

    # Write startup information to log file
    globs.log.write(1,'Logfile=[{}]  appendlog=[{}]  logLevel=[{}]'.format(globs.opts['logpath'], globs.opts['logappend'], globs.opts['verbose']))
    globs.log.write(1,'dbPath=[{}]  rcpath=[{}]'.format(globs.opts['dbpath'], globs.opts['rcfilename']))

    # Remove source/destination from database?
    if globs.opts['remove']:
        globs.db.removeSrcDest(globs.opts['remove'][0], globs.opts['remove'][1])
        globs.closeEverythingAndExit(0)
        
    # Update backupset with new nobackupwarn
    if globs.opts['upnobackupwarn']:
         globs.db.update_backupset_nobackupwarn(globs.opts['upnobackupwarn'][0], globs.opts['upnobackupwarn'][1], globs.opts['upnobackupwarn'][2])
         globs.closeEverythingAndExit(0)
        
    # Roll back the database to a specific date?
    if globs.opts['rollback']:
        globs.db.rollback(globs.opts['rollback'])

    # Open email servers
    globs.inServer = dremail.EmailServer()
    retVal = globs.inServer.connect(globs.opts['intransport'], globs.opts['inserver'], globs.opts['inport'], globs.opts['inaccount'], globs.opts['inpassword'], globs.opts['inencryption'])
    globs.log.write(3,'Open incoming server. retVal={}'.format(retVal))
    retVal = globs.inServer.setFolder(globs.opts['infolder'])
    globs.log.write(3,'Set folder. retVal={}'.format(retVal))

    globs.outServer = dremail.EmailServer()
    retVal = globs.outServer.connect('smtp', globs.opts['outserver'], globs.opts['outport'], globs.opts['outaccount'], globs.opts['outpassword'], globs.opts['outencryption'])
    globs.log.write(3,'Open outgoing server. retVal={}'.format(retVal))

    if (globs.opts['collect'] or not globs.opts['report']):
        # Either we're just collecting or not just reporting
        # Get new messages on server
        newMessages = globs.inServer.checkForMessages()
        if newMessages > 0:
            sqlStmt="UPDATE emails SET emailFound = 0"
            globs.db.execSqlStmt(sqlStmt)
            nxtMsg = globs.inServer.getNextMessage()
            while nxtMsg is not None:
                globs.db.execSqlStmt(sqlStmt)
                globs.inServer.processMessage(nxtMsg)
                nxtMsg = globs.inServer.getNextMessage()

    # Either we're just reporting or not just collecting
    if (globs.opts['report'] or not globs.opts['collect']):
        # All email has been collected. Create the report
        globs.report = report.Report()
        globs.report.extractReportData()

        # Select report module based on config parameters
        if globs.report.reportOpts['style'] == 'srcdest':
            import rpt_srcdest as rpt
        elif globs.report.reportOpts['style'] == 'bydest':
            import rpt_bydest as rpt
        elif globs.report.reportOpts['style'] == 'bysource':
            import rpt_bysource as rpt
        elif globs.report.reportOpts['style'] == 'bydate':
            import rpt_bydate as rpt
        else:
            globs.log.err('Invalid report specification: Style:{}  Please check .rc file for correct configuration.'.format(globs.report.reportOpts['style']))
            globs.closeEverythingAndExit(1)

        # Run selected report
        msgHtml, msgText, msgCsv = rpt.runReport(startTime)
    
        globs.log.write(1,msgText)

    # Do we need to send output to file(s)?
    if globs.opts['file'] and not globs.opts['collect']:
        report.sendReportToFile(msgHtml, msgText, msgCsv)
   
    # Are we forbidden from sending report to email?
    if not globs.opts['nomail'] and not globs.opts['collect']: 
        # Send email to SMTP server
        globs.outServer.sendEmail(msgHtml, msgText)
        
    # DC Check for backups that are inactive.
    if globs.opts['nobackupwarn'] > 0:
        globs.db.create_no_backup_warn()

    # DC Purge database emails entries.
    if globs.opts['purgedbemail'] == 'true':
        globs.db.purgedbemail()
    globs.log.write(1,'Program completed in {:.3f} seconds. Exiting'.format(time.time() - startTime))

    # Bye, bye, bye, BYE, BYE!
    globs.closeEverythingAndExit(0)
