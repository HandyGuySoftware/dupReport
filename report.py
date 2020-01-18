#####
#
# Module name:  report.py
# Purpose:      Create dupReport ouput reports
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
import sys
import os

# Import dupReport modules
import globs
import db
import drdatetime
import options

# fldDefs = Dictionary of field definitions
fldDefs = {
    # field                 [0]Title                [1]dbField             [2]alignment[3]gig/meg? [4]hdrDef   [5]normDef   [6]megaDef  [7]gigaDef
    'source':               ('Source',              'source',              'left',     False,      '20',       '20'),
    'destination':          ('Destination',         'destination',         'left',     False,      '20',       '20'),
    'dupversion':           ('Version',             'dupversion',          'left',     False,      '20',       '20'),
    'date':                 ('Date',                'dateStr',             'left',     False,      '13',       '13'),
    'time':                 ('Time',                'timeStr',             'left',     False,      '11',       '11'),
    'duration':             ('Duration',            'duration',            'right',    False,      '15',       '15'),
    'files':                ('Files',               'examinedFiles',       'right',    False,      '>12',      '>12,'),
    'filesplusminus':       ('+/-',                 'examinedFilesDelta',  'right',    False,      '>12',      '>+12,'),
    'size':                 ('Size',                'sizeOfExaminedFiles', 'right',    True,       '>20',      '>20,',      '>20,.2f', '>20,.2f'),
    'sizeplusminus':        ('+/-',                 'fileSizeDelta',       'right',    True,       '>20',      '>+20,',     '>+20,.2f', '>+20,.2f'),
    'added':                ('Added',               'addedFiles',          'right',    False,      '>12',      '>12,'),
    'deleted':              ('Deleted',             'deletedFiles',        'right',    False,      '>12',      '>12,'),
    'modified':             ('Modified',            'modifiedFiles',       'right',    False,      '>12',      '>12,'),
    'errors':               ('Errors',              'filesWithError',      'right',    False,      '>12',      '>12,'),
    'result':               ('Result',              'parsedResult',        'left',     False,      '>13',      '>13'),
    'jobmessages':          ('JobMessages',         'messages',            'center',   False,      '^50',      '^50'),
    'jobwarnings':          ('JobWarnings',         'warnings',            'center',   False,      '^50',      '^50'),
    'joberrors':            ('JobErrors',           'errors',              'center',   False,      '^50',      '^50'),
    'joblogdata':           ('Log Data',            'logdata',             'center',   False,      '^50',      '^50')
    }

# List of columns in the report
rptColumns = ['source', 'destination', 'dupversion', 'date', 'time', 'duration', 'files', 'filesplusminus', 'size',  'sizeplusminus', 'added', 'deleted', 'modified', 'errors', 'result', 'jobmessages', 'jobwarnings', 'joberrors', 'joblogdata']

# Provide a field format specification for the titles in the report
def printTitle(fld, typ):
    outStr = None
    globs.log.write(3, 'report.printTitle({}, {})'.format(fld, typ))

    # Need to see if we should add the size display after the heading  (e.g. '(MB)' or '(GB)')
    # This is kind of a cheat, but there is no other more elegant way of doing it
    displayAddOn = '' # Start with nothing
    if ((fld == 'size') or (fld == 'sizeplusminus')):  # These are the only fields that can use the add-on
        if globs.report.reportOpts['showsizedisplay'] is True:  # Do we want to show it, based on .rec config?
            if globs.report.reportOpts['sizedisplay'][:4].lower() == 'mega':    # Need to add (MB)
                displayAddOn = ' (MB)'
            elif globs.report.reportOpts['sizedisplay'][:4].lower() == 'giga': # giga - need to add (GB)
                displayAddOn = ' (GB)'
            else: # Unknown, revert to default
                displayAddOn = ''

    if typ == 'html':
        outStr = '<td align=\"{}\"><b>{}{}</b></td>'.format(fldDefs[fld][2], globs.report.reportTits[fld], displayAddOn)
    elif typ == 'text':
        outStr = '{:{fmt}}'.format(fldDefs[fld][0] + displayAddOn, fmt=fldDefs[fld][4])
    elif typ == 'csv':
        outStr = '\"{:{fmt}}\",'.format(fldDefs[fld][0] + displayAddOn, fmt=fldDefs[fld][4])

    globs.log.write(3, 'outStr = {}'.format(outStr))
    return outStr

