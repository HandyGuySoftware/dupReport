#####
#
# Module name:  rpt_srcdest.py
# Purpose:      Classic dupReport format
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
import options

# Report grouped by source/destination
def runReport(startTime):
    globs.log.write(1, 'rpt_srcdest()')

    # Get header and column info
    nFields, fldDefs, reportOpts, rptCols, rptTits = report.initReportVars()

    # Print the report title
    msgHtml, msgText, msgCsv = report.rptTop(reportOpts, nFields)
    
    # Remove columns we don't need for this report
    # These are already part of the report logic processing & subheaders
    # we won't need to loop through them for the report fields
    rptCols.remove('source')
    rptCols.remove('destination')

    # Print column titles if not printing for each section
    if reportOpts['repeatheaders'] is False:
        msgHtml, msgText, msgCsv = report.rptPrintTitles(msgHtml, msgText, msgCsv, rptCols)

    # Select source/destination pairs from database
    sqlStmt = "SELECT source, destination, lastTimestamp, lastFileCount, lastFileSize from backupsets"

    # How should report be sorted?
    # Options are source & destination
    if reportOpts['sortby'] == 'source':
        sqlStmt = sqlStmt + " ORDER BY source, destination"
    else:
        sqlStmt = sqlStmt + " ORDER BY destination, source"
    dbCursor = globs.db.execSqlStmt(sqlStmt)
    bkSetRows = dbCursor.fetchall()
    globs.log.write(2, 'bkSetRows=[{}]'.format(bkSetRows))

    # Loop through backupsets table and then get latest activity for each src/dest pair
    for source, destination, lastTimestamp, lastFileCount, lastFileSize in bkSetRows:
        globs.log.write(3, 'Src=[{}] Dest=[{}] lastTimestamp=[{}] lastFileCount=[{}] lastFileSize=[{}]'.format(source, 
            destination, lastTimestamp, lastFileCount, lastFileSize))
        
        # Add title for source/dest pair
        subHead = globs.optionManager.getRcOption('report', 'subheading')
        if subHead is not None:
            # Substitute subheading keywords
            subHead = subHead.replace('#SOURCE#',source).replace('#DESTINATION#', destination)
        if subHead is None or subHead == '':
            msgHtml += '<tr><td colspan="{}" align="center" bgcolor="{}"><b>{}:</b> {} <b>{}:</b> {}</td></tr>\n'.format(nFields, reportOpts['subheadbg'], \
                rptTits['source'], source, rptTits['destination'], destination)
            msgText += '***** {}: {}    {}: {} *****\n'.format(rptTits['source'], source, rptTits['destination'], destination)
            msgCsv += '\"***** {}: {}    {}: {} *****\"\n'.format(rptTits['source'], source, rptTits['destination'], destination)
        else:
            msgHtml += '<tr><td colspan="{}" align="center" bgcolor="{}">{}</td></tr>\n'.format(nFields, reportOpts['subheadbg'], subHead)
            msgText += '***** {} *****\n'.format(subHead)
            msgCsv += '\"***** {} *****\"\n'.format(subHead)

        # Print column titles if printing for each section
        if reportOpts['repeatheaders'] is True:
            msgHtml, msgText, msgCsv = report.rptPrintTitles(msgHtml, msgText, msgCsv, rptCols)

        # Select all activity for src/dest pair since last report run
        sqlStmt = "SELECT dupversion, timestamp, duration, examinedFiles, examinedFilesDelta, sizeOfExaminedFiles, fileSizeDelta, \
            addedFiles, deletedFiles, modifiedFiles, filesWithError, parsedResult, messages, warnings, errors, logdata \
            FROM report WHERE source=\'{}\' AND destination=\'{}\' order by timestamp".format(source, destination)
        dbCursor = globs.db.execSqlStmt(sqlStmt)
        reportRows = dbCursor.fetchall()
        globs.log.write(3, 'reportRows=[{}]'.format(reportRows))
        if not reportRows: # No rows found = no recent activity

            # If src/dest is known offline, skip
            srcDest = '{}{}{}'.format(source, globs.opts['srcdestdelimiter'], destination)
            offline = globs.optionManager.getRcOption(srcDest, 'offline')
            if offline != None:
                if offline.lower() in ('true'):
                    continue

            # Calculate days since last activity
            diff = drdatetime.daysSince(lastTimestamp)

            # No activiy seen. See if we're past the backup interval before reporting
            result, interval = report.pastBackupInterval(srcDest, diff)
            if result is False:
                globs.log.write(3, 'SrcDest=[{}] DaysDiff=[{}]. Skip reporting'.format(srcDest, diff))
                msgHtml += '<tr><td colspan="{}" align="center"><i>Last activity {} days ago. Backup interval is {} days.</i></td></tr>\n'.format(nFields, diff, interval)
                msgText += 'Last activity {} days ago. Backup interval is {} days.\n'.format(diff, interval)
                msgCsv += '\"Last activity {} days ago. Backup interval is {} days.\"\n'.format(diff, interval)
            else:
                lastDateStr, lastTimeStr = drdatetime.fromTimestamp(lastTimestamp)
                msgHtml += '<tr><td colspan="{}" align="center" bgcolor="{}"><i>No new activity. Last activity on {} at {} ({} days ago)</i></td></tr>\n'.format(nFields, report.getLastSeenColor(reportOpts, diff, interval), lastDateStr, lastTimeStr, diff)
                msgText += 'No new activity. Last activity on {} at {} ({} days ago)\n'.format(lastDateStr, lastTimeStr, diff)
                msgCsv += '\"No new activity. Last activity on {} at {} ({} days ago)\"\n'.format(lastDateStr, lastTimeStr, diff)
        else:
            # Loop through each new job email and report
            for dupversion, timestamp, duration, examinedFiles, examinedFilesDelta, sizeOfExaminedFiles, fileSizeDelta, \
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
                        msgHtml += '<tr><td colspan="{}" align="center" bgcolor="{}"><details><summary>{}</summary><p>{}</details></td></tr>\n'.format(nFields, reportOpts[bg], rptTits[tit], fld)
                        msgText += '{}: {}\n'.format(rptTits[tit], fld)
                        csvLine = '\"{}: {}\"\n'.format(rptTits[tit], fld).replace('\n', ' ').replace('\r', '') # Need to remove \n & \r because csv truncates after these characters
                        msgCsv += csvLine


    # Add report footer
    msgHtml, msgText, msgCsv = report.rptBottom(msgHtml, msgText, msgCsv, startTime, nFields)

    # Return text & HTML messages to main program. It can decide which one(s) it wants to use.
    return msgHtml, msgText, msgCsv
