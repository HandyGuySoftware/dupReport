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
import drdatetime
import dupapprise

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
        globs.log.out('RC file is out of date. Needs update from version {} to version {}{}{}.'.format(currRcVersion, globs.version[0], globs.version[1], globs.version[2]))
        import convert
        convert.convertRc(oMgr, currRcVersion)
        globs.log.out('RC file has been updated to the latest version.')
    
    # Check .rc file structure to see if all proper fields are there
    if oMgr.setRcDefaults() is True:
        globs.log.out('RC file {} has changed. Please edit file with proper configuration, then re-run program'.format(oMgr.options['rcfilename']))
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

def sendNoBackupWarnings():
    globs.log.write(1, 'sendNoBackupWarnings()')

    # Get all source/destination pairs
    sqlStmt = "SELECT source, destination FROM backupsets ORDER BY source, destination"
    dbCursor = globs.db.execSqlStmt(sqlStmt)
    srcDestRows = dbCursor.fetchall()
    if len(srcDestRows) != 0:
        for source, destination in srcDestRows:
			# First, see if SrcDest is listed as offline. If so, skip.
            srcDest = '{}{}{}'.format(source, globs.opts['srcdestdelimiter'], destination)
            offline = globs.optionManager.getRcOption(srcDest, 'offline')
            if offline != None:
                if offline.lower() in ('true'):
                    continue

            latestTimeStamp = report.getLatestTimestamp(source, destination)
            diff = drdatetime.daysSince(latestTimeStamp)
            if report.pastBackupWarningThreshold(source, destination, diff, globs.report.reportOpts) is True:
                globs.log.write(2,'{}-{} is past backup warning threshold @ {} days. Sending warning email'.format(source, destination, diff))
                warnHtml, warnText, subj, send, receive = report.buildWarningMessage(source, destination, diff, latestTimeStamp, globs.report.reportOpts)
                globs.outServer.sendEmail(msgHtml = warnHtml, msgText = warnText, subject = subj, sender = send, receiver = receive)
    return None