# Provide a field format specification for the data fields (cells) in the report
def printField(fld, val, fmt):

    # If the column has been removed from the report, return an empty string
    if fld not in rptColumns:
        return ''

    # Process fields based on their type.
    if type(val) is not str: # ints & floats
        v = val
        outFmt = fldDefs[fld][5]
        
        # Need to adjust value based on MB/GB specification
        # reportOpts['sizedisplay'] indicates if we want to convert sizes to MB/GB
        if ((globs.report.reportOpts['sizedisplay'][:4].lower() == 'mega') and (fldDefs[fld][3] == True)):
            v = val / 1000000.00
            outFmt = fldDefs[fld][6]
        elif ((globs.report.reportOpts['sizedisplay'][:4].lower() == 'giga') and (fldDefs[fld][3] == True)):
            v = val / 1000000000.00
            outFmt = fldDefs[fld][7]
        
        # Create HTML, text, and csv versions of the format string
        outHtml = '<td align=\"{}\">{:{fmt}}</td>'.format(fldDefs[fld][2], v, fmt=outFmt)
        outTxt = '{:{fmt}}'.format(v, fmt=outFmt)
        outCsv = '\"{:{fmt}}\",'.format(v, fmt=outFmt)
    else:
        # Create HTML, text, and csv versions of the format string
        outHtml = '<td align=\"{}\">{}</td>'.format(fldDefs[fld][2], val)
        outTxt = '{:{fmt}}'.format(val, fmt=fldDefs[fld][5])
        outCsv = '\"{:{fmt}}\",'.format(val, fmt=fldDefs[fld][5])

    if fmt == 'html':
        return outHtml
    elif fmt == 'text':
        return outTxt
    elif fmt == 'csv':
        return outCsv

# Send report to an output file
# msgH = HTML message
# msgT = Text message
# msgC = CSV message
def sendReportToFile(msgH, msgT, msgC = None):

    # See where the output files are going
    for fspec in globs.ofileList:
        fsplit = fspec[0].split(',')
        fName = fsplit[0]
        fmt = fsplit[1]

        if fmt == 'html':
            outMsg = msgH
        elif fmt == 'txt':
            outMsg = msgT
        elif fmt == 'csv':
            outMsg = msgC

        if fName == 'stdout':
            sys.stdout.write(outMsg)
        elif fName == 'stderr':
            sys.stderr.write(outMsg)
        else:
            try:
                outfile = open(fName,'w')
            except (OSError, IOError):
                sys.stderr.write('Error opening output file: {}\n'.format(fName))
                return
            outfile.write(outMsg)
            outfile.close()

    return

# Initialize bacic report varibles for individual reports
def initReportVars():
    # Get header and column info
    return len(rptColumns), fldDefs, globs.report.reportOpts, rptColumns, globs.report.reportTits

def rptTop(rOpts, nFlds):
    # Start HTML and text messages

    msgHtml = '<html><head></head><body>\n'
    msgText = ''
    msgCsv = ''
    if rOpts['lastseensummary'] == 'top':      # add summary to top of report
        msgHtml2, msgText2, msgCsv2 =  lastSeenTable(globs.report.reportOpts)
        msgHtml += msgHtml2 + '<br>\n'
        msgText += msgText2 + '\n'
        msgCsv += msgCsv2 + '\n'

    msgHtml += '<table border={} cellpadding="{}">'.format(rOpts['border'], rOpts['padding'])

    # Add report title
    msgHtml += '<tr><td align="center" colspan="{}" bgcolor="{}"><b>{}</b></td></tr>\n'.format(nFlds, rOpts['titlebg'], rOpts['reporttitle'])
    msgText += '{}\n'.format(rOpts['reporttitle'])
    msgCsv += '\"{}\"\n'.format(rOpts['reporttitle'])

    return msgHtml, msgText, msgCsv
    

