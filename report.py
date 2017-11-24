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
import configparser
from configparser import SafeConfigParser 
import sys

# Import dupReport modules
import globs
import db
import drdatetime

# fldDefs = Dictionary of field definitions
fldDefs = {
    # field                 [0]Title                [1]dbField             [2]alignment[3]gig/meg? [4hdrDef]   [5]normDef   [6]megaDef  [7]gigaDef
    'source':               ('Source',              'source',              'left',     False,      '20',       '20'),
    'destination':          ('Destination',         'destination',         'left',     False,      '20',       '20'),
    'date':                 ('Date',                'dateStr',             'left',     False,      '13',       '13'),
    'time':                 ('Time',                'timeStr',             'left',     False,      '11',       '11'),
    'files':                ('Files',               'examinedFiles',       'right',    False,      '>12',      '>12,'),
    'filesplusminus':       ('+/-',                 'examinedFilesDelta',  'right',    False,      '>12',      '>+12,'),
    'size':                 ('Size',                'sizeOfExaminedFiles', 'right',    True,       '>12',      '>20,',      '>15,.2f', '>12,.2f'),
    'sizeplusminus':        ('+/-',                 'fileSizeDelta',       'right',    True,       '>12',      '>+20,',      '>+15,.2f', '>+12,.2f'),
    'added':                ('Added',               'addedFiles',          'right',    False,      '>12',      '>12,'),
    'deleted':              ('Deleted',             'deletedFiles',        'right',    False,      '>12',      '>12,'),
    'modified':             ('Modified',            'modifiedFiles',       'right',    False,      '>12',      '>12,'),
    'errors':               ('Errors',              'filesWithError',      'right',    False,      '>12',      '>12,'),
    'result':               ('Result',              'parsedResult',        'left',     False,      '<13',      '<13'),
    'jobmessages':          ('JobMessages',         'messages',            'center',   False,      '^50',      '^50'),
    'jobwarnings':          ('JobWarnings',         'warnings',            'center',   False,      '^50',      '^50'),
    'joberrors':            ('JobErrors',           'errors',              'center',   False,      '^50',      '^50')
    }

# List of columns in the report
# This can be modified by emptying the value of the field names in the [headings] section of the .rc file
rptColumns = ['source', 'destination', 'date', 'time', 'files', 'filesplusminus', 'size', 'sizeplusminus', 'added', 'deleted', 'modified', 'errors', 'result']

# Provide a field format specification for the titles in the report
def printTitle(fld, typ):
    outStr = None

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
        outStr = '{:{fmt}}'.format(fldDefs[fld][0], displayAddOn, fmt=fldDefs[fld][4])

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
        
        # Create HTML and text versions of the format string
        outHtml = '<td align=\"{}\">{:{fmt}}</td>'.format(fldDefs[fld][2], v, fmt=outFmt)
        outTxt = '{:{fmt}}'.format(v, fmt=outFmt)
    else:
        # Create HTML and text versions of the format string
        outHtml = '<td align=\"{}\">{}</td>'.format(fldDefs[fld][2], val)
        outTxt = '{:{fmt}}'.format(val, fmt=fldDefs[fld][5])

    if fmt == 'html':
        return outHtml
    elif fmt == 'text':
        return outTxt


class Report:

    def __init__(self):
        globs.log.write(1,'Report:__init__()')
        
        self.reportOpts = {}    # Dictionary of report options
        self.reportTits = {}    # Dictionary of report titles
        
        # Open .rc file
        rcConfig = SafeConfigParser()
        rv=rcConfig.read(globs.opts['rcpath'])

        # Read name/value pairs from [report] section
        for name, value in rcConfig.items('report'):
            self.reportOpts[name] = value

        # Fix some of the data field types
        self.reportOpts['border'] = int(self.reportOpts['border'])    # integer
        self.reportOpts['padding'] = int(self.reportOpts['padding'])  # integer
        self.reportOpts['showsizedisplay'] = self.reportOpts['showsizedisplay'].lower() in ('true')     # Convert to boolean
        self.reportOpts['displaymessages'] = self.reportOpts['displaymessages'].lower() in ('true')     # Convert to boolean
        self.reportOpts['displaywarnings'] = self.reportOpts['displaywarnings'].lower() in ('true')     # Convert to boolean
        self.reportOpts['displayerrors'] = self.reportOpts['displayerrors'].lower() in ('true')         # Convert to boolean

        # Basic field value checking
        if self.reportOpts['style'] not in ('standard', 'grouped'):
            globs.log.err('Invalid RC file option in [report] section: style cannot be \'{}\''.format(self.reportOpts['style']))
            sys.exit(1)
        if self.reportOpts['sortorder'] not in ('source', 'destination'):
            globs.log.err('Invalid RC file option in [report] section: sortorder cannot be \'{}\''.format(self.reportOpts['sortorder']))
            sys.exit(1)
        if self.reportOpts['groupby'] not in ('source', 'destination', 'date'):
            globs.log.err('Invalid RC file option in [report] section: groupby cannot be \'{}\''.format(self.reportOpts['groupby']))
            sys.exit(1)
        if self.reportOpts['sizedisplay'].lower()[:4] not in ('byte', 'mega', 'giga'):
            globs.log.err('Invalid RC file option in [report] section: sizedisplay cannot be \'{}\''.format(self.reportOpts['sizedisplay']))
            sys.exit(1)

        # Read name/value pairs from [headings] section
        for name, value in rcConfig.items('headings'):
           if value != '':
              self.reportTits[name] = value
           else: 
               # Column was eliminated from .rc file by emptying the 'value' portion of the name/value pair
               # We need to remove it from the rptColumns list so we don't go looking for it later
               rptColumns.remove(name)

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
        sqlStmt = "SELECT source, destination, lastTime, lastFileCount, lastFileSize from backupsets"
        # How should report be sorted?
        if self.reportOpts['sortorder'] == 'source':
            sqlStmt = sqlStmt + " order by source, destination"
        else:
            sqlStmt = sqlStmt + " order by destination, source"

        # Loop through backupsets table and then get latest activity for each src/dest pair
        dbCursor = globs.db.execSqlStmt(sqlStmt)
        bkSetRows = dbCursor.fetchall()
        globs.log.write(2, 'bkSetRows=[{}]'.format(bkSetRows))
        for source, destination, lastTime, lastFileCount, lastFileSize in bkSetRows:
            globs.log.write(3, 'Src=[{}] Dest=[{}] lastTime=[{}] lastFileCount=[{}] lastFileSize=[{}]'.format(source, 
                destination, lastTime, lastFileCount, lastFileSize))

            # Select all activity for src/dest pair since last report run
            sqlStmt = 'SELECT endTimestamp, examinedFiles, sizeOfExaminedFiles, addedFiles, deletedFiles, modifiedFiles, \
                filesWithError, parsedResult, warnings, errors, messages FROM emails WHERE sourceComp=\'{}\' AND destComp=\'{}\' \
                AND  endTimestamp > {} order by endTimestamp'.format(source, destination, lastTime)
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
                        lasttime=\'{}\' WHERE source=\'{}\' AND destination=\'{}\''.format(examinedFiles, sizeOfExaminedFiles, \
                        endTimeStamp, source, destination)
                    globs.db.execSqlStmt(sqlStmt)
                    globs.db.dbCommit()

                    # Set last file count & size the latest information
                    lastFileCount = examinedFiles
                    lastFileSize = sizeOfExaminedFiles