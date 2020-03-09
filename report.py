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
"""
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
"""
fldDefs = {
    # field                 [0]alignment    [1]hdrDef   [2]colDef
    'source':               ('left',        '20',       '20'),
    'destination':          ('left',        '20',       '20'),
    'dupversion':           ('left',        '20',       '20'),
    'date':                 ('left',        '13',       '13'),
    'time':                 ('left',        '11',       '11'),
    'duration':             ('right',       '15',       '15'),
    'examinedFiles':        ('right',       '>12',      '>12,'),
    'examinedFilesDelta':   ('right',       '>12',      '>+12,'),
    'sizeOfExaminedFiles':  ('right',       '>20',      '>20,.2f'),
    'fileSizeDelta':        ('right',       '>20',      '>20,.2f'),
    'addedFiles':           ('right',       '>12',      '>12,'),
    'deletedFiles':         ('right',       '>12',      '>12,'),
    'modifiedFiles':        ('right',       '>12',      '>12,'),
    'filesWithError':       ('right',       '>12',      '>12,'),
    'parsedResult':         ('left',        '>13',      '>13'),
    'messages':             ('center',      '^50',      '^50'),
    'warnings':             ('center',      '^50',      '^50'),
    'errors':               ('center',      '^50',      '^50'),
    'logdata':              ('center',      '^50',      '^50')
    }



# List of columns in the report
rptColumns = ['source', 'destination', 'dupversion', 'date', 'time', 'duration', 'files', 'filesplusminus', 'size',  'sizeplusminus', 'added', 'deleted', 'modified', 'errors', 'result', 'jobmessages', 'jobwarnings', 'joberrors', 'joblogdata']

# List of allowable keyword substitutions
keyWordList = { 
    #  database field: keyword mask
    'source': '#SOURCE#',
    'destination': '#DESTINATION#', 
    'date': '#DATE#', 
    'time': '#TIME#'
    }

# Build an SQL query statement based on a given report's options ('groupby', 'columns', and 'columsort')
# If (whereOpts != None) whereOpts will be a list of columns and values those columns have to match
# If (groupBy is True), you're trying to group query results, so need to add a 'DISTINCT' clause to the SQL statement
def buildQuery(options, whereOpts = None, groupby=False):
    if groupby:
        sqlStmt = 'SELECT DISTINCT ' + buildSelectList(options['groupby']) + ' FROM report '
    else:
        sqlStmt = 'SELECT ' + buildSelectList(options['columns']) + ' FROM report '

    if whereOpts:
        sqlStmt += ' WHERE ' + buildWhereClause(options['groupby'], whereOpts) 

    if groupby:
        sqlStmt += ' ORDER BY ' + buildOrderList(options['groupby']) 
    elif 'columnsort' in options:
        sqlStmt += ' ORDER BY ' + buildOrderList(options['columnsort']) 
    
    return sqlStmt

# Build a list of fields to select based on 'list' 
def buildSelectList(list):
    selectString=''
    for i in range(len(list)):
        selectString += list[i][0] + ' '

        # More fields to add?
        if  i != (len(list)-1):
            selectString += ', '

    return selectString

# Build the WHERE clause of the SQL query.
# Do this by parsing through the "groupby" option of the report definition
# 'vals' are the values the 'groupby' fields must match
def buildWhereClause(grpList, vals):
    whereString = ''
    for i in range(len(grpList)):
        whereString += grpList[i][0] + ' = \'' + str(vals[i]) + '\''

        # Are there more where clauses to add?
        if i != (len(grpList) - 1):
            whereString += ' AND '
    return whereString

# Build the ORDER BY clause of the SQL query.
# Do this by parsing through the "columsort" option of the report definition
# 'list' is a list of (column, sortorder) tuples
def buildOrderList(list):
    sortString=''
    for i in range(len(list)):
        sortString += list[i][0] + ' '
        # ascending or descending?
        sortString += 'ASC ' if 'asc' in list[i][1] else 'DESC '
        
        # Are there more sort order fields to add?
        if  i != (len(list)-1):
            sortString += ', '

    return sortString

# Take .rc file option and split into a list structure
# Input format is:
#   option = <item>[:modifier] [, <item>[: modifier]]...
def splitRcIntoList(inputString):
    iniList = []

    # Multiline inputs have newlines (\n) built into them
    # Strip newlines & split along comma delimeters
    # Remove them and convert to list, split by commas
    strTmp = inputString.replace('\n','').split(',')
    
    # Loop through each value in the list
    for i in range(len(strTmp)):
        splitVal = strTmp[i].split(':')             # Split based on ':'
        if len(splitVal) == 1:                      # Len == 1 if there was no ':' (i.e. just a value)
            iniList.append([splitVal[0].strip()])   # Strip while space off end and append to list
        else:                                       # Len == 2 if there was a ':' (i.e. item:modifier)
            iniList.append([splitVal[0].strip(), splitVal[1].strip()])  # Strip while space off end and append to list

    return iniList