def rptPrintTitles(html, text, csv, cols):
    # Start column headings for HTML Message
    html += '<tr>'

    # Now, generate headings for the columns that are left
    # Some may have been removed in the .rc file configuration, [headings] section
    for col in cols:
        html += printTitle(col, 'html')
        text += printTitle(col, 'text')
        csv += printTitle(col, 'csv')

    # End of column headings row
    html += '</tr>\n'
    text += '\n'
    csv += '\n'

    return html, text, csv

def rptBottom(html, text, csv, start, nfld):

    # Add final rows & close
    runningTime = 'Running Time: {:.3f} seconds.'.format(time.time() - start)
    html += '<tr><td colspan={} align="center"><b>{}</b></td></tr>\n'.format(nfld, runningTime)
    html += '</table>'
    text += runningTime + '\n'
    csv += '\"' + runningTime + '\"\n'

    if globs.report.reportOpts['lastseensummary'] == 'bottom':      # add summary to top of report
        msgHtml2, msgText2, msgCsv2 =  lastSeenTable(globs.report.reportOpts)
        html += '<br>' + msgHtml2 + '\n'
        text += '\n' + msgText2
        csv += '\n' + msgCsv2

    html += '<br><br>Report generated by <a href=\'https://github.com/HandyGuySoftware/dupReport\'>dupReport</a> Version {}.{}.{} ({})<br>'.format(globs.version[0], globs.version[1], globs.version[2], globs.status)
    html += '</body></html>'
    text += '\n\nReport generated by dupReport (https://github.com/HandyGuySoftware/dupReport) Version {}.{}.{} ({})'.format(globs.version[0], globs.version[1], globs.version[2], globs.status)
    csv += '\n\"Report generated by dupReport (https://github.com/HandyGuySoftware/dupReport) Version {}.{}.{} ({})\"'.format(globs.version[0], globs.version[1], globs.version[2], globs.status)

    return html, text, csv

def pastBackupWarningThreshold(src, dest, nDays, opts):
    globs.log.write(1,'report.pastBackupWarningThreshold({}, {}, {})'.format(src, dest, nDays))

    srcDest = '{}{}{}'.format(src, globs.opts['srcdestdelimiter'], dest)

    # Look for nobackup warning threshold
    # First look in pair-specific section
    # Then look in main section
    nbwVal = globs.optionManager.getRcOption(srcDest, 'nobackupwarn')
    if nbwVal is not None:
        nbwVal = int(nbwVal)    # getRcOption returns a string, we need an int
    else:   # No pair-specific option. Use the global option from [main]
        nbwVal = opts['nobackupwarn']

    globs.log.write(3,'Nobackup warning threshold is {} days.'.format(nbwVal))

    if nbwVal == 0:     # 0 = do not warn on missing backups
        retVal = False
    else:
        if nDays >= nbwVal:     # Past threshold - need to warn
            retVal = True
        else:
            retVal = False

    globs.log.write(3,'pastBackupWarningThreshold returning {}'.format(retVal))
    return retVal


