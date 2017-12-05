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

# test imports
#import drdatetime

# Print program verersion info
def versionInfo():
    globs.log.out('\n-----\ndupReport: A summary email report generator for Duplicati.')
    globs.log.out('Program Version {}.{}.{} {}'.format(globs.version[0], globs.version[1], globs.version[2], globs.status))
    globs.log.out('Database Version {}.{}.{}'.format(globs.dbVersion[0], globs.dbVersion[1], globs.dbVersion[2]))
    globs.log.out('{}'.format(globs.copyright))
    globs.log.out('Distributed under MIT License. See LICENSE file for details.')
    globs.log.out('\nFollow dupReport on Twitter @dupreport\n-----\n')
    return None

def closeEverything():
    globs.log.write(1,'Closing everything...')

    
    if globs.inServer is not None:
        globs.inServer.close()
    if globs.outServer is not None:
        globs.outServer.close()
    if globs.db is not None:
        globs.db.dbClose()
    if globs.log is not None:
        globs.log.closeLog()

    sys.exit(0)

# Initialize options in the program
# Return True if program can continue
# Return False if enough changed in the .rc file that program needs to stop
def initOptions():
    globs.log.write(1, 'Startup.initOptions()')

    # Set program path
    globs.progPath = os.path.dirname(os.path.realpath(sys.argv[0]))

    # Create OptionManager instance
    oMgr = options.OptionManager()
    # Parse command line options
    oMgr.processCmdLineArgs()
    # Prepare the .rc file for processing
    oMgr.openRcFile(oMgr.options['rcfilename'])   
    
    # Check if .rc file needs upgrading
    needToUpgrade, currRcVersion = oMgr.checkRcFileVersion()
    if needToUpgrade is True:
        globs.log.out('RC file {} is out of date. Needs update to latest version.'.format(oMgr.options['rcfilename']))
        import convert
        convert.convertRc(oMgr, currRcVersion)
        globs.log.out('RC file {} has been updated to the latest version.'.format(oMgr.rcFileName))
    
    # Check .rc file structure to see if all proper fields are there
    if oMgr.setRcDefaults() is True:
        globs.log.out('RC file {} has changed. Plese edit file with proper configuration, then re-run program'.format(oMgr.options['rcfilename']))
        return False

    # RC file is structurally correct. Now need to parse rc options for global use. 
    if oMgr.readRcOptions() is True:
        return False

    # Set global variables for OptionManager and program options
    # A bit "un-pure', but makes programming much easier
    globs.optionManager = oMgr
    globs.opts = oMgr.options

   # If output files are specified on the command line (-f or -F), make sure their specification is correct
    if validateOutputFiles() is False:
        return False

    # Check if the DB exists or needs initializin
    # Either db file does not yet exist or forced db initialization
    globs.db = db.Database(globs.opts['dbpath'])
    if globs.opts['initdb'] is True:
        globs.log.write(1, 'Database {} needs initializing.'.format(globs.opts['dbpath']))
        globs.db.dbInitialize()
        globs.log.write(1, 'Database {} initialized. Continue processing.'.format(globs.opts['dbpath']))
    else:   # Check for DB version
        needToUpgrade, currDbVersion = globs.db.checkDbVersion()
        if needToUpgrade is True:
            import convert
            convert.convertDb(currDbVersion)
            globs.db.dbClose()
            globs.log.out('Databae file {} has been updated to the latest version.'.format(globs.opts['dbpath']))

    globs.db.dbClose() # Done with DB for now. We'll reopen it properly later.
    globs.log.write(1, 'Program initialization complete. Continuing program.')

    return True

def validateOutputFiles():
    canContinue = True

    # See where the output files are going
    if globs.ofileList:    # Potential output files specified
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
    globs.log = log.LogHandler()
    
    #globs.log.suppress()

    # Start Program Timer
    startTime = time.time()

    canContinue = initOptions() # Initialize program options
    if not canContinue:
        closeEverything()

    globs.log.unSuppress()

    # Looking for version info on command line? (-V)
    if globs.opts['version']:   # Print version info & exit
        versionInfo()
        closeEverything()

    # Open log file
    globs.log.openLog(globs.opts['logpath'], globs.opts['logappend'], globs.opts['verbose'])

    # Open SQLITE database
    globs.db = db.Database(globs.opts['dbpath'])

    # Write startup information to log file
    globs.log.write(1,'******** dupReport Log - Start: {}'.format(time.asctime(time.localtime(time.time()))))
    globs.log.write(1,'Logfile=[{}]  appendlog=[{}]  logLevel=[{}]'.format(globs.opts['logpath'], globs.opts['logappend'], globs.opts['verbose']))
    globs.log.write(1,'dbPath=[{}]  rcpath=[{}]'.format(globs.opts['dbpath'], globs.opts['rcfilename']))

    # Roll back the database to a specific date?
    if globs.opts['rollback']:
        globs.db.rollback(globs.opts['rollback'])


    # Open email servers
    globs.inServer = dremail.EmailServer()
    retVal = globs.inServer.connect(globs.opts['intransport'], globs.opts['inserver'], globs.opts['inport'], globs.opts['inaccount'], globs.opts['inpassword'], globs.opts['inencryption'])
    retVal = globs.inServer.setFolder(globs.opts['infolder'])

    globs.outServer = dremail.EmailServer()
    retVal = globs.outServer.connect('smtp', globs.opts['outserver'], globs.opts['outport'], globs.opts['outaccount'], globs.opts['outpassword'], globs.opts['outencryption'])

    # Either we're just collecting or not just reporting
    if (globs.opts['collect'] or not globs.opts['report']):
   
        # Get new messages on server
        newMessages = globs.inServer.checkForMessages()
        if newMessages > 0:
            nxtMsg = globs.inServer.getNextMessage()
            while nxtMsg is not None:
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

        # Run selected report
        msgHtml, msgText, msgCsv = rpt.runReport(startTime)
    
        globs.log.write(1,msgText)

    # Do we need to send output to file(s)?
    if globs.opts['file'] or globs.opts['filex']:
        report.sendReportToFile(msgHtml, msgText, msgCsv)
   
    # Are we forbidden from sending report to email?
    if not globs.opts['filex']: 
        # Send email to SMTP server
        globs.outServer.sendEmail(msgHtml, msgText)

    globs.log.write(1,'Program completed in {:.3f} seconds. Exiting'.format(time.time() - startTime))

    # Bye, bye, bye, BYE, BYE!
    closeEverything()