# Take data from report tablle and build the resulting report structure.
# Output structure will be used to generate the final report
# 'reportStructure' is the report options as extracted from the .rc file
# See docs/DataStructures/ConfigFormat for schema of reportStructure
# See docs/DataStructures/ReportFormat for schema of reportOutput
def buildReportOutput(reportStructure):

    reportOutput = {}
    reportOutput['sections'] = []

    # Loop through report configurations
    for report in reportStructure['sections']:
        
        # singleReport is the output for just this specific report. 
        # It will be appended to reportOutput once it is filled in.
        # This is how we produce multiple reports from the same run.
        singleReport = {}

        # Copy basic report information from the report definition
        singleReport['name'] = report['name']
        singleReport['columnCount'] = len(report['options']['columns'])
        singleReport['columnNames'] = []
        for i in range(len(report['options']['columns'])):
            singleReport['columnNames'].append([report['options']['columns'][i][0], report['options']['columns'][i][1]])
        singleReport['title'] = report['options']['title']

        # If we're not showing errors, messages, etc inline, get an adjusted list of the inline column names and count
        singleReport['inlineColumnCount'], singleReport['inlineColumnNames'] = adjustColumnInfo(singleReport['columnCount'], singleReport['columnNames'], report['options']['weminline'])

        # Determine how the report is grouped
        singleReport['groups'] = []
        sqlStmt = buildQuery(report['options'], groupby=True)
        dbCursor = globs.db.execSqlStmt(sqlStmt)
        groupList = dbCursor.fetchall()

        # Loop through the defined sections and create a new section for each group
        for groupName in groupList:
            groupIndex = len(singleReport['groups'])  # This will be the index number of the next element we add
            singleReport['groups'].append({})

            # Build the subheading (title) for the group
            if 'groupheading' in report['options']:                 # Group heading already defined
                grpHeading = report['options']['groupheading']
            else:                                                   # Group heading not defined. Build it from 'groupby' columns
                grpHeading = ''
                for i in range(len(groupName)):
                    grpHeading += str(groupName[i]) + ' '
                singleReport['groups'][groupIndex]['groupHeading'] = grpHeading

            # Substitute keywords for actual values
            for keyWdTmp in keyWordList:
                for i in range(len(report['options']['groupby'])):
                    if report['options']['groupby'][i][0] == keyWdTmp: # field is one of the groupbys. See if you need to substitute that value
                        # Check for timestmp expansion
                        if keyWdTmp == 'date':
                            dateStr, timeStr = drdatetime.fromTimestamp(groupName[i], dfmt=globs.opts['dateformat'], tfmt=globs.opts['timeformat'])
                            grpHeading = grpHeading.replace(keyWordList[keyWdTmp], dateStr)
                        elif keyWdTmp == 'time':
                            dateStr, timeStr = drdatetime.fromTimestamp(groupName[i], dfmt=globs.opts['dateformat'], tfmt=globs.opts['timeformat'])
                            grpHeading = grpHeading.replace(keyWordList[keyWdTmp], timeStr)
                        else:
                            grpHeading = grpHeading.replace(keyWordList[keyWdTmp], str(groupName[i]))

            # Perform keyword substutution on the group heading
            singleReport['groups'][groupIndex]['groupHeading'] = grpHeading

            #singleReport['groups'][groupIndex]['columNames'] = singleReport['columnNames']
            singleReport['groups'][groupIndex]['dataRows'] = []

            sqlQuery = {}
            sqlStmt = buildQuery(report['options'], whereOpts = groupName)
            dbCursor = globs.db.execSqlStmt(sqlStmt)
            rowList = dbCursor.fetchall()

            # Loop through all rows for that section
            dataRowIndex = -1
            for rl in range(len(rowList)):
                msgList = {}
                singleReport['groups'][groupIndex]['dataRows'].append([])
                dataRowIndex += 1

                # Print column values to dataRows
                for i in range(len(report['options']['columns'])):
                    # See if we need to substitute date, time, or duration fields
                    if report['options']['columns'][i][0] == 'date':
                        dateStr, timeStr = drdatetime.fromTimestamp(rowList[rl][i], dfmt=globs.opts['dateformat'], tfmt=globs.opts['timeformat'])
                        singleReport['groups'][groupIndex]['dataRows'][dataRowIndex].append(dateStr)
                    elif report['options']['columns'][i][0] == 'time':
                        dateStr, timeStr = drdatetime.fromTimestamp(rowList[rl][i], dfmt=globs.opts['dateformat'], tfmt=globs.opts['timeformat'])
                        singleReport['groups'][groupIndex]['dataRows'][dataRowIndex].append(timeStr)
                    elif report['options']['columns'][i][0] == 'duration':
                        tDiff = drdatetime.timeDiff(rowList[rl][i], report['options']['durationzeroes'])
                        singleReport['groups'][groupIndex]['dataRows'][dataRowIndex].append(tDiff)
                    elif ((report['options']['columns'][i][0] in ['messages', 'warnings', 'errors', 'logdata']) and (report['options']['weminline'] is False)):
                        if rowList[rl][i] != '':
                            msgList[report['options']['columns'][i][0]] = [report['options']['columns'][i][0], report['options']['columns'][i][1], rowList[rl][i]]
                    else:
                        singleReport['groups'][groupIndex]['dataRows'][dataRowIndex].append(rowList[rl][i])

                # If there are warnings, errors, messages to output and we don't want them inline, print separate lines
                if len(msgList) != 0 and report['options']['weminline'] is False:       
                    for msg in msgList:
                        msgList[msg] = truncateWarnErrMsgs(msgList[msg], report['options'])
                        singleReport['groups'][groupIndex]['dataRows'].append([msgList[msg]])
                        dataRowIndex += 1

        reportOutput['sections'].append(singleReport)

    return reportOutput

