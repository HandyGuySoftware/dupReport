#####
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

# Import dupReport modules
import globs
import startup
import db
import log
import report

# test imports
import drdatetime

def versionInfo():
    globs.log.out('\n-----\ndupReport: A summary email report generator for Duplicati.')
    globs.log.out('Program Version {}.{}.{} {}'.format(globs.version[0], globs.version[1], globs.version[2], globs.status))
    globs.log.out('Database Version {}.{}.{}'.format(globs.dbVersion[0], globs.dbVersion[1], globs.dbVersion[2]))
    globs.log.out('{}'.format(globs.copyright))
    globs.log.out('Distributed under MIT License. See LICENSE file for details.')
    globs.log.out('\nFollow dupReport on Twitter @dupreport\n-----\n')
    return None


if __name__ == "__main__":
    globs.log.suppress()

    # Start Program Timer
    startTime = time.time()

    prog = startup.Startup()
    needToExit = prog.initOptions()

    if needToExit is True:
        sys.exit(1)

    globs.log.unSuppress()

    # Looking for version info on command line? (-V)
    if globs.opts['version']:   # Print version info & exit
        versionInfo()
        sys.exit(0)

    # Open log file
    globs.log.openLog(globs.opts['logpath'], globs.opts['logappend'], globs.opts['verbose'])

    # Open SQLITE database
    globs.db = db.Database(globs.opts['dbpath'])

    # Write startup information to log file
    globs.log.write(1,'******** dupReport Log - Start: {}'.format(time.asctime(time.localtime(time.time()))))
    globs.log.write(1,'Logfile=[{}]  appendlog=[{}]  logLevel=[{}]'.format(globs.opts['logpath'], globs.opts['logappend'], globs.opts['verbose']))
    globs.log.write(1,'dbPath=[{}]  rcpath=[{}]'.format(globs.opts['dbpath'], globs.opts['rcpath']))

    retVal = globs.inServer.connect(globs.opts['intransport'], globs.opts['inserver'], globs.opts['inport'], globs.opts['inaccount'], globs.opts['inpassword'], globs.opts['inencryption'])
    retVal = globs.inServer.setFolder(globs.opts['infolder'])
   
    if (globs.opts['collect'] or not globs.opts['report']):
        newMessages = globs.inServer.checkForMessages()
        if newMessages > 0:
            nxtMsg = globs.inServer.getNextMessage()
            while nxtMsg is not None:
                #print('nxtMsg=[{}]'.format(nxtMsg))
                globs.inServer.processMessage(nxtMsg)
                nxtMsg = globs.inServer.getNextMessage()
        globs.inServer.close()


    if (globs.opts['report'] or not globs.opts['collect']):
        # All email has been collected. Create the report
        globs.report.extractReportData()

        # Select report module based on config parameters
        if globs.report.reportOpts['style'] == 'standard':
            import report1 as rpt
        elif globs.report.reportOpts['style'] == 'grouped':
            if globs.report.reportOpts['groupby'] == 'destination':
                import report2 as rpt
            elif globs.report.reportOpts['groupby'] == 'source':
                import report3 as rpt
            elif globs.report.reportOpts['groupby'] == 'date':
                import report4 as rpt
            else:
                globs.log.err('Invalid grouping specification for style \"{}\": {}. Please check .rc file for correct configuration.'.format(globs.opts['style'], globs.opts['groupby']))

        else:
            globs.log.err('Invalid report specification: Style:{}  Grouped By: {}. Please check .rc file for correct configuration.'.format(globs.opts['style'], globs.opts['groupby']))

        msgHtml, msgText = rpt.runReport(startTime)
    
    # Send the report through email
    retVal = globs.outServer.connect('smtp', globs.opts['outserver'], globs.opts['outport'], globs.opts['outaccount'], globs.opts['outpassword'], globs.opts['outencryption'])

    # Send email to SMTP server
    globs.outServer.sendEmail(msgHtml, msgText)
    globs.outServer.close()

    globs.log.write(1,msgText)

    globs.db.dbCommit()    # Commit any remaining database transactions
    globs.db.dbClose()     # Close database

    globs.log.write(1,'Program completed in {:.3f} seconds. Exiting'.format(time.time() - startTime))

    # Close log file
    globs.log.closeLog()    

    # Bye, bye, bye, BYE, BYE!
    sys.exit(0)
