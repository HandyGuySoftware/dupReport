#####
#
# Module name:  rpt_bydest.py
# Purpose:      dupReport grouped by destination
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


# Report grouped by destination
def runReport(startTime):
    globs.log.write(1, 'rpt_bydest()')

    # Get header and column info
    nFields, fldDefs, reportOpts, rptCols, rptTits = report.initReportVars()

    # Print the report title
    msgHtml, msgText, msgCsv = report.rptTop(reportOpts, nFields)
    
    # Remove columns we don't need for this report
    # These are already part of the report logic processing & subheaders
    # We won't need to loop through them for the report fields
    rptCols.remove('destination')

    # Print column titles if not printing for each section
    if reportOpts['repeatheaders'] is False:
        msgHtml, msgText, msgCsv = report.rptPrintTitles(msgHtml, msgText, msgCsv, rptCols)

    # Select destinations from database
    dbCursor = globs.db.execSqlStmt("SELECT DISTINCT destination FROM backupsets ORDER BY destination")
    destSet = dbCursor.fetchall()
    globs.log.write(2, 'destSet=[{}]'.format(destSet))
        
    # Loop through backupsets table and get all the potential destinations
    for destKey in destSet:

        # Add Destination title
        subHead = globs.optionManager.getRcOption('report', 'subheading')
        if subHead is not None:
            # Substitute subheading keywords
            subHead = subHead.replace('#DESTINATION#', destKey[0])
        if subHead is None or subHead == '':
            msgHtml += '<tr><td colspan="{}" align="center" bgcolor="{}"><b>{}:</b> {}</td></tr>\n'.format(nFields, reportOpts['subheadbg'], rptTits['destination'], destKey[0])
            msgText += '***** {}: {}*****\n'.format(rptTits['destination'], destKey[0])
            msgCsv += '\"***** {}: {}*****\",\n'.format(rptTits['destination'], destKey[0])
        else:
            msgHtml += '<tr><td colspan="{}" align="center" bgcolor="{}">{}</td></tr>\n'.format(nFields, reportOpts['subheadbg'], subHead)
            msgText += '***** {} *****\n'.format(subHead)
            msgCsv += '\"***** {} *****\"\n'.format(subHead)

        # Print column titles if printing for each section
        if reportOpts['repeatheaders'] is True:
            msgHtml, msgText, msgCsv = report.rptPrintTitles(msgHtml, msgText, msgCsv, rptCols)

        sqlStmt = "SELECT source, dupversion, timestamp, duration, examinedFiles, examinedFilesDelta, sizeOfExaminedFiles, fileSizeDelta, addedFiles, deletedFiles, modifiedFiles, filesWithError, \
            parsedResult, messages, warnings, errors, logdata FROM report WHERE destination=\'{}\'".format(destKey[0])
        if reportOpts['sortby'] == 'source':
            sqlStmt += ' ORDER BY source'
        else:
            sqlStmt += ' ORDER BY timestamp'

        dbCursor = globs.db.execSqlStmt(sqlStmt)
        reportRows = dbCursor.fetchall()
        globs.log.write(3, 'reportRows=[{}]'.format(reportRows))

        # Loop through each new activity for the source/destination and add to report
        for source, dupversion, timestamp, duration, examinedFiles, examinedFilesDelta, sizeOfExaminedFiles, fileSizeDelta, \
            addedFiles, deletedFiles, modifiedFiles, filesWithError, parsedResult, messages, \
            warnings, errors, logdata in reportRows:
            
            # Convert duration to string
            rptDuration = drdatetime.timeDiff(duration)    
            
            # Truncate message, warning, & error if indicated in .rc file
            messages, warnings, errors, logdata = report.truncateWarnErrMsgs(messages, reportOpts['truncatemessage'], warnings, reportOpts['truncatewarning'], errors, reportOpts['truncateerror'], logdata, reportOpts['truncatelogdata'])
            
            # Get date and time from timestamp
            dateStr, timeStr = drdatetime.fromTimestamp(timestamp)

            # Print report fields
            # Each field takes up one column/cell in the table
            msgHtml += '<tr>'

            # The full list of possible fields in the report. printField() below will skip a field if it is removed in the .rc file.
            titles = ['source', 'dupversion', 'date','time', 'duration', 'files', 'filesplusminus', 'size', 'sizeplusminus', 'added','deleted',  'modified', 'errors', 'result']
            fields = [source, dupversion, dateStr, timeStr, rptDuration, examinedFiles, examinedFilesDelta, sizeOfExaminedFiles, fileSizeDelta, addedFiles, deletedFiles,  modifiedFiles, filesWithError, parsedResult]

            for ttl, fld in zip(titles, fields):
                msgHtml += report.printField(ttl, fld, 'html')
                msgText += report.printField(ttl, fld, 'text')
                msgCsv += report.printField(ttl, fld, 'csv')

            msgHtml += '</tr>\n'
            msgText += '\n'
            msgCsv += '\n'

            fields = [messages, warnings, errors, logdata ]
            options = ['displaymessages', 'displaywarnings', 'displayerrors', 'displaylogdata']
            backgrounds = ['jobmessagebg', 'jobwarningbg', 'joberrorbg', 'joblogdatabg']
            titles = ['jobmessages', 'jobwarnings', 'joberrors', 'joblogdata']
            # Print message/warning/error/logdata fields
            # Each of these spans all the table columns
            for fld, opt, bg, tit in zip(fields, options, backgrounds, titles):
                if ((fld != '') and (reportOpts[opt] == True)):
                    msgHtml += '<tr><td colspan="{}" align="center" bgcolor="{}"><details><summary>{}</summary>{}</details></td></tr>\n'.format(nFields, reportOpts[bg], rptTits[tit], fld)
                    msgText += '{}: {}\n'.format(rptTits[tit], fld)
                    msgCsv += '\"{}: {}\",\n'.format(rptTits[tit], fld)


        # Show inactivity - Look for missing source/dest pairs in report
        dbCursor = globs.db.execSqlStmt("SELECT source, lastTimestamp, lastFileCount, lastFileSize FROM backupsets WHERE destination = '{}' ORDER BY source".format(destKey[0]))
        missingRows = dbCursor.fetchall()
        for source, lastTimestamp, lastFileCount, lastFileSize in missingRows:
            dbCursor = globs.db.execSqlStmt('SELECT count(*) FROM report WHERE source=\"{}\" AND destination=\"{}\"'.format(source, destKey[0]))
            countRows = dbCursor.fetchone()
            if countRows[0] == 0:

                # If src/dest is known offline, skip
                srcDest = '{}{}{}'.format(source, globs.opts['srcdestdelimiter'], destKey[0])
                offline = globs.optionManager.getRcOption(srcDest, 'offline')
                if offline != None:
                    if offline.lower() in ('true'):
                        continue

                # Calculate days since last activity
                diff = drdatetime.daysSince(lastTimestamp)

                # See if we're past the backup interval before reporting
                result, interval = report.pastBackupInterval(srcDest, diff)
                if result is False:
                    globs.log.write(3, 'SrcDest=[{}] DaysDiff=[{}]. Skip reporting'.format(srcDest, diff))
                    msgHtml += '<tr>'
                    msgHtml += report.printField('source', source, 'html')
                    msgHtml += '<td colspan="{}" align="center"><i>Last activity {} days ago. Backup interval is {} days.</i></td>'.format(nFields-1, diff, interval)
                    msgHtml += '</tr>\n'

                    msgText += report.printField('source', source, 'text')
                    msgText += '{}: Last activity {} days ago. Backup interval is {}\n'.format(source, diff, interval)

                    msgCsv += report.printField('source', source, 'csv')
                    msgCsv += '\"{}: Last activity {} days ago. Backup interval is {}.\"\n'.format(source, diff, interval)
                else:
                    lastDateStr, lastTimeStr = drdatetime.fromTimestamp(lastTimestamp)
                    msgHtml += '<tr>'
                    msgHtml += report.printField('source', source, 'html')
                    msgHtml += '<td colspan="{}" align="center" bgcolor="{}"><i>No new activity. Last activity on {} at {} ({} days ago)</i></td>'.format(nFields-1, report.getLastSeenColor(reportOpts, diff, interval), lastDateStr, lastTimeStr, diff)
                    msgHtml += '</tr>\n'

                    msgText += report.printField('source', source, 'text')
                    msgText += '{}: No new activity. Last activity on {} at {} ({} days ago)\n'.format(source, lastDateStr, lastTimeStr, diff)

                    msgCsv += report.printField('source', source, 'csv')
                    msgCsv += '\"{}: No new activity. Last activity on {} at {} ({} days ago)\"\n'.format(source, lastDateStr, lastTimeStr, diff)

    # Add report footer
    msgHtml, msgText, msgCsv = report.rptBottom(msgHtml, msgText, msgCsv, startTime, nFields)

    # Return text & HTML messages to main program. It can decide which one it wants to use.
    return msgHtml, msgText, msgCsv