def buildWarningMessage(source, destination, nDays, lastTimestamp, opts):
    globs.log.write(1,'buildWarningMessage({}, {}, {}, {})'.format(source, destination, nDays, lastTimestamp))
    lastDateStr, lastTimeStr = drdatetime.fromTimestamp(lastTimestamp)
    srcDest = '{}{}{}'.format(source, globs.opts['srcdestdelimiter'], destination)

    subj = globs.optionManager.getRcOption(srcDest, 'nbwsubject')
    if subj is None:
        subj = opts['nbwsubject']
    globs.log.write(3,'subj(original)={}'.format(subj))
    subj = subj.replace('#SOURCE#',source).replace('#DESTINATION#', destination).replace('#DELIMITER#', globs.opts['srcdestdelimiter']).replace('#DAYS#', str(nDays)).replace('#DATE#', lastDateStr).replace('#TIME#', lastTimeStr)
    globs.log.write(3,'subj(modified)={}'.format(subj))

    warnHtml='<html><head></head><body><table border=\"{}\" cellpadding=\"{}\">\n'.format(opts['border'],opts['padding'])
    warnHtml += '<tr><td bgcolor="#FF0000" align="center"><b>Backup Warning for {}{}{}</b></td></tr>\n'.format(source, globs.opts['srcdestdelimiter'], destination)
    warnHtml += '<tr><td bgcolor="#E6E6E6" align="center">Your last backup from {} to {} was on {} at {} - {} days ago.</td></tr>\n'.format(source, destination, lastDateStr,lastTimeStr, nDays)
    warnHtml += '<tr><td align="center"> {} has not been backed up in the last {} days!<br>'.format(source, nDays)
    warnHtml += "If {} has been powered off or has been offline for the last {} days, no further action is required.<br>\n".format(source, nDays)
    warnHtml += 'Your backups will resume the next time {} is brought back online.<br>'.format(source)
    warnHtml += 'Otherwise, please make sure your Duplicati service is running and/or manually run a backup as soon as possible!</td></tr>\n'
    warnHtml += '</table></body></html>'

    warnText = 'Backup Warning for {}{}{}!\n\n'.format(source,globs.opts['srcdestdelimiter'],destination)
    warnText += 'Your last backup from {} to {} was on {} at {} - {} days ago.\n\n'.format(source, destination, lastDateStr,lastTimeStr, nDays)
    warnText += "If {} has been powered off or has been offline for the last {} days, no further action is required.\n".format(source, nDays)
    warnText += 'Your backups will resume the next time {} is brought back online.\n'.format(source)
    warnText += 'Otherwise, please make sure your Duplicati service is running and/or manually run a backup as soon as possible!\n'
    
    sender = globs.opts['outsender']
    receiver = globs.optionManager.getRcOption(srcDest, 'receiver')
    if receiver is None:
        receiver = globs.opts['outreceiver']

    globs.log.write(3, 'Sending message to {}'.format(receiver))
    return warnHtml, warnText, subj, sender, receiver


def getLatestTimestamp(src, dest):
    globs.log.write(1, 'getLatestTimestamp({}, {})'.format(src, dest))

    # Get last timestamp from backupsets
    sqlStmt = 'SELECT lastTimestamp FROM backupsets WHERE source = \"{}\" AND destination = \"{}\"'.format(src, dest)
    dbCursor = globs.db.execSqlStmt(sqlStmt)
    lastTimestamp = dbCursor.fetchone()
    if lastTimestamp[0] is not None:
            # See if there is a later timestamp waiting in the email table
            sqlStmt = 'SELECT max(endTimeStamp) FROM emails WHERE sourceComp = \'{}\' AND destComp= \'{}\' AND endTimeStamp > {}'.format(src, dest, lastTimestamp[0])
            dbCursor = globs.db.execSqlStmt(sqlStmt)
            lastEmailStamp = dbCursor.fetchone()
            if lastEmailStamp[0]:
                # Found one - this is the latest timestamp for that srcDest pair
                globs.log.write(2, 'Returning email timestamp: {}'.format(lastEmailStamp[0]))
                return lastEmailStamp[0]
            else:
                # Nothing newer in database - return latest time from backupsets
                globs.log.write(2, 'Returning backupsets timestamp: {}'.format(lastTimestamp[0]))
                return lastTimestamp[0]
    else:
        # This should never happen
        globs.log.write(2, 'Didn\'t find any timestamp for {}-{}: something is wrong!'.format(src, dest))
        return None

def getLastSeenColor(opts, days, interval = 0):
    
    # Need to account for the backup interval when calculating "overtime" days
    if interval != 0:
        ndays = days - interval
    else:
        ndays = days

    if ndays <= opts['lastseenlow']:
        return opts['lastseenlowcolor']
    elif ndays <= opts['lastseenmed']:
        return opts['lastseenmedcolor']
    else:
        return opts['lastseenhighcolor']