# Adjust the column layout if error, messages, etc are being tracked on a separate line
def adjustColumnInfo(count, colNames, wemInLine):
    newColCount = count
    newColNames = colNames.copy()
    
    # If errors, messages, etc are put on separate lines (weminline = False), need to adjust column layout in output report
    if wemInLine is False:
        for i in reversed(range(len(colNames))):
            if newColNames[i][0] in ['messages', 'warnings', 'errors', 'logdata']:
                newColNames.pop(i)
                newColCount -= 1
    
    return newColCount, newColNames

def createHtmlOutput(reportStructure, reportOutput):

    msgHtml = '<html><head></head><body>\n'

    rptIndex = -1
    for report in reportOutput['sections']:
        rptIndex += 1
        rptName = report['name']
        rptOptions = reportStructure['sections'][rptIndex]['options']

        # Start table
        msgHtml += '<table border={} cellpadding="{}">\n'.format(rptOptions['border'], rptOptions['padding'])

        # Add title               
        msgHtml += '<tr><td align="center" colspan="{}" bgcolor="{}"><b>{}</b></td></tr>\n'.format(report['inlineColumnCount'], rptOptions['titlebg'], rptOptions['title'])

        # Loop through each group in the report
        grpIndex = -1
        for group in reportOutput['sections'][rptIndex]['groups']:
            grpIndex += 1
            
            # Print group heading
            msgHtml += '<tr><td align="center" colspan="{}" bgcolor="{}"><b>{}</b></td></tr>\n'.format(report['inlineColumnCount'], rptOptions['groupheadingbg'], report['groups'][grpIndex]['groupHeading'])

            # Print column headings
            msgHtml += '<tr>'
            for i in range(len(report['inlineColumnNames'])):
                msgHtml += printTitle(report['inlineColumnNames'][i], rptOptions, 'html')
            msgHtml += '</tr>\n'

            # Print data rows & columns for that group
            for row in report['groups'][grpIndex]['dataRows']:
                msgHtml += '<tr>'
                for column in range(len(row)):
                    if len(row) != 1:  # Standard, multicolumn report 
                        outStr = printField(row[column], report['inlineColumnNames'][column][0], reportStructure['sections'][rptIndex]['options']['sizedisplay'], 'html')
                        msgHtml += '<td align=\"{}\">'.format(fldDefs[report['inlineColumnNames'][column][0]][0]) + outStr + '</td>'
                    else:   # Single column - error, warning, message
                        outStr = printField(row[column][2], row[column][0], reportStructure['sections'][rptIndex]['options']['sizedisplay'], 'html')
                        msgHtml += '<td colspan={} align=\"{}\"><details><summary>{}</summary><p><i>'.format(report['inlineColumnCount'], report['inlineColumnNames'][column][0], row[column][1]) + outStr + '</i></p></details></td>'
                msgHtml += '</tr>\n'
        msgHtml += '</table><br>'

    msgHtml += '</body></html>\n'

    return msgHtml

