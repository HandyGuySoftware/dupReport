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

# fldDefs = Dictionary of field definitions
fldDefs = {
    # field                 [0]Title                [1]dbField             [2]alignment[3]gig/meg? [4]hdrDef   [5]normDef   [6]megaDef  [7]gigaDef
    'source':               ('Source',              'source',              'left',     False,      '20',       '20'),
    'destination':          ('Destination',         'destination',         'left',     False,      '20',       '20'),
    'date':                 ('Date',                'dateStr',             'left',     False,      '13',       '13'),
    'time':                 ('Time',                'timeStr',             'left',     False,      '11',       '11'),
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
    'joberrors':            ('JobErrors',           'errors',              'center',   False,      '^50',      '^50')
    }

# List of columns in the report
rptColumns = ['source', 'destination', 'date', 'time', 'files', 'filesplusminus', 'size',  'sizeplusminus', 'added', 'deleted', 'modified', 'errors', 'result', 'jobmessages', 'jobwarnings', 'joberrors']

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
        outStr = '<td align=\"{}\">{}{}</td>'.format(fldDefs[fld][2], globs.report.reportTits[fld], displayAddOn)
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
        fsplit = fspec.split(',')
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
    # Table border and padding settings
    msgHtml = '<html><head></head><body><table border={} cellpadding="{}">'.format(rOpts['border'], rOpts['padding'])
    msgText = ''
    msgCsv = ''

    # Add report title
    msgHtml += '<tr><td align="center" colspan="{}" bgcolor="{}"><b>{}</b></td></tr>'.format(nFlds, rOpts['titlebg'], rOpts['reporttitle'])
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
    html += '</tr>'
    text += '\n'
    csv += '\n'

    return html, text, csv

def rptBottom(html, text, csv, start, nfld):

    # Add final rows & close
    runningTime = 'Running Time: {:.3f} seconds.'.format(time.time() - start)
    html += '<tr><td colspan={} align="center"><b>{}</b></td></tr>'.format(nfld, runningTime)
    html += '</table></body></html>'
    text += runningTime + '\n'
    csv += '\"' + runningTime + '\"\n'

    return html, text, csv


# Class for report management
class Report:

    def __init__(self):
        globs.log.write(1,'Report:__init__()')
        
        self.reportOpts = {}    # Dictionary of report options
        self.reportTits = {}    # Dictionary of report titles
        titTmp = {}
        
        # Read name/value pairs from [report] section
        self.reportOpts = globs.optionManager.getRcSection('report')

        # Fix some of the data field types
        self.reportOpts['border'] = int(self.reportOpts['border'])    # integer
        self.reportOpts['padding'] = int(self.reportOpts['padding'])  # integer
        self.reportOpts['showsizedisplay'] = self.reportOpts['showsizedisplay'].lower() in ('true')     # Convert to boolean
        self.reportOpts['displaymessages'] = self.reportOpts['displaymessages'].lower() in ('true')     # Convert to boolean
        self.reportOpts['displaywarnings'] = self.reportOpts['displaywarnings'].lower() in ('true')     # Convert to boolean
        self.reportOpts['displayerrors'] = self.reportOpts['displayerrors'].lower() in ('true')         # Convert to boolean

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
            sqlStmt = 'SELECT endTimestamp, examinedFiles, sizeOfExaminedFiles, addedFiles, deletedFiles, modifiedFiles, \
                filesWithError, parsedResult, warnings, errors, messages FROM emails WHERE sourceComp=\'{}\' AND destComp=\'{}\' \
                AND  endTimestamp > {} order by endTimestamp'.format(source, destination, lastTimestamp)
            dbCursor = globs.db.execSqlStmt(sqlStmt)

            emailRows = dbCursor.fetchall()
            globs.log.write(3, 'emailRows=[{}]'.format(emailRows))
            if emailRows: 
                # Loop through each new activity and report
                for endTimeStamp, examinedFiles, sizeOfExaminedFiles, addedFiles, deletedFiles, modifiedFiles, \
                    filesWithError, parsedResult, warnings, errors, messages in emailRows:
            
                    # Determine file count & size diffeence from last run
                    examinedFilesDelta = examinedFiles - lastFileCount
                    globs.log.write(3, 'examinedFilesDelta = {} - {} = {}'.format(examinedFiles, lastFileCount, examinedFilesDelta))
                    fileSizeDelta = sizeOfExaminedFiles - lastFileSize
                    globs.log.write(3, 'fileSizeDelta = {} - {} = {}'.format(sizeOfExaminedFiles, lastFileSize, fileSizeDelta))

                    # Convert frmo timestamp to date & time strings
                    dateStr, timeStr = drdatetime.fromTimestamp(endTimeStamp)

                    sqlStmt = "INSERT INTO report (source, destination, timestamp, examinedFiles, examinedFilesDelta, sizeOfExaminedFiles, fileSizeDelta, \
                        addedFiles, deletedFiles, modifiedFiles, filesWithError, parsedResult, messages, warnings, errors) \
                        VALUES ('{}', '{}', {}, {}, {}, {}, {}, {}, {}, {}, {}, \"{}\", \"{}\", \"{}\", \"{}\")".format(source, destination, endTimeStamp, examinedFiles, \
                        examinedFilesDelta, sizeOfExaminedFiles, fileSizeDelta, addedFiles, deletedFiles, modifiedFiles, filesWithError, parsedResult, messages, warnings, errors)
                    globs.db.execSqlStmt(sqlStmt)

                    # Update latest activity into into backupsets
                    sqlStmt = 'UPDATE backupsets SET lastFileCount={}, lastFileSize={}, \
                        lasttimestamp=\'{}\' WHERE source=\'{}\' AND destination=\'{}\''.format(examinedFiles, sizeOfExaminedFiles, \
                        endTimeStamp, source, destination)
                    globs.db.execSqlStmt(sqlStmt)
                    globs.db.dbCommit()

                    # Set last file count & size the latest information
                    lastFileCount = examinedFiles
                    lastFileSize = sizeOfExaminedFiles