def pastBackupInterval(srcDest, days):
    # Get backup interval from rc file. Default is 0
    backupInterval = globs.optionManager.getRcOption(srcDest, 'backupinterval')
    if backupInterval is None:
        backupInterval = 0
    else:
        backupInterval = int(backupInterval)    # Change value to an int type

    # If we're not past the backup interval, skip reporting this src/dest as missing
    if days >= backupInterval:
        return True, backupInterval     # At or past the backup interval
    else:
        return False, backupInterval    # Not yet past the backup interval

def lastSeenTable(opts):
    globs.log.write(1, 'report.lastSeenTable()')

    msgHtml = '<table border={} cellpadding="{}"><td align=\"center\" colspan = \"4\"><b>{}</b></td>\n'.format(opts['border'],opts['padding'], opts['lastseensummarytitle'])
    msgHtml += '<tr><td><b>Source</b></td><td><b>Destination</b></td><td><b>Duplicati Version</b></td><td><b>Last Seen</b></td></tr>\n'
    msgText = '***** {} *****\n(Source-Destination-Duplicati Version-Last Seen)\n'.format(opts['lastseensummarytitle'])
    msgCsv = '\"{}\",\n\"Source\",\"Destination\",\"Duplicati Version\",\"Last Seen\"\n'.format(opts['lastseensummarytitle'])

    dbCursor = globs.db.execSqlStmt("SELECT source, destination, lastTimestamp FROM backupsets ORDER BY source, destination")
    sdSets = dbCursor.fetchall()
    globs.log.write(3,'sdSets=[{}]'.format(sdSets))
    for source, destination, lastTimestamp in sdSets:

        # If src/dest is known offline, skip
        srcDest = '{}{}{}'.format(source, globs.opts['srcdestdelimiter'], destination)
        offline = globs.optionManager.getRcOption(srcDest, 'offline')
        if offline != None:
            if offline.lower() in ('true'):
                continue

        lastDate = drdatetime.fromTimestamp(lastTimestamp)
        days = drdatetime.daysSince(lastTimestamp)

        dbCursor = globs.db.execSqlStmt("SELECT dupversion FROM emails WHERE sourcecomp='{}' AND destcomp='{}' and dupversion != '' ORDER BY emailtimestamp DESC".format(source, destination))
        dvPtr = dbCursor.fetchone()
        # Issue #123
        # Earlier versions of Duplicati did not return the version number in the email. Need to account for that.
        dVersion = dvPtr[0] if dvPtr != None else ''

        result, interval = pastBackupInterval(srcDest, days)
        if result is False:
            globs.log.write(3,'source=[{}] destination=[{}] dupversion=[{}] lastTimestamp=[{}] lastDate=[{}] days=[{}]'.format(source, destination, dVersion, lastTimestamp, lastDate, days))
            msgHtml += '<tr><td>{}</td><td>{}</td><td>{}</td><td>{} {} ({} days ago. Backup interval is {} days)</td></tr>\n'.format(source, destination, dVersion, lastDate[0], lastDate[1], days, interval)
            msgText += '{}{}{} Version {}: Last seen on {} {} ({} days ago. Backup interval is {} days.)\n'.format(source, globs.opts['srcdestdelimiter'], destination, dVersion, lastDate[0], lastDate[1], days, interval)
            msgCsv += '\"{}\",\"{}\",\"{}\",\"{} {} ({} days ago. Backup interval is {} days.)\"\n'.format(source, destination, dVersion, lastDate[0], lastDate[1], days, interval)
        else:            
            globs.log.write(3,'source=[{}] destination=[{}] dupversion=[{}] lastTimestamp=[{}] lastDate=[{}] days=[{}]'.format(source, destination, dVersion, lastTimestamp, lastDate, days))
            msgHtml += '<tr><td>{}</td><td>{}</td><td>{}</td><td bgcolor=\"{}\">{} {} ({} days ago)</td></tr>\n'.format(source, destination, dVersion, getLastSeenColor(opts, days), lastDate[0], lastDate[1], days)
            msgText += '{}{}{} Version {}: Last seen on {} {} ({} days ago)\n'.format(source, globs.opts['srcdestdelimiter'], destination, dVersion, lastDate[0], lastDate[1], days)
            msgCsv += '\"{}\",\"{}\",\"{}\",\"{} {} ({} days ago)\"\n'.format(source, destination, dVersion, lastDate[0], lastDate[1], days)

    msgHtml += '</table>'

    return msgHtml, msgText, msgCsv