# Provide a field format specification for the titles in the report
def printTitle(fld, options, typ):
    outStr = None
    globs.log.write(3, 'report.printTitle({}, {})'.format(fld, typ))

    # Need to see if we should add the size display after the heading  (e.g. '(MB)' or '(GB)')
    # This is kind of a cheat, but there is no other more elegant way of doing it
    displayAddOn = '' # Start with nothing
    if ((fld[0] == 'sizeOfExaminedFiles') or (fld[0] == 'fileSizeDelta')):  # These are the only fields that can use the add-on
        if options['showsizedisplay'] is True:  # Do we want to show it, based on .rec config?
            if options['sizedisplay'][:2].lower() == 'mb':    # Need to add (MB)
                displayAddOn = ' (Mb)'
            elif options['sizedisplay'][:2].lower() == 'gb': # giga - need to add (GB)
                displayAddOn = ' (Gb)'
            else: # Unknown, revert to default
                pass

    if typ == 'html':
        outStr = '<td align=\"{}\"><b>{}{}</b></td>'.format(fldDefs[fld[0]][0], fld[1], displayAddOn)
    elif typ == 'text':
        outStr = '{:{fmt}}'.format(fldDefs[fld][0] + displayAddOn, fmt=fldDefs[fld][1])
    elif typ == 'csv':
        outStr = '\"{:{fmt}}\",'.format(fldDefs[fld][0] + displayAddOn, fmt=fldDefs[fld][1])

    globs.log.write(3, 'outStr = {}'.format(outStr))
    return outStr

# Provide a field format specification for the data fields (cells) in the report
def printField(val, fldName, format, type):
    v = val
    outFmt = fldDefs[fldName][2]

    # Process fields based on their type.
    if not isinstance(val,str): # i.e., ints & floats
        # Need to adjust value based on MB/GB specification
        # 'display' option (from reportOutput['sections'][rptIndex]['options']['sizedisplay']) indicates if we want to convert sizes to MB/GB
        if fldName in ['sizeOfExaminedFiles', 'fileSizeDelta']:
            if format[:2].lower() == 'mb':
                v = val / 1000000.00
            elif format[:2].lower() == 'gb':
                v = val / 1000000000.00
        
    # Create HTML, text, and csv versions of the format string
    if type == 'html':
        outStr = '{:{fmt}}'.format(v, fmt=outFmt)
    elif type == 'text':
        outStr = '{:{fmt}}'.format(v, fmt=outFmt)
    elif type == 'csv':
        outStr = '\"{:{fmt}}\",'.format(v, fmt=outFmt)

    return outStr

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
def truncateWarnErrMsgs(msg, options):

    msgRet = msg

    # Truncate string if length of string is > desired length
    if msg[0] == 'errors':
        msgLen = options['truncateerror']
    elif msg[0] == 'messages':
        msgLen = options['truncatemessage']
    elif msg[0] == 'warnings':
        msgLen = options['truncatewarning']
    elif msg[0] == 'logdata':
        msgLen = options['truncatelogdata']

    if msgLen != 0:
        msgRet[2] = (msg[2][:msgLen]) if len(msg[2]) > msgLen else msg[2]  
    
    return msgRet

def splitRcIntoList(inputString):
    iniList = []

    # Strip newlines & split along comma delimeters
    strTmp = inputString.replace('\n','').split(',')
    
    # Loop through each value. 
    for i in range(len(strTmp)):
        tmp2 = strTmp[i].split(':')
        if len(tmp2) == 0: # Empty set. prpbably because there was a comma at the end of the line. just Skip it
            continue
        elif len(tmp2) == 1:
            iniList.append([tmp2[0].strip()])
        else:
            iniList.append([tmp2[0].strip(), tmp2[1].strip()])

    return iniList

def readDefaultOptions(section):
    #tmpDict = {}
    sectionList = globs.optionManager.getRcSection(section)
    #for option in sectionList:
    #    tmpDict[option] = option[1]
    return sectionList

