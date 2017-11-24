#####
#
# Module name:  report3.py
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

# Report grouped by destination
def runReport(startTime):
    globs.log.write(1, 'report3()')
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
    rptCols.remove('source')
   
    # Now, generate headings for the columns that are left
    # Some may have been removed in the .rc file configuration, [headings] section
    for col in rptCols:
        msgHtml += report.printTitle(col, 'html')
        msgText += report.printTitle(col, 'text')

    # End of column headings row
    msgHtml += '</tr>'
    msgText += '\n'

    # Select sources from database
    dbCursor = globs.db.execSqlStmt("SELECT DISTINCT source FROM backupsets ORDER BY source")
    srcSet = dbCursor.fetchall()
    globs.log.write(2, 'srcSet=[{}]'.format(srcSet))
        
    # Loop through backupsets table and get all the potential sources
    for srcKey in srcSet:
        # Add Source title
        msgHtml += '<tr><td colspan={} align="center" bgcolor="{}"><b>{}:</b> {}</b></td></tr>'.format(nFields, reportOpts['subheadbg'], rptTits['source'], srcKey[0])
        msgText += '***** {}: {}*****\n'.format(rptTits['source'], srcKey[0])

        dbCursor = globs.db.execSqlStmt("SELECT destination, lastTime, lastFileCount, lastFileSize FROM backupsets WHERE source = '{}' ORDER BY destination".format(srcKey[0]))
        srcDestSets = dbCursor.fetchall()
        globs.log.write(2, 'srcDestSets=[{}]'.format(srcDestSets))

        # Loop through all sources for that destination
        for destination, lastTime, lastFileCount, lastFileSize in srcDestSets:
            globs.log.write(3, 'Src=[{}] Dest=[{}] lastTime=[{}] lastFileCount=[{}] lastFileSize=[{}]'.format(srcKey[0], destination, lastTime, lastFileCount, lastFileSize))

            # Select all activity for src/dest pair since last report run
            sqlStmt = "SELECT timestamp, examinedFiles, examinedFilesDelta, sizeOfExaminedFiles, fileSizeDelta, \
                addedFiles, deletedFiles, modifiedFiles, filesWithError, parsedResult, messages, warnings, errors \
                FROM report WHERE source=\'{}\' AND destination=\'{}\' order by timestamp".format(srcKey[0], destination)

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
                msgHtml += '<tr>'
                msgHtml += report.printField('destination', destination, 'html')
                msgHtml += '<td colspan={} align="center"><i>No new activity. Last activity on {} at {} ({} days ago)</i></td>'.format(nFields-1, lastDateStr, lastTimeStr, diff)
                msgHtml += '</tr>'

                msgText += report.printField('destination', destination, 'text')
                msgText += '{}: No new activity. Last activity on {} at {} ({} days ago)\n'.format(destination, lastDateStr, lastTimeStr, diff)
            else:
                # Loop through each new activity for the source/destination and add to report
                for timestamp, examinedFiles, examinedFilesDelta, sizeOfExaminedFiles, fileSizeDelta, \
                        addedFiles, deletedFiles, modifiedFiles, filesWithError, parsedResult, messages, \
                        warnings, errors in reportRows:
            
                    # Get date and time from timestamp
                    dateStr, timeStr = drdatetime.fromTimestamp(timestamp)

                    msgHtml += '<tr>'

                    msgHtml += report.printField('destination', destination, 'html')
                    msgText += report.printField('destination', destination, 'text')
                    
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

    return msgHtml, msgText


