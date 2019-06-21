#####
#
# Module name:  report4.py
# Purpose:      dupReport grouped by date
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


# Report grouped by date
def runReport(startTime):
    globs.log.write(1, 'rpt_bydate()')

    # Get header and column info
    nFields, fldDefs, reportOpts, rptCols, rptTits = report.initReportVars()

    # Print the report title
    msgHtml, msgText, msgCsv = report.rptTop(reportOpts, nFields)
    
    # Remove columns we don't need for this report
    # These are already part of the report logic processing & subheaders
    # We won't need to loop through them for the report fields
    rptCols.remove('date')

    # Print column titles if not printing for each section
    if reportOpts['repeatheaders'] is False:
        msgHtml, msgText, msgCsv = report.rptPrintTitles(msgHtml, msgText, msgCsv, rptCols)


    # Get earliest & latest timestamps in the report table
    dbCursor = globs.db.execSqlStmt("SELECT min(timestamp) FROM report")    # Smallest timestamp in the report table
    currentTs = dbCursor.fetchone()[0]
    dbCursor = globs.db.execSqlStmt("SELECT max(timestamp) FROM report")    # Largest timestamp in the report table
    highestTs = dbCursor.fetchone()[0]

    if (currentTs is not None) and (highestTs is not None): #Report table was not empty. There are rows to report
        while currentTs <= highestTs:
            currentDate, currentTime = drdatetime.fromTimestamp(currentTs, dfmt=globs.opts['dateformat'], tfmt=globs.opts['timeformat'])
            currentDateBeginTs = drdatetime.toTimestamp(currentDate + ' 00:00:00', dfmt=globs.opts['dateformat'], tfmt=globs.opts['timeformat'])  # Convert the string into a timestamp
            currentDateEndTs = drdatetime.toTimestamp(currentDate + ' 23:59:59', dfmt=globs.opts['dateformat'], tfmt=globs.opts['timeformat'])  # Convert the string into a timestamp
        
            sqlStmt = "SELECT source, destination, dupversion, timestamp, duration, examinedFiles, examinedFilesDelta, sizeOfExaminedFiles, fileSizeDelta, \
                addedFiles, deletedFiles, modifiedFiles, filesWithError, parsedResult, messages, warnings, errors, logdata \
                FROM report WHERE timestamp >= {} AND timestamp <= {}".format(currentDateBeginTs, currentDateEndTs)
            if reportOpts['sortby'] == 'source':
                sqlStmt += ' ORDER BY source, destination'
            elif reportOpts['sortby'] == 'destination':
                sqlStmt += ' ORDER BY destination, source'
            else:
                sqlStmt += ' ORDER BY timestamp'

            dbCursor = globs.db.execSqlStmt(sqlStmt)
            reportRows = dbCursor.fetchall()
            globs.log.write(3, 'reportRows=[{}]'.format(reportRows))

            if len(reportRows) != 0:
                subHead = globs.optionManager.getRcOption('report', 'subheading')
                if subHead is not None:
                        # Substitute subheading keywords
                        subHead = subHead.replace('#DATE#', currentDate)
                if subHead is None or subHead == '':
                    msgHtml += '<tr><td colspan="{}" align="center" bgcolor="{}"><b>{}:</b> {}</td></tr>\n'.format(nFields, reportOpts['subheadbg'], rptTits['date'], currentDate)
                    msgText += '***** {}: {} *****\n'.format(rptTits['date'], currentDate)
                    msgCsv += '\"***** {}: {} *****\"\n'.format(rptTits['date'], currentDate)
                else:
                    msgHtml += '<tr><td colspan="{}" align="center" bgcolor="{}">{}</td></tr>\n'.format(nFields, reportOpts['subheadbg'], subHead)
                    msgText += '***** {} *****\n'.format(subHead)
                    msgCsv += '\"***** {} *****\"\n'.format(subHead)

                # Print column titles if printing for each section
                if reportOpts['repeatheaders'] is True:
                    msgHtml, msgText, msgCsv = report.rptPrintTitles(msgHtml, msgText, msgCsv, rptCols)


            for source, destination, dupversion, timestamp, duration, examinedFiles, examinedFilesDelta, sizeOfExaminedFiles, fileSizeDelta, \
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

                # The full list of possible fields in the report. printField() below will skip a field if it is emoved in the .rc file.
                titles = ['source', 'destination', 'dupversion', 'time', 'duration', 'files', 'filesplusminus', 'size', 'sizeplusminus', 'added', 'deleted', 'modified', 'errors', 'result']
                fields = [source, destination, dupversion, timeStr, rptDuration, examinedFiles, examinedFilesDelta, sizeOfExaminedFiles, fileSizeDelta, addedFiles, deletedFiles,  modifiedFiles, filesWithError, parsedResult]
                
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
                        msgCsv += '\"{}: {}\"\n'.format(rptTits[tit], fld)


            # Move current timestamp ahead 1 second
            currentTs = currentDateEndTs + 1

    # Now see which systems didn't report in
    dbCursor = globs.db.execSqlStmt("SELECT source, destination, lastTimestamp FROM backupsets ORDER BY source, destination")
    setRows = dbCursor.fetchall()
    globs.log.write(3, 'setRows=[{}]'.format(setRows))

    # Flag to let us know if we need to print a header for missing backupsets
    hdrFlag = 0
    for source, destination, lastTimestamp in setRows:
        dbCursor = globs.db.execSqlStmt("SELECT count(*) FROM report WHERE source = \'{}\' AND destination = \'{}\'".format(source, destination))
        seenRows = dbCursor.fetchone()[0]
        globs.log.write(3, 'seenRows=[{}]'.format(seenRows))
        if seenRows == 0:   # Didn't get any rows for source/Destination pair. Add to report

            # If src/dest is known offline, skip
            srcDest = '{}{}{}'.format(source, globs.opts['srcdestdelimiter'], destination)
            offline = globs.optionManager.getRcOption(srcDest, 'offline')
            if offline != None:
                if offline.lower() in ('true'):
                    continue

            if hdrFlag == 0:
                msgHtml += '<tr><td colspan="{}" align="center" bgcolor="{}"><b>Missing Backup Sets</b></td></tr>\n'.format(nFields, reportOpts['subheadbg'])
                msgText += 'Missing Back Sets\n'
                msgCsv += '\"Missing Back Sets\"\n'
                hdrFlag = 1

            diff = drdatetime.daysSince(lastTimestamp)
            result, interval = report.pastBackupInterval(srcDest, diff)
            if result is False:
                msgHtml += '<tr><td colspan="{}" align="center">{} to {}: <i>Last activity {} days ago. Backup interval is {} days.</i></td></tr>\n'.format(nFields, source, destination, diff, interval)
                msgText += '{} to {}: Last activity {} days ago. Backup interval is {} days.\n'.format(source, destination, diff, interval)
                msgCsv += '\"{} to {}: Last activity {} days ago. Backup interval is {} days.\"\n'.format(source, destination, diff, interval)
            else:
                lastDateStr, lastTimeStr = drdatetime.fromTimestamp(lastTimestamp)
                msgHtml += '<tr><td colspan="{}" align="center" bgcolor="{}">{} to {}: <i>No new activity. Last activity on {} at {} ({} days ago)</i></td></tr>\n'.format(nFields, report.getLastSeenColor(reportOpts, diff, interval), source, destination, lastDateStr, lastTimeStr, diff)
                msgText += '{} to {}: No new activity. Last activity on {} at {} ({} days ago)\n'.format(source, destination, lastDateStr, lastTimeStr, diff)
                msgCsv += '\"{} to {}: No new activity. Last activity on {} at {} ({} days ago)\"\n'.format(source, destination, lastDateStr, lastTimeStr, diff)

    # Add report footer
    msgHtml, msgText, msgCsv = report.rptBottom(msgHtml, msgText, msgCsv, startTime, nFields)

    # Return text & HTML messages to main program. It can decide which one it wants to use.
    return msgHtml, msgText, msgCsv