# Truncate warning & error messages
def truncateWarnErrMsgs(msg, msgLen, warn, warnLen, err, errLen, logData, logDataLen):

    # Set defaults to original messages
    msgRet = msg
    warnRet = warn
    errRet = err
    logDataRet = logData

    # Truncate string if length of string is > desired length
    if msgLen != 0:
        msgRet = (msg[:msgLen]) if len(msg) > msgLen else msg  
    if warnLen != 0:
        warnRet = (warn[:warnLen]) if len(warn) > warnLen else warn  
    if errLen != 0:
        errRet = (err[:errLen]) if len(err) > errLen else err
    if logDataLen != 0:
        logDataRet = (logData[:logDataLen]) if len(logData) > logDataLen else logData

    return msgRet, warnRet, errRet, logDataRet

# Class for report management
class Report:

    def __init__(self):
        globs.log.write(1,'Report:__init__()')
        
        self.reportOpts = {}    # Dictionary of report options
        self.reportTits = {}    # Dictionary of report titles
        titTmp = {}
        
        # Read name/value pairs from [report] section
        self.reportOpts = globs.optionManager.getRcSection('report')

        # Fix some of the data field types - integers
        for item in ('border', 'padding', 'nobackupwarn', 'lastseenlow', 'lastseenmed', 'truncatemessage', 'truncatewarning', 'truncateerror', 'truncatelogdata'):
            self.reportOpts[item] = int(self.reportOpts[item])

        # Fix some of the data field types - boolean
        for item in ('showsizedisplay', 'displaymessages', 'displaywarnings', 'displayerrors', 'displaylogdata', 'repeatheaders', 'durationzeroes'):
            self.reportOpts[item] = self.reportOpts[item].lower() in ('true')   

        # Basic field value checking
        # See if valid report name
        rptName = globs.progPath + '/rpt_' + self.reportOpts['style'] + '.py'
        validReport = os.path.isfile(rptName)
        if not validReport:
            globs.log.err('Invalid RC report style option in [report] section: style cannot be \'{}\''.format(self.reportOpts['style']))
            globs.closeEverythingAndExit(1)

        if self.reportOpts['sortby'] not in ('source', 'destination', 'date', 'time'):
            globs.log.err('Invalid RC file sorting option in [report] section: sortby cannot be \'{}\''.format(self.reportOpts['sortby']))
            globs.closeEverythingAndExit(1)

        if self.reportOpts['sizedisplay'].lower()[:4] not in ('byte', 'mega', 'giga'):
            globs.log.err('Invalid RC file size display option in [report] section: sizedisplay cannot be \'{}\''.format(self.reportOpts['sizedisplay']))
            globs.closeEverythingAndExit(1)

        if self.reportOpts['lastseensummary'].lower()[:3] not in ('non', 'top', 'bot'):
            globs.log.err('Invalid RC file size display option in [report] section: lastseensummary cannot be \'{}\''.format(self.reportOpts['lastseensummary']))
            globs.closeEverythingAndExit(1)

        # Get list of existing headers in [headings] section
        titTmp = globs.optionManager.getRcSection('headings')
        if titTmp is not None:
            for name in titTmp:
                if titTmp[name] == '':  # Empty string means column is not to be displayed
                    rptColumns.remove(name)
                else:
                    self.reportTits[name] = titTmp[name]

        # Remove these columns from the column list. We deal with these separately in the reports
        rptColumns.remove('jobmessages')
        rptColumns.remove('jobwarnings')
        rptColumns.remove('joberrors')
        rptColumns.remove('joblogdata')

        globs.log.write(3, 'Report: reportOps=[{}]'.format(self.reportOpts))
        globs.log.write(3, 'Report: reportTits=[{}]'.format(self.reportTits))
        globs.log.write(3, 'Report: rptColumns=[{}]'.format(rptColumns))

        return None

    # Extract the data needed for the report and move it to the report table in the database
    # This data will be picked up later by the specific report module
    def extractReportData(self):
        globs.log.write(1, 'extractReportData()')

        # Initialize report table. Delete all existing rows
        dbCursor = globs.db.execSqlStmt("DELETE FROM report")

        # Select source/destination pairs from database
        sqlStmt = "SELECT source, destination, lastTimestamp, lastFileCount, lastFileSize FROM backupsets ORDER BY source, destination"

        # Loop through backupsets table and then get latest activity for each src/dest pair
        dbCursor = globs.db.execSqlStmt(sqlStmt)
        bkSetRows = dbCursor.fetchall()
        globs.log.write(2, 'bkSetRows=[{}]'.format(bkSetRows))
        for source, destination, lastTimestamp, lastFileCount, lastFileSize in bkSetRows:
            globs.log.write(3, 'Src=[{}] Dest=[{}] lastTimestamp=[{}] lastFileCount=[{}] lastFileSize=[{}]'.format(source, 
                destination, lastTimestamp, lastFileCount, lastFileSize))

            # Select all activity for src/dest pair since last report run
            sqlStmt = 'SELECT dupVersion, endTimestamp, beginTimeStamp, duration, examinedFiles, sizeOfExaminedFiles, addedFiles, deletedFiles, modifiedFiles, \
                filesWithError, parsedResult, warnings, errors, messages, logdata FROM emails WHERE sourceComp=\'{}\' AND destComp=\'{}\' \
                AND  endTimestamp > {} order by endTimestamp'.format(source, destination, lastTimestamp)
            dbCursor = globs.db.execSqlStmt(sqlStmt)

            emailRows = dbCursor.fetchall()
            globs.log.write(3, 'emailRows=[{}]'.format(emailRows))
            if emailRows: 
                # Loop through each new activity and report
                for dupversion, endTimeStamp, beginTimeStamp, duration, examinedFiles, sizeOfExaminedFiles, addedFiles, deletedFiles, modifiedFiles, \
                    filesWithError, parsedResult, warnings, errors, messages, logdata in emailRows:
            
                    # Determine file count & size difference from last run
                    examinedFilesDelta = examinedFiles - lastFileCount
                    globs.log.write(3, 'examinedFilesDelta = {} - {} = {}'.format(examinedFiles, lastFileCount, examinedFilesDelta))
                    fileSizeDelta = sizeOfExaminedFiles - lastFileSize
                    globs.log.write(3, 'fileSizeDelta = {} - {} = {}'.format(sizeOfExaminedFiles, lastFileSize, fileSizeDelta))

                    # Convert from timestamp to date & time strings
                    sqlStmt = "INSERT INTO report (source, destination, timestamp, duration, examinedFiles, examinedFilesDelta, sizeOfExaminedFiles, fileSizeDelta, \
                        addedFiles, deletedFiles, modifiedFiles, filesWithError, parsedResult, messages, warnings, errors, dupversion, logdata) \
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
                    rptData = (source, destination, endTimeStamp, duration, examinedFiles, examinedFilesDelta, sizeOfExaminedFiles, fileSizeDelta, addedFiles, deletedFiles, modifiedFiles, filesWithError, parsedResult, messages, warnings, errors, dupversion, logdata)
                    globs.db.execReportInsertSql(sqlStmt, rptData)

                    # Update latest activity into into backupsets
                    sqlStmt = 'UPDATE backupsets SET lastFileCount={}, lastFileSize={}, \
                        lasttimestamp=\'{}\' WHERE source=\'{}\' AND destination=\'{}\''.format(examinedFiles, sizeOfExaminedFiles, \
                        endTimeStamp, source, destination)
                    globs.db.execSqlStmt(sqlStmt)
                    globs.db.dbCommit()

                    # Set last file count & size the latest information
                    lastFileCount = examinedFiles
                    lastFileSize = sizeOfExaminedFiles