if __name__ == "__main__":

    # Set program home directory
    globs.progPath = os.path.dirname(os.path.realpath(sys.argv[0]))

    # Open a LogHandler object. 
    # We don't have a log file named yet, but we still need to capture output information
    # See LogHandler class description for more details
    globs.log = log.LogHandler()
    globs.log.write(1,'******** dupReport Log - Start: {}'.format(time.asctime(time.localtime(time.time()))))
    globs.log.write(1,'Program Version {}.{}.{} {}'.format(globs.version[0], globs.version[1], globs.version[2], globs.status))
    globs.log.write(1,'Database Version {}.{}.{}'.format(globs.dbVersion[0], globs.dbVersion[1], globs.dbVersion[2]))
    globs.log.write(1,'Python version {}'.format(sys.version))
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

    # see if [apprise] section exists in .rc file. If so, initialize Apprise options
    if globs.optionManager.parser.has_section("apprise"):
        globs.appriseObj = dupapprise.dupApprise()

    # Open SQLITE database
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
            globs.log.out('Database file {} has been updated to the latest version.'.format(globs.opts['dbpath']))

    # Write startup information to log file
    globs.log.write(1,'Logfile=[{}]  appendlog=[{}]  logLevel=[{}]'.format(globs.maskData(globs.opts['logpath']), globs.opts['logappend'], globs.opts['verbose']))
    globs.log.write(1,'dbPath=[{}]  rcpath=[{}]'.format(globs.maskData(globs.opts['dbpath']), globs.maskData(globs.opts['rcfilename'])))

    # Remove source/destination from database?
    if globs.opts['remove']:
        globs.db.removeSrcDest(globs.opts['remove'][0], globs.opts['remove'][1])
        globs.closeEverythingAndExit(0)

    # Roll back the database to a specific date?
    if globs.opts['rollback']: # Roll back & continue
        globs.db.rollback(globs.opts['rollback'])
    elif  globs.opts['rollbackx']:  # Roll back and exit
        globs.db.rollback(globs.opts['rollbackx'])
        globs.closeEverythingAndExit(0)

    # Open email servers
    if globs.opts['showprogress'] > 0:
        globs.log.out('Connecting to email servers.')
    globs.inServer = dremail.EmailServer(globs.opts['intransport'], globs.opts['inserver'], globs.opts['inport'], globs.opts['inaccount'], \
        globs.opts['inpassword'], globs.opts['inencryption'], globs.opts['inkeepalive'], globs.opts['infolder'], )

    # Don't need to open output email server if we're not sending email
    # This is used for Apprise support, especially if you're using Apprise to notify you through email. Thus, you may not want to also send redundant emails through dupReport.
    # However, if you haven't supressed backup warnings (i.e., -w), you'll still need an outgoing server connection
    # So, basically, if you've suppressed BOTH backup warnings AND outgoing email, skip opening the outgoing server
    # If EITHER of these is false (i.e., you want either of these to work), open the server connection
    if not globs.opts['stopbackupwarn'] or not globs.opts['nomail']:
        globs.outServer = dremail.EmailServer('smtp', globs.opts['outserver'], globs.opts['outport'], globs.opts['outaccount'], \
            globs.opts['outpassword'], globs.opts['outencryption'], globs.opts['outkeepalive'])

    # Are we just collecting or not just reporting?
    if (globs.opts['collect'] or not globs.opts['report']):

        # Prep email list for potential purging (-p option or [main]purgedb=true)
        globs.db.execSqlStmt('UPDATE emails SET dbSeen = 0')
        globs.db.dbCommit()

        if globs.opts['showprogress'] > 0:
            globs.log.out('Analyzing email messages.')

        # Get new messages on server
        progCount = 0   # Count for progress indicator
        newMessages = globs.inServer.checkForMessages()
        if newMessages > 0:
            nxtMsg = globs.inServer.processNextMessage()
            while nxtMsg is not None:
                if globs.opts['showprogress'] > 0:
                    progCount += 1
                    if (progCount % globs.opts['showprogress']) == 0:
                        globs.log.out('.', newline = False)
                nxtMsg = globs.inServer.processNextMessage()
            if globs.opts['showprogress'] > 0:
                globs.log.out(' ')   # Add newline at end.

            # Do we want to mark messages as 'read/seen'? (Only works for IMAP)
            if globs.opts['markread'] is True and globs.inServer.protocol == 'imap':
                globs.inServer.markMessagesRead()

    # Open report object and initialize report options
    # We may not be running reports, but the options will be needed later in the program 
    globs.report = report.Report()

    # Are we just reporting or not just collecting?
    if (globs.opts['report'] or not globs.opts['collect']):
        # All email has been collected. Create the report
        if globs.opts['showprogress'] > 0:
            globs.log.out('Producing report.')

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

    # Do we need to send any "backup not seen" warning messages?
    if not globs.opts['stopbackupwarn'] or not globs.opts['nomail']:
        sendNoBackupWarnings()

    if globs.appriseObj is not None:
        globs.appriseObj.sendNotifications()

    # Do we need to send output to file(s)?
    if globs.opts['file'] and not globs.opts['collect']:
        if globs.opts['showprogress'] > 0:
            globs.log.out('Creating report file(s).')
        report.sendReportToFile(msgHtml, msgText, msgCsv)
   
    # Are we forbidden from sending report to email?
    if not globs.opts['nomail'] and not globs.opts['collect']: 
        if globs.opts['showprogress'] > 0:
            globs.log.out('Sending report emails.')

        # Send email to SMTP server
        globs.outServer.sendEmail(msgHtml, msgText)

    # Do we need to purge the database?
    if globs.opts['purgedb'] == True:
        globs.db.purgeOldEmails()

    globs.log.write(1,'Program completed in {:.3f} seconds. Exiting'.format(time.time() - startTime))

    if globs.opts['showprogress'] > 0:
        globs.log.out('Ending program.')

    # Bye, bye, bye, BYE, BYE!
    globs.closeEverythingAndExit(0)
