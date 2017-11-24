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


def runReport(startTime):
    globs.log.write(1, 'report1()')
    msgHtml=''  # HTML code for report
    msgText=''  # Text output for report

    # Get header and column info
    nFields = len(report.rptColumns)        # Number of fields used in this report
    fldDefs = report.fldDefs                # Field definitions table
    reportOpts = globs.report.reportOpts    # Report Options
    rptCols = report.rptColumns             # Columns used in this report
    rptTits = globs.report.reportTits       # Titles for columns in report

    # Start HTML and text messages
    # Table border and padding settings
    msgHtml='<html><head></head><body><table border={} cellpadding="{}">'.format(reportOpts['border'], reportOpts['padding'])
    msgText = ''

    # Report title
    msgHtml += '<tr><td align="center" colspan = "{}" bgcolor="{}"><b>{}</b></td></tr>'.format(nFields, reportOpts['titlebg'], reportOpts['reporttitle'])
    msgText += reportOpts['reporttitle'] + '\n'
    
    # Column headings - HTML Message
    msgHtml += '<tr>'

    # Remove columns we don't need for this report
    # These are already part of the report logic processing & subheaders
    # We won't need to loop through them for the report fields
    rptCols.remove('date')

    # Get the smallest and largest timestamp in the report file
    dbCursor = globs.db.execSqlStmt("SELECT MIN(timestamp) FROM REPORT")
    minTimestamp = dbCursor.fetchone()[0]
    dbCursor = globs.db.execSqlStmt("SELECT MAX(timestamp) FROM REPORT")
    maxTimestamp = dbCursor.fetchone()[0]
    globs.log.write(2, 'dbResult=[{}]'.format(dbResult))


    # Now, generate headings for the columns that are left
    # Some may have been removed in the .rc file configuration, [headings] section
    for col in rptCols:
        msgHtml += report.printTitle(col, 'html')
        msgText += report.printTitle(col, 'text')

    # End of column headings row
    msgHtml += '</tr>'
    msgText += '\n'

    # Select source/destination pairs from database
    sqlStmt = "SELECT source, destination, lastTime, lastFileCount, lastFileSize from backupsets"
    # How should report be sorted?
    if reportOpts['sortorder'] == 'source':
        sqlStmt = sqlStmt + " order by source, destination"
    else:
        sqlStmt = sqlStmt + " order by destination, source"
    dbCursor = globs.db.execSqlStmt(sqlStmt)
    bkSetRows = dbCursor.fetchall()
    globs.log.write(2, 'bkSetRows=[{}]'.format(bkSetRows))

    # Loop through backupsets table and then get latest activity for each src/dest pair
    for source, destination, lastTime, lastFileCount, lastFileSize in bkSetRows:
        globs.log.write(3, 'Src=[{}] Dest=[{}] lastTime=[{}] lastFileCount=[{}] lastFileSize=[{}]'.format(source, 
            destination, lastTime, lastFileCount, lastFileSize))
        
        # Add title for source/dest pair
        msgHtml += '<tr><td colspan={} align="center" bgcolor="{}"><b>{}:</b> {} <b>{}:</b> {}</b></td></tr>'.format(nFields, reportOpts['subheadbg'], rptTits['source'], source, \
            rptTits['destination'], destination)
        msgText += '***** {}: {}    {}: {} *****\n'.format(rptTits['source'], source, rptTits['destination'], destination)

        # Select all activity for src/dest pair since last report run
        sqlStmt = "SELECT timestamp, examinedFiles, examinedFilesDelta, sizeOfExaminedFiles, fileSizeDelta, \
            addedFiles, deletedFiles, modifiedFiles, filesWithError, parsedResult, messages, warnings, errors \
            FROM report WHERE source=\'{}\' AND destination=\'{}\' order by timestamp".format(source, destination)
        dbCursor = globs.db.execSqlStmt(sqlStmt)
        reportRows = dbCursor.fetchall()
        globs.log.write(3, 'reportRows=[{}]'.format(reportRows))
        if not reportRows: # No rows found = no recent activity
            # Calculate days since last activity
            nowTimestamp = datetime.datetime.now().timestamp()
            now = datetime.datetime.fromtimestamp(nowTimestamp)
            then = datetime.datetime.fromtimestamp(lastTime)
            diff = (now-then).days

            lastDateStr, lastTimeStr = drdatetime.fromTimestamp(lastTime)
            msgHtml += '<tr><td colspan={} align="center"><i>No new activity. Last activity on {} at {} ({} days ago)</i></td></tr>'.format(nFields, lastDateStr, lastTimeStr, diff)
            msgText += 'No new activity. Last activity on {} at {} ({} days ago)\n'.format(lastDateStr, lastTimeStr, diff)
        else:
            # Loop through each new job email and report
            for timestamp, examinedFiles, examinedFilesDelta, sizeOfExaminedFiles, fileSizeDelta, \
                    addedFiles, deletedFiles, modifiedFiles, filesWithError, parsedResult, messages, \
                    warnings, errors in reportRows:
            
                # Get date and time from timestamp
                dateStr, timeStr = drdatetime.fromTimestamp(timestamp)

                # Print report fields
                # Each field takes up one column/cell in the table
                msgHtml += '<tr>'

                msgHtml += report.printField('date', dateStr, 'html')
                msgText += report.printField('date', dateStr, 'text')

                msgHtml += report.printField('time', timeStr, 'html')
                msgText += report.printField('time', timeStr, 'text')

                msgHtml += report.printField('files', examinedFiles, 'html')
                msgText += report.printField('files', examinedFiles, 'text')

                msgHtml += report.printField('filesplusminus', examinedFilesDelta, 'html')
                msgText += report.printField('filesplusminus', examinedFilesDelta, 'text')

                msgHtml += report.printField('size', sizeOfExaminedFiles, 'html')
                msgText += report.printField('size', sizeOfExaminedFiles, 'text')

                msgHtml += report.printField('sizeplusminus', fileSizeDelta, 'html')
                msgText += report.printField('sizeplusminus', fileSizeDelta, 'text')

                msgHtml += report.printField('added', addedFiles, 'html')
                msgText += report.printField('added', addedFiles, 'text')

                msgHtml += report.printField('deleted', deletedFiles, 'html')
                msgText += report.printField('deleted', deletedFiles, 'text')

                msgHtml += report.printField('modified', modifiedFiles, 'html')
                msgText += report.printField('modified', modifiedFiles, 'text')

                msgHtml += report.printField('errors', filesWithError, 'html')
                msgText += report.printField('errors', filesWithError, 'text')

                msgHtml += report.printField('result', parsedResult, 'html')
                msgText += report.printField('result', parsedResult, 'text')

                msgHtml += '</tr>'
                msgText += '\n'

                # Print message/warning/error fields
                # Each of these spans all the table columns
                if ((messages != '') and (reportOpts['displaymessages'] == True)):
                    msgHtml += '<tr><td colspan="{}" align="center" bgcolor="{}">{}: {}</td></tr>'.format(nFields, reportOpts['jobmessagebg'], rptTits['jobmessages'], messages)
                    msgText += '{}: {}\n'.format(rptTits['jobmessages'], messages)
                if ((warnings != '') and (reportOpts['displaywarnings'] == True)):
                    msgHtml += '<tr><td colspan="{}" align="center" bgcolor="{}">{}: {}</td></tr>'.format(nFields, reportOpts['jobwarningbg'], rptTits['jobwarnings'], warnings)
                    msgText += '{}: {}\n'.format(rptTits['jobwarnings'], warnings)
                if ((errors != '') and (reportOpts['displayerrors'] == True)):
                    msgHtml += '<tr><td colspan="{}" align="center" bgcolor="{}">{}: {}</td></tr>'.format(nFields, reportOpts['joberrorbg'], rptTits['joberrors'], errors)
                    msgText += '{}: {}\n'.format(rptTits['joberrors'], errors)

       
    # Add final rows & close
    runningTime = 'Running Time: {:.3f} seconds.'.format(time.time() - startTime)
    msgHtml += '<tr><td colspan={} align="center"><b>{}</b></td></tr>'.format(nFields, runningTime)
    msgHtml += '</table></body></html>'
    msgText += runningTime + '\n'

    # Return text & HTML messages to main program. It can decide which one it wants to use.
    return msgHtml, msgText


