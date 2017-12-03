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
    nFields = len(report.rptColumns)        # Number of fields used in this report
    fldDefs = report.fldDefs                # Field definitions table
    reportOpts = globs.report.reportOpts    # Report Options
    rptCols = report.rptColumns             # Columns used in this report
    rptTits = globs.report.reportTits       # Titles for columns in report

    # Start HTML and text messages
    # Table border and padding settings
    msgHtml = '<html><head></head><body><table border={} cellpadding="{}">'.format(reportOpts['border'], reportOpts['padding'])
    msgText = ''
    msgCsv = ''
    
    # Add report title
    msgHtml += '<tr><td align="center" colspan = "{}" bgcolor="{}"><b>{}</b></td></tr>'.format(nFields, reportOpts['titlebg'], reportOpts['reporttitle'])
    msgText += reportOpts['reporttitle'] + '\n'
    msgCsv += '\"' + reportOpts['reporttitle'] + '\"\n'
    
    # Start column headings for HTML Message
    msgHtml += '<tr>'

    # Remove columns we don't need for this report
    # These are already part of the report logic processing & subheaders
    # We won't need to loop through them for the report fields
    rptCols.remove('destination')
   
    # Now, generate headings for the columns that are left
    # Some may have been removed in the .rc file configuration, [headings] section
    for col in rptCols:
        msgHtml += report.printTitle(col, 'html')
        msgText += report.printTitle(col, 'text')
        msgCsv += report.printTitle(col, 'csv')


    # End of column headings row
    msgHtml += '</tr>'
    msgText += '\n'
    msgCsv += '\n'

    # Select destinations from database
    dbCursor = globs.db.execSqlStmt("SELECT DISTINCT destination FROM backupsets ORDER BY destination")
    destSet = dbCursor.fetchall()
    globs.log.write(2, 'destSet=[{}]'.format(destSet))
        
    # Loop through backupsets table and get all the potential destinations
    for destKey in destSet:
        # Add Destination title
        subHead = globs.optionManager.getOption('report', 'subheading')
        if subHead is not None:
            subHead = subHead.replace('#DESTINATION#', destKey[0])
        if subHead is None or subHead == '':
            msgHtml += '<tr><td colspan={} align="center" bgcolor="{}"><b>{}:</b> {}</b></td></tr>'.format(nFields, reportOpts['subheadbg'], rptTits['destination'], destKey[0])
            msgText += '***** {}: {}*****\n'.format(rptTits['destination'], destKey[0])
            msgCsv += '\"***** {}: {}*****\",\n'.format(rptTits['destination'], destKey[0])
        else:
            msgHtml += '<tr><td colspan={} align="center" bgcolor="{}">{}</td></tr>'.format(nFields, reportOpts['subheadbg'], subHead)
            msgText += '***** {} *****\n'.format(subHead)
            msgCsv += '\"***** {} *****\",\n'.format(subHead)

        dbCursor = globs.db.execSqlStmt("SELECT source, lastTime, lastFileCount, lastFileSize FROM backupsets WHERE destination = '{}'".format(destKey[0]))
        #srcDestSets = dbCursor.fetchone()
        source, lastTime, lastFileCount, lastFileSize = dbCursor.fetchone()
        globs.log.write(2, 'source=[{}] lastTime=[{}] lastFileCount=[{}] lastFileSize=[{}]'.format(source, lastTime, lastFileCount, lastFileSize))

        sqlStmt = "SELECT source, timestamp, examinedFiles, examinedFilesDelta, sizeOfExaminedFiles, fileSizeDelta, \
            addedFiles, deletedFiles, modifiedFiles, filesWithError, parsedResult, messages, warnings, errors \
            FROM report WHERE destination=\'{}\'".format(destKey[0])
        if reportOpts['sortby'] == 'source':
            sqlStmt += ' ORDER BY source'
        else:
            sqlStmt += ' ORDER BY timestamp'

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
            msgHtml += report.printField('source', source, 'html')
            msgHtml += '<td colspan={} align="center"><i>No new activity. Last activity on {} at {} ({} days ago)</i></td>'.format(nFields-1, lastDateStr, lastTimeStr, diff)
            msgHtml += '</tr>'

            msgText += report.printField('source', source, 'text')
            msgText += '{}: No new activity. Last activity on {} at {} ({} days ago)\n'.format(source, lastDateStr, lastTimeStr, diff)

            msgCsv += report.printField('source', source, 'csv')
            msgCsv += '\"{}: No new activity. Last activity on {} at {} ({} days ago)\"\n'.format(source, lastDateStr, lastTimeStr, diff)
        else:
            # Loop through each new activity for the source/destination and add to report
            for source, timestamp, examinedFiles, examinedFilesDelta, sizeOfExaminedFiles, fileSizeDelta, \
                addedFiles, deletedFiles, modifiedFiles, filesWithError, parsedResult, messages, \
                warnings, errors in reportRows:
            
                # Get date and time from timestamp
                dateStr, timeStr = drdatetime.fromTimestamp(timestamp)

                # Print report fields
                # Each field takes up one column/cell in the table
                msgHtml += '<tr>'

                # The fill list of possible fields in the report. printField() below will skip a field if it is emoved in the .rc file.
                titles = ['source', 'date','time', 'files', 'filesplusminus', 'size', 'sizeplusminus', 'added','deleted',  'modified', 'errors', 'result']
                fields = [source, dateStr, timeStr, examinedFiles, examinedFilesDelta, sizeOfExaminedFiles, fileSizeDelta, addedFiles, deletedFiles,  modifiedFiles, filesWithError, parsedResult]

                for ttl, fld in zip(titles, fields):
                    msgHtml += report.printField(ttl, fld, 'html')
                    msgText += report.printField(ttl, fld, 'text')
                    msgCsv += report.printField(ttl, fld, 'csv')

                msgHtml += '</tr>'
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
                        msgHtml += '<tr><td colspan="{}" align="center" bgcolor="{}">{}: {}</td></tr>'.format(nFields, reportOpts[bg], rptTits[tit], fld)
                        msgText += '{}: {}\n'.format(rptTits[tit], fld)
                        msgCsv += '\"{}: {}\",\n'.format(rptTits[tit], fld)

       
    # Add final rows & close
    runningTime = 'Running Time: {:.3f} seconds.'.format(time.time() - startTime)
    msgHtml += '<tr><td colspan={} align="center"><b>{}</b></td></tr>'.format(nFields, runningTime)
    msgHtml += '</table></body></html>'
    msgText += runningTime + '\n'
    msgText += '\"' + runningTime + '\"\n'
    msgCsv += '\"' + runningTime + '\"\n'

    return msgHtml, msgText, msgCsv
