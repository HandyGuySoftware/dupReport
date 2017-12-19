#####
#
# Module name:  rpt_bysource.py
# Purpose:      dupReport grouped by source
# 
# Notes:
#
#####

# Import system modules
import datetime
import time
import email
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import smtplib
import re

# Import dupReport modules
import globs
import db
import drdatetime
import report


# Report grouped by source
def runReport(startTime):
    globs.log.write(1, 'rpt_bysource()')

    # Get header and column info
    nFields, fldDefs, reportOpts, rptCols, rptTits = report.initReportVars()

    # Print the report title
    msgHtml, msgText, msgCsv = report.rptTop(reportOpts, nFields)
    
    # Remove columns we don't need for this report
    # These are already part of the report logic processing & subheaders
    # We won't need to loop through them for the report fields
    rptCols.remove('source')

    # Print column titles if not printing for each section
    if reportOpts['repeatheaders'] is False:
        msgHtml, msgText, msgCsv = report.rptPrintTitles(msgHtml, msgText, msgCsv, rptCols)

    # Select sources from database
    dbCursor = globs.db.execSqlStmt("SELECT DISTINCT source FROM backupsets ORDER BY source")
    srcSet = dbCursor.fetchall()
    globs.log.write(2, 'srcSet=[{}]'.format(srcSet))
        
    # Loop through backupsets table and get all the potential destinations
    for srcKey in srcSet:

        # Add Source title
        subHead = globs.optionManager.getRcOption('report', 'subheading')
        if subHead is not None:
            # Substitute subheading keywords
            subHead = subHead.replace('#SOURCE#', srcKey[0])
        if subHead is None or subHead == '':
            msgHtml += '<tr><td colspan="{}" align="center" bgcolor="{}"><b>{}:</b> {}</td></tr>\n'.format(nFields, reportOpts['subheadbg'], rptTits['source'], srcKey[0])
            msgText += '***** {}: {}*****\n'.format(rptTits['source'], srcKey[0])
            msgCsv += '\"***** {}: {}*****\",\n'.format(rptTits['source'], srcKey[0])
        else:
            msgHtml += '<tr><td colspan="{}" align="center" bgcolor="{}">{}</td></tr>\n'.format(nFields, reportOpts['subheadbg'], subHead)
            msgText += '***** {} *****\n'.format(subHead)
            msgCsv += '\"***** {} *****\"\n'.format(subHead)

        # Print column titles if printing for each section
        if reportOpts['repeatheaders'] is True:
            msgHtml, msgText, msgCsv = report.rptPrintTitles(msgHtml, msgText, msgCsv, rptCols)

        sqlStmt = "SELECT destination, timestamp, examinedFiles, examinedFilesDelta, sizeOfExaminedFiles, fileSizeDelta, addedFiles, deletedFiles, modifiedFiles, filesWithError, \
            parsedResult, messages, warnings, errors FROM report WHERE source=\'{}\'".format(srcKey[0])
        if reportOpts['sortby'] == 'destination':
            sqlStmt += ' ORDER BY destination'
        else:
            sqlStmt += ' ORDER BY timestamp'

        dbCursor = globs.db.execSqlStmt(sqlStmt)
        reportRows = dbCursor.fetchall()
        globs.log.write(3, 'reportRows=[{}]'.format(reportRows))

        # Loop through each new activity for the source/destination and add to report
        for destination, timestamp, examinedFiles, examinedFilesDelta, sizeOfExaminedFiles, fileSizeDelta, \
            addedFiles, deletedFiles, modifiedFiles, filesWithError, parsedResult, messages, \
            warnings, errors in reportRows:
            
            # Get date and time from timestamp
            dateStr, timeStr = drdatetime.fromTimestamp(timestamp)

            # Print report fields
            # Each field takes up one column/cell in the table
            msgHtml += '<tr>'

            # The fill list of possible fields in the report. printField() below will skip a field if it is emoved in the .rc file.
            titles = ['destination', 'date','time', 'files', 'filesplusminus', 'size', 'sizeplusminus', 'added','deleted',  'modified', 'errors', 'result']
            fields = [destination, dateStr, timeStr, examinedFiles, examinedFilesDelta, sizeOfExaminedFiles, fileSizeDelta, addedFiles, deletedFiles,  modifiedFiles, filesWithError, parsedResult]

            for ttl, fld in zip(titles, fields):
                msgHtml += report.printField(ttl, fld, 'html')
                msgText += report.printField(ttl, fld, 'text')
                msgCsv += report.printField(ttl, fld, 'csv')

            msgHtml += '</tr>\n'
            msgText += '\n'
            msgCsv += '\n'

            fields = [messages, warnings, errors ]
            options = ['displaymessages', 'displaywarnings', 'displayerrors']
            backgrounds = ['jobmessagebg', 'jobwarningbg', 'joberrorbg']
            titles = ['jobmessages', 'jobwarnings', 'joberrors']
            # Print message/warning/error fields
            # Each of these spans all the table columns
            for fld, opt, bg, tit in zip(fields, options, backgrounds, titles):
                if ((fld != '') and (reportOpts[opt] == True)):
                    msgHtml += '<tr><td colspan="{}" align="center" bgcolor="{}"><details><summary>{}</summary>{}</details></td></tr>\n'.format(nFields, reportOpts[bg], rptTits[tit], fld)
                    msgText += '{}: {}\n'.format(rptTits[tit], fld)
                    msgCsv += '\"{}: {}\",\n'.format(rptTits[tit], fld)


        # Show inactivity - Look for missing source/dest pairs in report
        dbCursor = globs.db.execSqlStmt("SELECT destination, lastTimestamp, lastFileCount, lastFileSize FROM backupsets WHERE source = '{}' ORDER BY source".format(srcKey[0]))
        missingRows = dbCursor.fetchall()
        for destination, lastTimestamp, lastFileCount, lastFileSize in missingRows:
            dbCursor = globs.db.execSqlStmt('SELECT count(*) FROM report WHERE source=\"{}\" AND destination=\"{}\"'.format(srcKey[0], destination))
            countRows = dbCursor.fetchone()
            if countRows[0] == 0:
                # Calculate days since last activity
                diff = drdatetime.daysSince(lastTimestamp)
                lastDateStr, lastTimeStr = drdatetime.fromTimestamp(lastTimestamp)
                msgHtml += '<tr>'
                msgHtml += report.printField('destination', destination, 'html')
                msgHtml += '<td colspan="{}" align="center" bgcolor="{}"><i>No new activity. Last activity on {} at {} ({} days ago)</i></td>'.format(nFields-1, reportOpts['noactivitybg'], lastDateStr, lastTimeStr, diff)
                msgHtml += '</tr>\n'

                msgText += report.printField('destination', destination, 'text')
                msgText += '{}: No new activity. Last activity on {} at {} ({} days ago)\n'.format(destination, lastDateStr, lastTimeStr, diff)

                msgCsv += report.printField('destination', destination, 'csv')
                msgCsv += '\"{}: No new activity. Last activity on {} at {} ({} days ago)\"\n'.format(destination, lastDateStr, lastTimeStr, diff)

                # See if we need to send a warning email for missing backups
                if report.pastBackupWarningThreshold(srcKey[0], destination, diff, reportOpts) is True:
                    warnHtml, warnText, subj, send, receive = report.buildWarningMessage(srcKey[0], destination, diff, lastTimestamp, reportOpts)
                    globs.outServer.sendEmail(msgHtml = warnHtml, msgText = warnText, subject = subj, sender = send, receiver = receive)

    # Add report footer
    msgHtml, msgText, msgCsv = report.rptBottom(msgHtml, msgText, msgCsv, startTime, nFields)


    # Return text & HTML messages to main program. It can decide which one it wants to use.
    return msgHtml, msgText, msgCsv


