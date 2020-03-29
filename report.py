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
import json

# Import dupReport modules
import globs
import db
import drdatetime
import options
import report

# fldDefs = Dictionary of field definitions
fldDefs = {
    # field                 [0]alignment    [1]hdrDef   [2]colDef
    'source':               ('left',        '20',       '20'),
    'destination':          ('left',        '20',       '20'),
    'dupversion':           ('left',        '35',       '35'),
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
    'lastseen':             ('left',        '50',       '50'),
    'messages':             ('center',      '^50',      '^50'),
    'warnings':             ('center',      '^50',      '^50'),
    'errors':               ('center',      '^50',      '^50'),
    'logdata':              ('center',      '^50',      '^50')
    }

# List of all the valid column names that can be used in reports
colNames = ['source','destination','date','time','examinedFiles','examinedFilesDelta','sizeOfExaminedFiles','fileSizeDelta','addedFiles','deletedFiles','modifiedFiles','filesWithError','parsedResult','messages','warnings','errors','duration','logdata','dupversion']

# List of allowable keyword substitutions
keyWordList = { 
    #  database field: keyword mask
    'source':       '#SOURCE#',
    'destination':  '#DESTINATION#', 
    'date':         '#DATE#', 
    'time':         '#TIME#'
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
    
    # Loop through each value. 
    for i in range(len(strTmp)):
        splitVal = strTmp[i].split(':')
        if len(splitVal) == 0: # Empty set. probably because there was a comma at the end of the line. just Skip it
            continue
        elif len(splitVal) == 1:
            iniList.append([splitVal[0].strip()])
        else:
            iniList.append([splitVal[0].strip(), splitVal[1].strip()])

    return iniList

markupDefs = {
    'bold':         0x01,
    'italic':       0x02,
    'underline':    0x04,
    'left':         0x08,
    'center':       0x10,
    'right':         0x20
    }

# Create a markup value based on what's specified in markupDefs
def toMarkup(bold=False, italic=False, underline=False, align='left'):
    markup = 0

    if bold:
        markup += markupDefs['bold'] 
    if italic:
        markup += markupDefs['italic'] 
    if underline:
        markup += markupDefs['underline'] 
    
    markup += markupDefs[align]
    return markup

# Return HTML markup tags based on what's store in a markup variable
def fromMarkup(markup):
    fmtStart = ''
    fmtEnd = ''

    if bool(markup & markupDefs['bold']):
        fmtStart += ' <b> '
        fmtEnd += ' </b> '
    if bool(markup & markupDefs['italic']):
        fmtStart += ' <i> '
        fmtEnd += ' </i> '
    if bool(markup & markupDefs['underline']):
        fmtStart += ' <u> '
        fmtEnd += ' </u> '

    if markup & markupDefs['center']:
        align = 'center'
    elif markup & markupDefs['right']:
        align = 'right'
    else:
        align = 'left'

    return fmtStart, fmtEnd, align

# If errors, messages, etc are put on separate lines (weminline = False), they shouldn't be included in the column layout or count
# Adjust the column layout  & count (inlineColumns, inlineColumnCount to account for this
def adjustColumnInfo(count, colNames, wemInLine):
    newColCount = count
    newColNames = colNames.copy()
    
    if wemInLine is False:
        for i in reversed(range(len(colNames))):
            if newColNames[i][0] in ['messages', 'warnings', 'errors', 'logdata']:
                newColNames.pop(i)
                newColCount -= 1
    
    return newColCount, newColNames

# Provide a field format specification for the titles in the report
def printTitle(fldTuple, options, typ):
    outStr = None
    globs.log.write(3, 'report.printTitle({}, {})'.format(fldTuple[1], typ))

    # Need to see if we should add the size display after the heading  (e.g. '(MB)' or '(GB)')
    # This is kind of a cheat, but there is no other more elegant way of doing it
    displayAddOn = '' # Start with nothing
    if ((fldTuple[0] == 'sizeOfExaminedFiles') or (fldTuple[0] == 'fileSizeDelta')):  # These are the only fields that can use the add-on
        #if options['showsizedisplay'] is True:  # Do we want to show it, based on .rec config?
        if options['sizedisplay'][:2].lower() == 'mb':    # Need to add (MB)
            displayAddOn = ' (Mb)'
        elif options['sizedisplay'][:2].lower() == 'gb': # giga - need to add (GB)
            displayAddOn = ' (Gb)'
        else: # 'None' or Unknown, revert to default
            pass

    if typ == 'html':
        fmtStart, fmtEnd, align = fromMarkup(fldTuple[3])
        outStr = '<td align=\"{}\" bgcolor=\"{}\">{}{}{}{}</td>'.format(align, fldTuple[2], fmtStart, fldTuple[1], displayAddOn, fmtEnd)
    elif typ == 'txt':
        outStr = '{:{fmt}} '.format(fldTuple[1] + displayAddOn, fmt=fldDefs[fldTuple[0]][1])
    elif typ == 'csv':
        outStr = '\"{:{fmt}}\",'.format(fldTuple[1] + displayAddOn, fmt=fldDefs[fldTuple[0]][1])

    globs.log.write(3, 'outStr = {}'.format(outStr))
    return outStr

# Provide a field format specification for the data fields (cells) in the report
def printField(fldTuple, fldName, sizeDisplay, typ, title=None, columnCount=0, summary=False):
    outStr = None

    val = fldTuple[0]

    # Process fields based on their type.
    if not isinstance(val,str): # i.e., ints & floats
        # Need to adjust value based on MB/GB specification
        # 'display' option (from reportOutput['sections'][rptIndex]['options']['sizedisplay']) indicates if we want to convert sizes to MB/GB
        if fldName in ['sizeOfExaminedFiles', 'fileSizeDelta']:
            if sizeDisplay[:2].lower() == 'mb':
                val = val / 1000000.00
            elif sizeDisplay[:2].lower() == 'gb':
                val = val / 1000000000.00
        
    # Create HTML, text, and csv versions of the format string
    if typ == 'html':
        fmtStart, fmtEnd, align = fromMarkup(fldTuple[2])
        if title is None:  # Standard data field
            outStr = '<td align=\"{}\" bgcolor=\"{}\">{}{:{fmt}}{}</td>'.format(align, fldTuple[1], fmtStart, val, fmtEnd, fmt=fldDefs[fldName][2])
        else: # Err/warn/message field
            if summary is True:
                outStr = '<td colspan={} align=\"{}\" bgcolor=\"{}\"><details><summary>{}</summary><p>{}{}{}</details></td>'.format(columnCount, align, fldTuple[1], title, fmtStart, val, fmtEnd)
            else:
                outStr = '<td colspan={} align=\"{}\" bgcolor=\"{}\">{}{}{}</td>'.format(columnCount, align, fldTuple[1], fmtStart, val, fmtEnd)
    elif typ == 'txt':
        if title is None:  # Standard data field
            outStr = '{:{fmt}} '.format(val, fmt=fldDefs[fldName][2])
        else: # Err/warn/message field
            outStr = '{} '.format(val)
    elif typ == 'csv':
        if title is None:  # Standard data field
            outStr = '\"{:{fmt}}\",'.format(val, fmt=fldDefs[fldName][2])
        else: # Err/warn/message field
            outStr = '\"{}\",'.format(val)

    return outStr

# Get running time of program
def getRunningTime(start):
    return 'Running Time: {:.3f} seconds.'.format(time.time() - start)

def sendReportToFiles(reportOutput, startTime):
    # See where the output files are going
    for fspec in globs.ofileList:
        fsplit = fspec[0].split(',')
        fName = fsplit[0]
        fmt = fsplit[1]

        msgContent = globs.report.createFormattedOutput(reportOutput, fmt, startTime) 
        if fName == 'stdout':
            sys.stdout.write(msgContent)
        elif fName == 'stderr':
            sys.stderr.write(msgContent)
        else:
            try:
                outfile = open(fName,'w')
            except (OSError, IOError):
                sys.stderr.write('Error opening output file: {}\n'.format(fName))
                return
            if fmt in ['html', 'txt', 'csv']:
                outfile.write(msgContent)
            else:
                json.dump(msgContent, outfile)
            outfile.close()
    return None

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

# Truncate warning & error messages
def truncateWarnErrMsgs(field, msg, options):

    msgFldDefs = {'errors': 'truncateerror', 'messages': 'truncatemessage', 'warnings':'truncatewarning', 'logdata': 'truncatelogdata'}
    
    msgRet = msg
    msgLen = options[msgFldDefs[field]]

    if msgLen != 0:
        msgRet = msg[:msgLen] if len(msg) > msgLen else msg  
    
    return msgRet

def readDefaultOptions(section):
    return globs.optionManager.getRcSection(section)

# Class for report management
class Report:
    def __init__(self):
        globs.log.write(1,'Report:__init__()')

        # Initialize fomatted report list
        self.formattedReports = {'html': None, 'txt': None, 'csv': None, 'json': None}

        self.rStruct = {}
        self.validConfig = True     # Is the report config valid? Default to true for now. Alter if true later
        
        # Read in the default options
        self.rStruct['defaults'] = globs.optionManager.getRcSection('report')

        # Fix some of the data field types - integers
        for item in ('border', 'padding', 'nobackupwarn', 'truncatemessage', 'truncatewarning', 'truncateerror', 'truncatelogdata'):
            self.rStruct['defaults'][item] = int(self.rStruct['defaults'][item])

        # Fix some of the data field types - boolean
        #for item in ('showsizedisplay', 'displaymessages', 'displaywarnings', 'displayerrors', 'displaylogdata', 'repeatcolumntitles', 'durationzeroes', 'weminline'):
        for item in ('displaymessages', 'displaywarnings', 'displayerrors', 'displaylogdata', 'repeatcolumntitles', 'durationzeroes', 'weminline'):
            self.rStruct['defaults'][item] = self.rStruct['defaults'][item].lower() in ('true')   
            
        # Get reports that need to run as defined in [report]layout option
        layoutSections = splitRcIntoList(self.rStruct['defaults']['layout'])
        self.rStruct['sections'] = []

        # Now, loop through each report and get the specific configurations
        for section in layoutSections:
            rIndex = len(self.rStruct['sections'])   # This will be the index number of the next element we add
            self.rStruct['sections'].append({})
 
            # Get section name & type
            self.rStruct['sections'][rIndex]['name'] = section[0]
            self.rStruct['sections'][rIndex]['type'] = globs.optionManager.getRcOption(section[0], 'type')

            if self.rStruct['sections'][rIndex]['type'] == 'report':
                # Copy default options to report-specific options
                self.rStruct['sections'][rIndex]['options'] = self.rStruct['defaults'].copy()

                # Get report-specific options
                optionTmp = readDefaultOptions(section[0])
                for optTmp in optionTmp:
                    self.rStruct['sections'][rIndex]['options'][optTmp] = optionTmp[optTmp]

                # Fix some of the data field types - integers
                for item in ('border', 'padding', 'nobackupwarn', 'truncatemessage', 'truncatewarning', 'truncateerror', 'truncatelogdata'):
                    if type(self.rStruct['sections'][rIndex]['options'][item]) is not int:
                        self.rStruct['sections'][rIndex]['options'][item] = int(self.rStruct['sections'][rIndex]['options'][item])

                # Fix some of the data field types - boolean
                #for item in ('showsizedisplay', 'displaymessages', 'displaywarnings', 'displayerrors', 'displaylogdata', 'repeatcolumntitles', 'durationzeroes', 'weminline'):
                for item in ('displaymessages', 'displaywarnings', 'displayerrors', 'displaylogdata', 'repeatcolumntitles', 'durationzeroes', 'weminline'):
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
            elif self.rStruct['sections'][rIndex]['type'] == 'noactivity':
                # Get default options
                self.rStruct['sections'][rIndex]['options'] = self.rStruct['defaults'].copy()

                # Get report-specific options
                optionTmp = readDefaultOptions(section[0])
                for optTmp in optionTmp:
                    self.rStruct['sections'][rIndex]['options'][optTmp] = optionTmp[optTmp]

                # Fix some of the data field types - integers
                for item in ('border', 'padding', 'normaldays', 'warningdays'):
                    if type(self.rStruct['sections'][rIndex]['options'][item]) is not int:
                        self.rStruct['sections'][rIndex]['options'][item] = int(self.rStruct['sections'][rIndex]['options'][item])

            elif self.rStruct['sections'][rIndex]['type'] == 'lastseen':
                # Get default options
                self.rStruct['sections'][rIndex]['options'] = self.rStruct['defaults'].copy()

                # Get report-specific options
                optionTmp = readDefaultOptions(section[0])
                for optTmp in optionTmp:
                    self.rStruct['sections'][rIndex]['options'][optTmp] = optionTmp[optTmp]

                # Fix some of the data field types - integers
                for item in ('border', 'padding', 'normaldays', 'warningdays'):
                    if type(self.rStruct['sections'][rIndex]['options'][item]) is not int:
                        self.rStruct['sections'][rIndex]['options'][item] = int(self.rStruct['sections'][rIndex]['options'][item])

        # Basic field value checking
        self.validConfig = self.validateReportFields()

        return None

    # Determine if a column specified in the .rc file is a valid column name
    def validateColumns(self, section, colSpec):
        errRate = 0

        colList = colSpec
        # The first time around (checking the default colums) colList comes in as a string
        # By the time the individual report columns come in for checking, they have been converted to lists
        # Check if they're already lists to avoid program crashes
        if isinstance(colSpec, str):
            colList = splitRcIntoList(colSpec)

        for i in range(len(colList)):
            if colList[i][0] not in colNames:
                globs.log.err('ERROR: [{}] section: Column \'{}\' is an undefined field.\n'.format(section, colList[i][0]))
                globs.log.write(1, 'ERROR: [{}] section: Column \'{}\' is an undefined field.'.format(section, colList[i][0]))
                errRate += 1
            if len(colList[i]) != 2:
                globs.log.write(1, 'WARNING: [{}] section: Column \'{}\' does not have a title definition. Defaulting to column name as title.'.format(section, colList[i][0]))
            elif colList[i][1] =='':
                globs.log.write(1, 'WARNING: [{}] section: Title field for column \'{}\' is empty. This is not an error, but that column will not have a title when printed.'.format(section, colList[i][0]))

        return errRate

    def isValidReportField(self, fname):
        for i in range(len(options.rcParts)):
            if options.rcParts[i][0] != 'report':
                continue
            if options.rcParts[i][1] == fname:
                return True
        return False

    # Self-explanatory. See if the fields in the report-related sections of the .rc file are valid
    # Beginning with dupReport 3.0, the .report sections got much more complicated.
    # This function tries to find the most common problems at the strat of the program, rather than waiting until the end when thge reports are run
    def validateReportFields(self):
        globs.log.write(1,'Validating report specifications in .rc file.')
        anyProblems = 0
        
        # First, check the default [report]columns section for validity
        anyProblems = self.validateColumns('report', self.rStruct['defaults']['columns'])

        # Now, validate each report in the [report]layout= option
        sectionList = splitRcIntoList(self.rStruct['defaults']['layout'])
        for i in range(len(sectionList)):
            sect = globs.optionManager.getRcSection(sectionList[i][0])
            if sect == None: #Section does not exist
                globs.log.err('ERROR: [report] section specifies a report named \'{}\' but there is no corresponding \'[{}]\' section defined in the .rc file.\n'.format(sectionList[i][0], sectionList[i][0]))
                globs.log.write(1, 'ERROR: [report] section specifies a report named \'{}\' but there is no corresponding \'[{}]\' section defined in the .rc file.'.format(sectionList[i][0], sectionList[i][0]))
                anyProblems += 1
            elif 'type' not in sect:
                globs.log.err('ERROR: No \'type\' option in [{}] section. Valid types are \'report\', \'noactivity\', or \'lastseen\'\n'.format(sectionList[i][0]))
                globs.log.write(1,'ERROR: No \'type\' option in [{}] section. Valid types are \'report\', \'noactivity\', or \'lastseen\''.format(sectionList[i][0]))
                anyProblems += 1
            elif sect['type'] not in ['report', 'noactivity', 'lastseen']:
                globs.log.write(1,'ERROR: [{}] section: invalid section type: \'{}\'. Must be \'report\', \'noactivity\', or \'lastseen\''.format(sectionList[i][0], sect['type']))
                globs.log.err('ERROR: [{}] section: invalid section type: \'{}\'. Must be \'report\', \'noactivity\', or \'lastseen\'\n'.format(sectionList[i][0], sect['type']))
                anyProblems += 1
            else:
                if 'columns' in sect:
                    anyProblems += self.validateColumns(sectionList[i][0], sect['columns'])

                for optName in sect:    # Check that each option is valid
                    if optName in ['type', 'groupheading']:
                        continue
                    if optName in ['groupby', 'columnsort']:    # See if these two fields are specified correctly
                        oList = splitRcIntoList(sect[optName])
                        for i in range(len(oList)):
                            if oList[i][0] not in colNames:
                                globs.log.err('ERROR: [{}] section, \'{}\' option: invalid field name: \'{}\'. Must use a valid field name for this.\n'.format(sectionList[i][0], optName, oList[i][0]))
                                globs.log.write(1,'ERROR: [{}] section, \'{}\' option: invalid field name: \'{}\'. Must use a valid field name for this.'.format(sectionList[i][0], optName, oList[i][0]))
                                anyProblems += 1
                            if oList[i][1] not in ['ascending', 'descending']:
                                globs.log.err('ERROR: [{}] section, \'{}\' option, \'{}\' field: invalid sort order: \'{}\'. Must be \'ascending\' or \'descending\'.\n'.format(sectionList[i][0], optName, oList[i][0], oList[i][1]))
                                globs.log.write(1,'ERROR: [{}] section, \'{}\' option, \'{}\' field: invalid sort order: \'{}\'. Must be \'ascending\' or \'descending\'.'.format(sectionList[i][0], optName, oList[i][0], oList[i][1]))
                                anyProblems += 1
                    else:
                        if not self.isValidReportField(optName):
                            globs.log.write(1,'ERROR: [{}] section: invalid option: \'{}\'.'.format(sectionList[i][0], optName))
                            globs.log.err('ERROR: [{}] section: invalid option: \'{}\'.\n'.format(sectionList[i][0], optName))
                            anyProblems += 1

        globs.log.write(1, 'Found {} report validation errors.'.format(anyProblems))
        if globs.opts['validatereport'] == True:
            globs.log.out('Found {} report validation errors. See log file for details'.format(anyProblems))
        if anyProblems > 0:
            globs.log.err('Found {} report validation errors.\n'.format(anyProblems))
            return False
        else:
            return True

    # Extract the data needed for the report and move it to the report table in the database
    # This data will be picked up later by the specific report module
    def extractReportData(self):
        globs.log.write(1, 'extractReportData()')

        # Initialize report table. Delete all existing rows
        dbCursor = globs.db.execSqlStmt("DELETE FROM report")
        globs.db.dbCommit()


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

    def createReport(self, reportStructure):

        reportOutput = {}
        reportOutput['sections'] = []

        # Loop through report configurations
        for report in reportStructure['sections']:
            if report['type'] == 'report':
                reportOutput['sections'].append(self.buildReportOutput(report))
            elif report['type'] == 'noactivity':
                reportOutput['sections'].append(self.buildNoActivityOutput(report))
            elif report['type'] == 'lastseen':
                reportOutput['sections'].append(self.buildLastSeenOutput(report))
    
        return reportOutput

    # Manage the formattedReport dictionary in the class
    # Basically, if a report in a given format has already been generated, just return it. 
    # Otherwise, generate it, store it, and return it.
    def createFormattedOutput(self, reportOutput, type, startTime):
        # Has report already been created?
        if self.formattedReports[type] == None:
            # No. generate the report
            if type == 'html':
                self.formattedReports[type] = self.createHtmlFormat(globs.report.rStruct, reportOutput, startTime)
            elif type == 'txt':
                self.formattedReports[type] = self.createTextFormat(globs.report.rStruct, reportOutput, startTime) 
            elif type == 'csv':
                self.formattedReports[type] = self.createCsvFormat(globs.report.rStruct, reportOutput, startTime) 
            elif type == 'json':
                self.formattedReports[type] = self.createJsonFormat(globs.report.rStruct, reportOutput, startTime) 

        # Return what you got
        return self.formattedReports[type]
        pass

    # Take data from report table and build the resulting report structure.
    # Output structure will be used to generate the final report
    # 'reportStructure' is the report options as extracted from the .rc file
    # See docs/DataStructures/ConfigFormat for schema of reportStructure
    # See docs/DataStructures/ReportFormat for schema of reportOutput
    def buildReportOutput(self, report):

        # singleReport is the output for just this specific report. 
        # It will be appended to reportOutput once it is filled in.
        # This is how we produce multiple reports from the same run.
        singleReport = {}

        # Copy basic report information from the report definition
        singleReport['name'] = report['name']
        singleReport['columnCount'] = len(report['options']['columns'])
        singleReport['columnNames'] = []
        for i in range(len(report['options']['columns'])):
            markup = toMarkup(bold=True, align=fldDefs[report['options']['columns'][i][0]][0])
            singleReport['columnNames'].append([report['options']['columns'][i][0], report['options']['columns'][i][1], '#FFFFFF', markup]) # Column names are white and bold
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
                #singleReport['groups'][groupIndex]['groupHeading'] = grpHeading

            # Perform keyword substutution on the group heading
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

            singleReport['groups'][groupIndex]['groupHeading'] = [grpHeading,  report['options']['groupheadingbg'], toMarkup(bold=True)]
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
                        markup = toMarkup(align=fldDefs['date'][0])
                        dateStr, timeStr = drdatetime.fromTimestamp(rowList[rl][i], dfmt=globs.opts['dateformat'], tfmt=globs.opts['timeformat'])
                        singleReport['groups'][groupIndex]['dataRows'][dataRowIndex].append([dateStr, '#FFFFFF', markup])
                    elif report['options']['columns'][i][0] == 'time':
                        markup = toMarkup(align=fldDefs['time'][0])
                        dateStr, timeStr = drdatetime.fromTimestamp(rowList[rl][i], dfmt=globs.opts['dateformat'], tfmt=globs.opts['timeformat'])
                        singleReport['groups'][groupIndex]['dataRows'][dataRowIndex].append([timeStr, '#FFFFFF', markup])
                    elif report['options']['columns'][i][0] == 'duration':
                        markup = toMarkup(align=fldDefs['duration'][0])
                        tDiff = drdatetime.timeDiff(rowList[rl][i], report['options']['durationzeroes'])
                        singleReport['groups'][groupIndex]['dataRows'][dataRowIndex].append([tDiff, '#FFFFFF', markup])
                    elif ((report['options']['columns'][i][0] in ['messages', 'warnings', 'errors', 'logdata']) and (report['options']['weminline'] is False)):
                        if rowList[rl][i] != '':
                            type = report['options']['columns'][i][0]
                            if type == 'messages':
                                if report['options']['displaymessages'] == False:
                                    continue
                                bground = report['options']['jobmessagebg']
                            elif type == 'warnings':
                                if report['options']['displaywarnings'] == False:
                                    continue
                                bground = report['options']['jobwarningbg']
                            elif type == 'errors':
                                if report['options']['displayerrors'] == False:
                                    continue
                                bground = report['options']['joberrorbg']
                            elif type == 'logdata':
                                if report['options']['displaylogdata'] == False:
                                    continue
                                bground = report['options']['joblogdatabg']
                            truncatedMsg = truncateWarnErrMsgs(type, rowList[rl][i], report['options'])
                            markup = toMarkup(align=fldDefs[type][0])
                            msgList[report['options']['columns'][i][0]] = [truncatedMsg, bground, markup, report['options']['columns'][i][1]]
                    elif report['options']['columns'][i][0] in ['examinedFiles', 'examinedFilesDelta', 'sizeOfExaminedFiles', 'fileSizeDelta', 'addedFiles', 'deletedFiles', 'modifiedFiles', 'filesWithError']:  # Right-aligned fields
                        markup = toMarkup(align='right')
                        singleReport['groups'][groupIndex]['dataRows'][dataRowIndex].append([rowList[rl][i], '#FFFFFF', markup])
                    else:
                        markup = toMarkup(align='left')
                        singleReport['groups'][groupIndex]['dataRows'][dataRowIndex].append([rowList[rl][i], '#FFFFFF', markup])

                # If there are warnings, errors, messages to output and we don't want them inline, print separate lines after the main columns
                if len(msgList) != 0 and report['options']['weminline'] is False:       
                    for msg in msgList:
                        singleReport['groups'][groupIndex]['dataRows'].append([msgList[msg]])
                        dataRowIndex += 1

        if len(singleReport['groups']) == 0:    # No activity
            singleReport['groups'].append({})
            singleReport['groups'][0]['groupHeading'] = ['No Email Activity Today', '#FFFFFF', toMarkup(bold=True, italic=True)] 
            singleReport['groups'][0]['dataRows'] = []
            singleReport['groups'][0]['dataRows'].append([])
            singleReport['groups'][0]['dataRows'][0].append(['No Email Activity', '#FFFFFF', toMarkup(italic=True), 'No Email Activity'])

        return singleReport

    def buildNoActivityOutput(self, report):
        singleReport = {}

        # Copy basic report information from the report definition
        singleReport['name'] = report['name']
        singleReport['title'] = report['options']['title']
        singleReport['columnCount'] = 3
        singleReport['columnNames'] = []

        markup = toMarkup(bold=True)
        singleReport['columnNames'].append(['source', 'Source', '#FFFFFF', markup])
        singleReport['columnNames'].append(['destination', 'Destination', '#FFFFFF', markup])
        singleReport['columnNames'].append(['lastseen', 'Last Seen', '#FFFFFF', markup])
        singleReport['inlineColumnCount'] = 3
        singleReport['inlineColumnNames'] = singleReport['columnNames']

        singleReport['groups'] = []
        singleReport['groups'].append({})
        singleReport['groups'][0]['dataRows'] = []

        # Select all source/destination pairs (& last seen timestamp) from the backupset list 
        sqlStmt = "SELECT DISTINCT source, destination, lasttimestamp FROM backupsets"
        dbCursor = globs.db.execSqlStmt(sqlStmt)
        sourceDestList = dbCursor.fetchall()

        dataRowIndex = -1
        for source, destination, lastTimestamp in sourceDestList:
            sqlStmt = "SELECT count(*) FROM report WHERE source='{}' and destination='{}'".format(source, destination)
            dbCursor = globs.db.execSqlStmt(sqlStmt)
            countRows = dbCursor.fetchone()

            if countRows[0] == 0:
                # If src/dest is known offline, skip
                srcDest = '{}{}{}'.format(source, globs.opts['srcdestdelimiter'], destination)
                offline = globs.optionManager.getRcOption(srcDest, 'offline')
                if offline != None:  
                    if offline.lower() in ('true'):
                        continue

                # Calculate days since last activity & set background accordingly
                diff = drdatetime.daysSince(lastTimestamp)
                pastInterval, interval = pastBackupInterval(srcDest, diff)

                if interval == 0:   # Normal backup times apply
                    bgColor = report['options']['normalbg']
                    if diff > report['options']['normaldays']:
                        bgColor = report['options']['warningbg']
                    if diff > report['options']['warningdays']:
                        bgColor = report['options']['errorbg']
                else:   # Backup interval in play
                    bgColor = report['options']['normalbg']
                    if diff > interval:
                        bgColor = report['options']['warningbg']
                    if diff > (interval + int(report['options']['warningdays'])):
                        bgColor = report['options']['errorbg']

                singleReport['groups'][0]['dataRows'].append([])
                dataRowIndex += 1
                markupPlain = toMarkup()
                markupItal = toMarkup(italic=True)
                # See if we're past the backup interval before reporting
                singleReport['groups'][0]['dataRows'][dataRowIndex].append([source, '#FFFFFF', markupPlain])
                singleReport['groups'][0]['dataRows'][dataRowIndex].append([destination,'#FFFFFF', markupPlain])
                if pastInterval is False:
                    globs.log.write(3, 'SrcDest=[{}] DaysDiff=[{}]. Skip reporting'.format(srcDest, diff))
                    singleReport['groups'][0]['dataRows'][dataRowIndex].append(['{} days ago. Backup interval is {} days.'.format(diff, interval), bgColor, markupPlain])
                else:
                    lastDateStr, lastTimeStr = drdatetime.fromTimestamp(lastTimestamp)
                    singleReport['groups'][0]['dataRows'][dataRowIndex].append(['Last activity on {} at {} ({} days ago)'.format(lastDateStr, lastTimeStr, diff), bgColor, markupItal])

    
        if dataRowIndex == -1:  # No rows in unseen table
            singleReport['groups'][0]['dataRows'].append([])
            markup = toMarkup(italic=True, align='center')
            singleReport['groups'][0]['dataRows'][0].append(['None', '#FFFFFF', markup, '', '', 3])

        return singleReport

    def buildLastSeenOutput(self, report):

        singleReport = {}

        # Copy basic report information from the report definition
        singleReport['name'] = report['name']
        singleReport['title'] = report['options']['title']
        singleReport['columnCount'] = 3
        singleReport['columnNames'] = []

        markup = toMarkup(bold=True)
        singleReport['columnNames'].append(['source', 'Source', '#FFFFFF', markup])
        singleReport['columnNames'].append(['destination', 'Destination', '#FFFFFF', markup])
        singleReport['columnNames'].append(['lastseen', 'Last Seen', '#FFFFFF', markup])
        singleReport['inlineColumnCount'] = 3
        singleReport['inlineColumnNames'] = singleReport['columnNames']

        singleReport['groups'] = []
        singleReport['groups'].append({})
        singleReport['groups'][0]['dataRows'] = []

        # Select all source/destination pairs (& last seen timestamp) from the backupset list 
        sqlStmt = "SELECT source, destination, lastTimestamp FROM backupsets ORDER BY source, destination"
        dbCursor = globs.db.execSqlStmt(sqlStmt)
        sourceDestList = dbCursor.fetchall()
        globs.log.write(3,'sourceDestList=[{}]'.format(sourceDestList))

        dataRowIndex = -1
        for source, destination, lastTimestamp in sourceDestList:
            # If src/dest is known offline, skip
            srcDest = '{}{}{}'.format(source, globs.opts['srcdestdelimiter'], destination)
            offline = globs.optionManager.getRcOption(srcDest, 'offline')
            if offline != None:  
                if offline.lower() in ('true'):
                    continue

            lastDate = drdatetime.fromTimestamp(lastTimestamp)
            diff = drdatetime.daysSince(lastTimestamp)

            # Calculate days since last activity & set background accordingly
            pastInterval, interval = pastBackupInterval(srcDest, diff)

            if interval == 0:   # Normal backup times apply
                bgColor = report['options']['normalbg']
                if diff > report['options']['normaldays']:
                    bgColor = report['options']['warningbg']
                if diff > report['options']['warningdays']:
                    bgColor = report['options']['errorbg']
            else:   # Backup interval in play
                bgColor = report['options']['normalbg']
                if diff > interval:
                    bgColor = report['options']['warningbg']
                if diff > (interval + int(report['options']['warningdays'])):
                    bgColor = report['options']['errorbg']

            singleReport['groups'][0]['dataRows'].append([])
            dataRowIndex += 1
            markupPlain = toMarkup()
            markupItal = toMarkup(italic=True)
            # See if we're past the backup interval before reporting
            singleReport['groups'][0]['dataRows'][dataRowIndex].append([source, '#FFFFFF', markupPlain])
            singleReport['groups'][0]['dataRows'][dataRowIndex].append([destination,'#FFFFFF', markupPlain])
            if pastInterval is False:
                globs.log.write(3, 'SrcDest=[{}] DaysDiff=[{}]. Skip reporting'.format(srcDest, diff))
                singleReport['groups'][0]['dataRows'][dataRowIndex].append(['{} days ago. Backup interval is {} days.'.format(diff, interval), bgColor, markupPlain])
            else:
                lastDateStr, lastTimeStr = drdatetime.fromTimestamp(lastTimestamp)
                singleReport['groups'][0]['dataRows'][dataRowIndex].append(['Last activity on {} at {} ({} days ago)'.format(lastDateStr, lastTimeStr, diff), bgColor, markupItal])

        return singleReport

    def createHtmlFormat(self, reportStructure, reportOutput, startTime):
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

            if reportStructure['sections'][rptIndex]['type'] == 'report':
                if rptOptions['repeatcolumntitles'] is False:    # Only print headers at the top of the report
                    # Print column headings
                    msgHtml += '<tr>'
                    for i in range(len(report['inlineColumnNames'])):
                        msgHtml += printTitle(report['inlineColumnNames'][i], rptOptions, 'html')
                    msgHtml += '</tr>\n'

                # Loop through each group in the report
                grpIndex = -1
                for group in reportOutput['sections'][rptIndex]['groups']:
                    grpIndex += 1
            
                    # Print group heading
                    msgHtml += '<tr><td align="center" colspan="{}" bgcolor="{}"><b>{}</b></td></tr>\n'.format(report['inlineColumnCount'], rptOptions['groupheadingbg'], report['groups'][grpIndex]['groupHeading'][0])

                    if rptOptions['repeatcolumntitles'] is True:    # Only print headers at the top of the report
                        # Print column headings
                        msgHtml += '<tr>'
                        for i in range(len(report['inlineColumnNames'])):
                            msgHtml += printTitle(report['inlineColumnNames'][i], rptOptions, 'html')
                        msgHtml += '</tr>\n'

                    # Print data rows & columns for that group
                    for row in report['groups'][grpIndex]['dataRows']:
                        msgHtml += '<tr>'
                        if len(row) != 1:  # Standard, multicolumn report 
                            for column in range(len(row)):
                                msgHtml += printField(row[column], report['inlineColumnNames'][column][0], reportStructure['sections'][rptIndex]['options']['sizedisplay'], 'html')
                        else:   # Single column - error, warning, message
                            msgHtml += printField(row[0], '', '', 'html', row[0][3], report['inlineColumnCount'], summary=True)
                        msgHtml += '</tr>\n'
            elif reportStructure['sections'][rptIndex]['type'] in ['noactivity', 'lastseen']:
                # Loop through each group in the report
                grpIndex = -1
                for group in reportOutput['sections'][rptIndex]['groups']:
                    grpIndex += 1
            
                    # Print column headings
                    for i in range(len(report['inlineColumnNames'])):
                        msgHtml += printTitle(report['inlineColumnNames'][i], rptOptions, 'html')
                    msgHtml += '</tr>\n'

                    # Print data rows
                    msgHtml += '<tr>'
                    for row in group['dataRows']:
                        msgHtml += '<tr>'
                        if len(row) != 1:  # Standard, multicolumn report 
                            # Print data rows & columns for that group
                            for column in range(len(row)):
                                msgHtml += printField(row[column], report['inlineColumnNames'][column][0], '', 'html')
                        else:   # Single column
                            msgHtml += printField(row[0], '', '', 'html', row[0][3], report['inlineColumnCount'])
                        msgHtml += '</tr>\n'

            msgHtml += '</table><br>'

        msgHtml += '<br>{}'.format(getRunningTime(startTime))
        msgHtml += '<br>Report generated by <a href=\'https://github.com/HandyGuySoftware/dupReport\'>dupReport</a> Version {}.{}.{} ({})<br>'.format(globs.version[0], globs.version[1], globs.version[2], globs.status)
        msgHtml += '</body></html>\n'

        return msgHtml

    def createTextFormat(self, reportStructure, reportOutput, startTime):
        msgText = ''

        rptIndex = -1
        for report in reportOutput['sections']:
            rptIndex += 1
            rptName = report['name']
            rptOptions = reportStructure['sections'][rptIndex]['options']

            # Add title               
            msgText += rptOptions['title'] + '\n'

            if reportStructure['sections'][rptIndex]['type'] == 'report':
                if rptOptions['repeatcolumntitles'] is False:    # Only print headers at the top of the report
                    # Print column headings
                    for i in range(len(report['inlineColumnNames'])):
                        msgText += printTitle(report['inlineColumnNames'][i], rptOptions, 'txt')
                    msgText += '\n'

                # Loop through each group in the report
                grpIndex = -1
                for group in reportOutput['sections'][rptIndex]['groups']:
                    grpIndex += 1
            
                    # Print group heading
                    msgText += '{}\n'.format(report['groups'][grpIndex]['groupHeading'][0])

                    if rptOptions['repeatcolumntitles'] is True:    # Only print headers at the top of the report
                        # Print column headings
                        for i in range(len(report['inlineColumnNames'])):
                            msgText += printTitle(report['inlineColumnNames'][i], rptOptions, 'txt')
                        msgText += '\n'

                    # Print data rows & columns for that group
                    for row in report['groups'][grpIndex]['dataRows']:
                        if len(row) != 1:  # Standard, multicolumn report 
                            for column in range(len(row)):
                                msgText += printField(row[column], report['inlineColumnNames'][column][0], reportStructure['sections'][rptIndex]['options']['sizedisplay'], 'txt')
                        else:   # Single column - error, warning, message
                            msgText += printField(row[0], report['inlineColumnNames'][0][0], '', 'txt', row[0][3], report['inlineColumnCount'], summary=True)
                        msgText += '\n'
            elif reportStructure['sections'][rptIndex]['type'] in ['noactivity', 'lastseen']:
                # Loop through each group in the report
                grpIndex = -1
                for group in reportOutput['sections'][rptIndex]['groups']:
                    grpIndex += 1
            
                    # Print column headings
                    for i in range(len(report['inlineColumnNames'])):
                        msgText += printTitle(report['inlineColumnNames'][i], rptOptions, 'txt')
                    msgText += '\n'

                    # Print data rows
                    for row in group['dataRows']:
                        if len(row) != 1:  # Standard, multicolumn report 
                            # Print data rows & columns for that group
                            for column in range(len(row)):
                                msgText += printField(row[column], report['inlineColumnNames'][column][0], '', 'txt')
                        else:   # Single column
                            msgText += printField(row[0], '', '', 'txt', row[0][3], report['inlineColumnCount'])
                        msgText += '\n'

            msgText += '\n'

        msgText += '\n{}\n'.format(getRunningTime(startTime))
        msgText += 'Report generated by dupReport (https://github.com/HandyGuySoftware/dupReport) Version {}.{}.{} ({})\n'.format(globs.version[0], globs.version[1], globs.version[2], globs.status)
        msgText += '\n'

        return msgText

    def createCsvFormat(self, reportStructure, reportOutput, startTime):
        msgCsv = ''

        rptIndex = -1
        for report in reportOutput['sections']:
            rptIndex += 1
            rptName = report['name']
            rptOptions = reportStructure['sections'][rptIndex]['options']

            # Add title               
            msgCsv += rptOptions['title'] + '\n'

            if reportStructure['sections'][rptIndex]['type'] == 'report':
                if rptOptions['repeatcolumntitles'] is False:    # Only print headers at the top of the report
                    # Print column headings
                    for i in range(len(report['inlineColumnNames'])):
                        msgCsv += printTitle(report['inlineColumnNames'][i], rptOptions, 'csv')
                    msgCsv += '\n'

                # Loop through each group in the report
                grpIndex = -1
                for group in reportOutput['sections'][rptIndex]['groups']:
                    grpIndex += 1
            
                    # Print group heading
                    msgCsv += '\"{}\"\n'.format(report['groups'][grpIndex]['groupHeading'][0])

                    if rptOptions['repeatcolumntitles'] is True:    # Only print headers at the top of the report
                        # Print column headings
                        for i in range(len(report['inlineColumnNames'])):
                            msgCsv += printTitle(report['inlineColumnNames'][i], rptOptions, 'csv')
                        msgCsv += '\n'

                    # Print data rows & columns for that group
                    for row in report['groups'][grpIndex]['dataRows']:
                        if len(row) != 1:  # Standard, multicolumn report 
                            for column in range(len(row)):
                                msgCsv += printField(row[column], report['inlineColumnNames'][column][0], reportStructure['sections'][rptIndex]['options']['sizedisplay'], 'csv')
                        else:   # Single column - error, warning, message
                            msgCsv += printField(row[0], report['inlineColumnNames'][0][0], '', 'csv', row[0][3], report['inlineColumnCount'], summary=True)
                        msgCsv += '\n'
            elif reportStructure['sections'][rptIndex]['type'] in ['noactivity', 'lastseen']:
                # Loop through each group in the report
                grpIndex = -1
                for group in reportOutput['sections'][rptIndex]['groups']:
                    grpIndex += 1
            
                    # Print column headings
                    for i in range(len(report['inlineColumnNames'])):
                        msgCsv += printTitle(report['inlineColumnNames'][i], rptOptions, 'csv')
                    msgCsv += '\n'

                    # Print data rows
                    for row in group['dataRows']:
                        if len(row) != 1:  # Standard, multicolumn report 
                            # Print data rows & columns for that group
                            for column in range(len(row)):
                                msgCsv += printField(row[column], report['inlineColumnNames'][column][0], '', 'csv')
                        else:   # Single column
                            msgCsv += printField(row[0], '', '', 'csv', row[0][3], report['inlineColumnCount'])
                        msgCsv += '\n'

            msgCsv += '\n'

        msgCsv += '\"{}\"\n'.format(getRunningTime(startTime))
        msgCsv += '\"Report generated by dupReport (https://github.com/HandyGuySoftware/dupReport) Version {}.{}.{} ({})\"\n'.format(globs.version[0], globs.version[1], globs.version[2], globs.status)

        return msgCsv

    def createJsonFormat(self, reportStructure, reportOutput, startTime):
        return reportOutput

