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
import platform
import os
import json

# Import dupReport modules
import globs
import db
import log
import report
import options
import dremail
import drdatetime
import dupapprise
from datetime import datetime

# Print program verersion info
def versionInfo():
    globs.log.out('\n-----\ndupReport: A summary email report generator for Duplicati.')
    globs.log.out('Program Version {}.{}.{} {}'.format(globs.version[0], globs.version[1], globs.version[2], globs.status))
    globs.log.out('Database Version {}.{}.{}'.format(globs.dbVersion[0], globs.dbVersion[1], globs.dbVersion[2]))
    globs.log.out('RC File Version {}.{}.{}'.format(globs.rcVersion[0], globs.rcVersion[1], globs.rcVersion[2]))
    globs.log.out('{}'.format(globs.copyright))
    globs.log.out('Distributed under MIT License. See LICENSE file for details.')
    globs.log.out('\nFollow dupReport on Twitter @dupreport\n-----\n')
    return None

if __name__ == "__main__":
    # Get program home directory
    globs.progPath = os.path.dirname(os.path.realpath(sys.argv[0]))

    # Open a LogHandler object. 
    # We don't have a log file named yet, but we still need to capture output information
    # See LogHandler class description for more details
    globs.log = log.LogHandler()
    globs.log.write(globs.SEV_NOTICE, function='main', action='startup', msg='dupReport Log - Start')
    globs.log.write(globs.SEV_NOTICE, function='main', action='startup', msg='Program Version {}.{}.{} {}'.format(globs.version[0], globs.version[1], globs.version[2], globs.status))
    globs.log.write(globs.SEV_NOTICE, function='main', action='startup', msg='Database Version {}.{}.{}'.format(globs.dbVersion[0], globs.dbVersion[1], globs.dbVersion[2]))
    globs.log.write(globs.SEV_NOTICE, function='main', action='startup', msg='Python version {}'.format(sys.version))
    globs.log.write(globs.SEV_NOTICE, function='main', action='startup', msg='OS Platform: {}'.format(platform.platform()))
    globs.log.write(globs.SEV_NOTICE, function='main', action='startup', msg='Program path: {}'.format(globs.progPath))
    # Check if we're running a compatible version of Python. Must be 3.0 or higher
    if sys.version_info.major < 3:
        globs.log.err('dupReport requires Python 3.0 or higher to run. Your installation is on version {}.{}.{}.\nPlease install a newer version of Python.'.format(sys.version_info.major, sys.version_info.minor, sys.version_info.micro))
        globs.closeEverythingAndExit(1)
    
    # Start Program Timer
    startTime = time.time()

    # Initialize program options
    # This includes command line options and .rc file options
    canContinue = options.initOptions() 
    if not canContinue: # Something changed in the .rc file that needs manual editing
        globs.closeEverythingAndExit(1)

    # Looking for version info on command line? (-V)
    if globs.opts['version']:   # Print version info & exit
        versionInfo()
        globs.closeEverythingAndExit(0)

    # Open log file (finally!)
    globs.log.openLog(globs.opts['logpath'], globs.opts['logappend'], globs.opts['verbose'])

    # Open report object and validate report options
    # We may not be running reports, but the options will be needed later in the program 
    globs.report = report.Report()
    if globs.report.validConfig is False:
        errmsg = 'Report configuration has errors. See log file {} for specific error messages.'.format(globs.logName)
        globs.log.err(errmsg)
        globs.log.write(globs.SEV_ERROR, function='main', action='ValidateConfig', msg=errmsg)
        globs.closeEverythingAndExit(0)
    if globs.opts['validatereport'] == True:  # We just want to validate the report. Exit from here without doing anyting else.
        globs.closeEverythingAndExit(0)

    # See if [apprise] is enabled in .rc file. If so, initialize Apprise options
    if str.lower(globs.optionManager.getRcOption('apprise', 'enabled')) in ['true']:
        globs.appriseObj = dupapprise.dupApprise()

    # Open SQLITE database
    globs.db = db.Database(globs.opts['dbpath'])
    if globs.opts['initdb'] is True:    
        # Forced initialization from command line
        globs.log.write(globs.SEV_NOTICE, function='main', action='InitDB', msg='Database initialization specified on command line.')
        globs.db.dbInitialize()
    else:   # Check for DB version
        needToUpgrade, currDbVersion = globs.db.checkDbVersion()
        if needToUpgrade is True:
            import convert
            globs.log.write(globs.SEV_NOTICE, function='main', action='DBUpgrade', msg='Upgrading database {} from version {} to version {}{}{}'.format(globs.opts['dbpath'], currDbVersion, globs.dbVersion[0], globs.dbVersion[1], globs.dbVersion[2]))
            convert.convertDb(currDbVersion)
            globs.log.write(globs.SEV_NOTICE, function='main', action='DBUpgrade', msg='Database upgrade complete.')

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
    globs.emailManager = dremail.EmailManager()

    # Are we just collecting or not just reporting?
    if (globs.opts['collect'] or not globs.opts['report']):
        # Prep email list for potential purging (-p option or [main]purgedb=true)
        globs.db.execSqlStmt('UPDATE emails SET dbSeen = 0')
        globs.db.dbCommit()

        if globs.opts['showprogress'] > 0:
            globs.log.out('Analyzing email messages.')
        globs.emailManager.checkForNewMessages()

    # Are we just reporting or not just collecting?
    if (globs.opts['report'] or not globs.opts['collect']):
        # All email has been collected. Create the report
        if globs.opts['showprogress'] > 0:
            globs.log.out('Producing report.')

        globs.report.extractReportData()

        # Run selected report
        reportOutput = globs.report.createReport(globs.report.rStruct, startTime)

    # Do we need to send any "backup not seen" warning messages?
    if not globs.opts['stopbackupwarn'] or not globs.opts['nomail']:
        report.sendNoBackupWarnings()

    if globs.appriseObj is not None:
        globs.appriseObj.sendNotifications()

    # Do we need to send output to file(s)?
    if globs.ofileList and not globs.opts['collect']:
        if globs.opts['showprogress'] > 0:
            globs.log.out('Creating report file(s).')
        report.sendReportToFiles(reportOutput)
   
    # Are we forbidden from sending report to email?
    if not globs.opts['nomail'] and not globs.opts['collect']: 
        if globs.opts['showprogress'] > 0:
            globs.log.out('Sending report emails.')

        # Send email to SMTP server
        globs.emailManager.sendEmail(msgHtml=globs.report.createFormattedOutput(reportOutput, 'html'), msgText=globs.report.createFormattedOutput(reportOutput, 'txt'), fileattach=True)

    # Do we need to purge the database?
    if globs.opts['purgedb'] == True:
        globs.db.purgeOldEmails()

    globs.log.write(globs.SEV_NOTICE, function='main', action='Complete', msg='Program completed in {:.3f} seconds. Exiting.'.format(time.time() - startTime))

    if globs.opts['showprogress'] > 0:
        globs.log.out('Ending program.')

    # Bye, bye, bye, BYE, BYE!
    globs.closeEverythingAndExit(0)