# Class for report management
class Report:
    def __init__(self):
        globs.log.write(1,'Report:__init__()')

        self.rStruct = {}
        
        # Read in the default options
        self.rStruct['defaults'] = globs.optionManager.getRcSection('report')

        # Fix some of the data field types - integers
        for item in ('border', 'padding', 'nobackupwarn', 'lastseenlow', 'lastseenmed', 'truncatemessage', 'truncatewarning', 'truncateerror', 'truncatelogdata'):
            self.rStruct['defaults'][item] = int(self.rStruct['defaults'][item])

        # Fix some of the data field types - boolean
        for item in ('showsizedisplay', 'displaymessages', 'displaywarnings', 'displayerrors', 'displaylogdata', 'repeatheaders', 'durationzeroes', 'weminline'):
            self.rStruct['defaults'][item] = self.rStruct['defaults'][item].lower() in ('true')   
            
        # Get reports that need to run
        layoutSections = splitRcIntoList(self.rStruct['defaults']['layout'])
        self.rStruct['sections'] = []

        # Basic field value checking - TO DO
        isValid = self.validateReportFields(self.rStruct)
        if not isValid:
            pass# Do something here

        # Now, loop through each report and get the specific configurations
        for section in layoutSections:
            rIndex = len(self.rStruct['sections'])   # This will be the index number of the next element we add
            self.rStruct['sections'].append({})
 
            # Create structure to hold configs for that report
            self.rStruct['sections'][rIndex]['name'] = section[0]
            # Copy default options to report-specific options
            self.rStruct['sections'][rIndex]['options'] = self.rStruct['defaults'].copy()

            # Get report-specific options
            optionTmp = readDefaultOptions(section[0])
            #optionTmp = readDefaultOptions(self.parser, section[0])
            for optTmp in optionTmp:
                self.rStruct['sections'][rIndex]['options'][optTmp] = optionTmp[optTmp]

            # Fix some of the data field types - integers
            for item in ('border', 'padding', 'nobackupwarn', 'lastseenlow', 'lastseenmed', 'truncatemessage', 'truncatewarning', 'truncateerror', 'truncatelogdata'):
                if type(self.rStruct['sections'][rIndex]['options'][item]) is not int:
                    self.rStruct['sections'][rIndex]['options'][item] = int(self.rStruct['sections'][rIndex]['options'][item])

            # Fix some of the data field types - boolean
            for item in ('showsizedisplay', 'displaymessages', 'displaywarnings', 'displayerrors', 'displaylogdata', 'repeatheaders', 'durationzeroes', 'weminline'):
                if type (self.rStruct['sections'][rIndex]['options'][item]) is not bool:
                   self.rStruct['sections'][rIndex]['options'][item] = self.rStruct['sections'][rIndex]['options'][item].lower() in ('true')   

        
            # Some options are lists masquerading as strings. Need to split them out into their own list structures
            if 'columns' in self.rStruct['sections'][rIndex]['options']:
                self.rStruct['sections'][rIndex]['options']['columns'] = splitRcIntoList(self.rStruct['sections'][rIndex]['options']['columns']) 
            if 'groupby' in self.rStruct['sections'][rIndex]['options']:
                self.rStruct['sections'][rIndex]['options']['groupby'] = splitRcIntoList(self.rStruct['sections'][rIndex]['options']['groupby']) 
            if 'columnsort' in self.rStruct['sections'][rIndex]['options']:
                self.rStruct['sections'][rIndex]['options']['columnsort'] = splitRcIntoList(self.rStruct['sections'][rIndex]['options']['columnsort']) 
            if 'layout' in self.rStruct['sections'][rIndex]['options']:
                self.rStruct['sections'][rIndex]['options']['layout'] = splitRcIntoList(self.rStruct['sections'][rIndex]['options']['layout']) 
        return None


    def validateReportFields(self, rStruct):
        return True

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

                    # Create date & time fields from timestamp field.
                    # This makes it much easier to extract & sort later on rather than trying to manipulate the timestamp at runtime
                    soloDate, soloTime = drdatetime.fromTimestamp(endTimeStamp, dfmt='YYYY-MM-DD')
                    soloDate += ' 00:00:00'
                    soloTime = '2000-01-01 ' + soloTime
                    reportDateStamp = drdatetime.toTimestamp(soloDate, 'YYYY-MM-DD', 'HH:MM:SS')
                    reportTimeStamp = drdatetime.toTimestamp(soloTime, 'YYYY-MM-DD', 'HH:MM:SS')
                    
                    # Convert from timestamp to date & time strings
                    sqlStmt = "INSERT INTO report (source, destination, timestamp, date, time, duration, examinedFiles, examinedFilesDelta, sizeOfExaminedFiles, fileSizeDelta, \
                        addedFiles, deletedFiles, modifiedFiles, filesWithError, parsedResult, messages, warnings, errors, dupversion, logdata) \
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
                    rptData = (source, destination, endTimeStamp, reportDateStamp, reportTimeStamp, duration, examinedFiles, examinedFilesDelta, sizeOfExaminedFiles, fileSizeDelta, addedFiles, deletedFiles, modifiedFiles, filesWithError, parsedResult, messages, warnings, errors, dupversion, logdata)
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

        return None



