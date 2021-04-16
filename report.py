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
    'srcdest':              ('left',        '20',       '20'),
    'dupversion':           ('left',        '35',       '35'),
    'date':                 ('left',        '13',       '13'),
    'time':                 ('left',        '11',       '11'),
    'duration':             ('right',       '>15',      '>15'),
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
    'messages':             ('left',        '50',       '50'),
    'warnings':             ('left',        '50',       '50'),
    'errors':               ('left',        '50',       '50'),
    'logdata':              ('left',        '50',       '50'),
    'bytesUploaded':        ('right',       '>21',      '>21,.3f'),
    'bytesDownloaded':      ('right',       '>21',      '>21,.3f')
    }

dataRowTypes = {
        'rptTitle':     0x01,
        'grpHeading':   0x02,
        'rowHead':      0x04,
        'data':         0x08,
        'wemData':      0x10,
        'singleLine':   0x20
        }

# List of all the valid column names that can be used in reports
colNames = ['source','destination','date','time','examinedFiles','examinedFilesDelta','sizeOfExaminedFiles','fileSizeDelta','addedFiles','deletedFiles','modifiedFiles','filesWithError','parsedResult','messages','warnings','errors','duration','logdata','dupversion', 'bytesUploaded', 'bytesDownloaded']

# Group field types
wemFields = ['messages', 'warnings', 'errors', 'logdata']
intFields = ['border', 'padding', 'normaldays', 'warningdays', 'nobackupwarn', 'truncatemessage', 'truncatewarning', 'truncateerror', 'truncatelogdata']
boolFields = ['displaymessages', 'displaywarnings', 'displayerrors', 'displaylogdata', 'repeatcolumntitles', 'suppresscolumntitles', 'durationzeroes', 'weminline', 'includeruntime', 'failedonly', 'showoffline']
sizeFields = ['sizeOfExaminedFiles', 'fileSizeDelta', 'bytesUploaded', 'bytesDownloaded']
timestampFields = ['date', 'time', 'duration']
numberFields = ['examinedFiles', 'examinedFilesDelta', 'sizeOfExaminedFiles', 'fileSizeDelta', 'addedFiles', 'deletedFiles', 'modifiedFiles', 'filesWithError', 'bytesUploaded', 'bytesDownloaded']

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

    if options['failedonly']:
        if whereOpts:
            sqlStmt += ' AND parsedResult != \'Success\' '
        else:
            sqlStmt += ' WHERE parsedResult != \'Success\' '

    if groupby:
        sqlStmt += ' ORDER BY ' + buildOrderList(options['groupby']) 
    elif 'columnsort' in options:
        sqlStmt += ' ORDER BY ' + buildOrderList(options['columnsort']) 

    globs.log.write(globs.SEV_DEBUG, function='Report', action='buildQuery', msg='Created SQL stmt: {}'.format(sqlStmt))
    return sqlStmt

# Build a list of fields to select based on 'list' 
def buildSelectList(list):
    selectString=''
    for i in range(len(list)):
        selectString += list[i][0] + ' '

        # More fields to add?
        if  i != (len(list)-1):
            selectString += ', '

    globs.log.write(globs.SEV_DEBUG, function='Report', action='buildSelectList', msg='Created SQL SELECT stmt: {}'.format(selectString))
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

    globs.log.write(globs.SEV_DEBUG, function='Report', action='buildWhereClause', msg='Created SQL WHERE stmt: {}'.format(whereString))
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

    globs.log.write(globs.SEV_DEBUG, function='Report', action='buildOrderList', msg='Created SQL ORDER BY stmt: {}'.format(sortString))
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

    globs.log.write(globs.SEV_DEBUG, function='Report', action='splitRcIntoList', msg='.rc entry \'{}\' split into list: {}'.format(inputString, iniList))
    return iniList

markupDefs = {
    'bold':         0x01,
    'italic':       0x02,
    'underline':    0x04,
    'left':         0x08,
    'center':       0x10,
    'right':        0x20
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
# Returns start_tag, end_tag, alignment
def fromMarkup(markup):
    fmtStart = ''
    fmtEnd = ''

    if bool(markup & markupDefs['bold']):
        fmtStart += '<b>'
        fmtEnd += '</b>'
    if bool(markup & markupDefs['italic']):
        fmtStart += '<i>'
        fmtEnd += '</i>'
    if bool(markup & markupDefs['underline']):
        fmtStart += '<u>'
        fmtEnd += '</u>'

    if markup & markupDefs['left']:
        align = 'left'
    elif markup & markupDefs['right']:
        align = 'right'
    else:
        align = 'center'

    return fmtStart, fmtEnd, align

# If errors, messages, etc are put on separate lines (weminline = False), they shouldn't be included in the column layout or count
# Adjust the column layout  & count (inlineColumns, inlineColumnCount to account for this
def adjustColumnCountInfo(count, colNames, wemInLine):
    newColCount = count
    newColNames = colNames.copy()
    
    if wemInLine == False:
        for i in reversed(range(len(colNames))):
            if newColNames[i][0] in wemFields:
                newColNames.pop(i)
                newColCount -= 1
    
    globs.log.write(globs.SEV_DEBUG, function='Report', action='adjustColumnCountInfo', msg='WEMInline={}. Column count adusted from {} columns to {} columns'.format(wemInLine, count, newColCount))
    return newColCount, newColNames

def sendReportToFiles(reportOutput):
    globs.log.write(globs.SEV_NOTICE, function='Report', action='sendReportToFiles', msg='Sending report to output files.')
    # Loop through filespec list provided on command line
    # Split into file names and formats
    for fspec in globs.ofileList:
        fsplit = fspec[0].split(',')
        fileName = fsplit[0]
        format = fsplit[1]
        globs.log.write(globs.SEV_DEBUG, function='Report', action='sendReportToFiles', msg='Output file:{}  Format:{}'.format(fileName, format))

        msgContent = globs.report.createFormattedOutput(reportOutput, format) 
        if fileName == 'stdout':
            sys.stdout.write(msgContent)
        elif fileName == 'stderr':
            sys.stderr.write(msgContent)
        else:
            try:
                outfile = open(fileName,'w')
            except (OSError, IOError):
                e = sys.exc_info()[0]
                globs.log.write(globs.SEV_ERROR, function='Report', action='sendReportToFiles', msg='Error: problem opening output file {}: {}'.format(fileName, e))
                return
            if format in ['html', 'txt', 'csv']:
                outfile.write(msgContent)
            else:
                json.dump(msgContent, outfile)
            outfile.close()
    return None

# Look for nobackup warning threshold
# Default to value in [eport] section
# Override if found in pair-specific section
def pastBackupWarningThreshold(src, dest, nDays, nbWarnDefault):
    srcDest = src + globs.opts['srcdestdelimiter'] + dest
    globs.log.write(globs.SEV_NOTICE, function='Report', action='pastBackupWarningThreshold', msg='{} last reported {} days ago'.format(srcDest, nDays))

    nbwVal = globs.optionManager.getRcOption(srcDest, 'nobackupwarn')
    if nbwVal is not None:
        nbwVal = int(nbwVal)    # getRcOption returns a string, we need an int
    else:
        nbwVal = nbWarnDefault

    globs.log.write(globs.SEV_DEBUG, function='Report', action='pastBackupWarningThreshold', msg='Nobackup warning threshold is {} days.'.format(nbwVal))

    retVal = False
    if (nbwVal != 0) and (nDays >= nbwVal):     # Past threshold - need to warn
        retVal = True

    globs.log.write(globs.SEV_NOTICE, function='Report', action='pastBackupWarningThreshold', msg='Need to warn? {}'.format(retVal))
    return retVal

def sendNoBackupWarnings():
    # Get all source/destination pairs
    sqlStmt = "SELECT source, destination FROM backupsets ORDER BY source, destination"
    dbCursor = globs.db.execSqlStmt(sqlStmt)
    srcDestRows = dbCursor.fetchall()
    if len(srcDestRows) != 0:
        for source, destination in srcDestRows:
			# First, see if SrcDest is listed as offline. If so, skip.
            srcDest = source + globs.opts['srcdestdelimiter'] + destination
            offline = globs.optionManager.getRcOption(srcDest, 'offline')
            if offline != None:
                if offline.lower() in ('true'):
                    globs.log.write(globs.SEV_DEBUG, function='Report', action='sendNoBackupWarnings', msg='{} is offline.'.format(srcDest))
                    continue

            latestTimeStamp = getLatestTimestamp(source, destination)
            diff = drdatetime.daysSince(latestTimeStamp)
            if pastBackupWarningThreshold(source, destination, diff, globs.report.rStruct['defaults']['nobackupwarn']) is True:
                globs.log.write(globs.SEV_NOTICE, function='Report', action='sendNoBackupWarnings', msg='{} is past backup warning threshold @ {} days. Sending warning email.'.format(srcDest, diff))
                warnHtml, warnText, subj, send, receive = report.buildWarningMessage(source, destination, diff, latestTimeStamp, globs.report.rStruct['defaults'])
                globs.emailManager.sendEmail(msgHtml = warnHtml, msgText = warnText, subject = subj, sender = send, receiver = receive)
    return None

def buildWarningMessage(source, destination, nDays, lastTimestamp, opts):
    lastDateStr, lastTimeStr = drdatetime.fromTimestamp(lastTimestamp)
    srcDest = source + globs.opts['srcdestdelimiter'] + destination
    globs.log.write(globs.SEV_NOTICE, function='Report', action='buildWarningMessage', msg='Building warning message for {}.'.format(srcDest))
    globs.log.write(globs.SEV_DEBUG, function='Report', action='buildWarningMessage', msg='{} last reported in {} at {}.'.format(srcDest, lastDateStr, lastTimeStr))

    subj = globs.optionManager.getRcOption(srcDest, 'nbwsubject')
    if subj is None:
        subj = opts['nbwsubject']
    subj = subj.replace('#SOURCE#',source).replace('#DESTINATION#', destination).replace('#DELIMITER#', globs.opts['srcdestdelimiter']).replace('#DAYS#', str(nDays)).replace('#DATE#', lastDateStr).replace('#TIME#', lastTimeStr)
    globs.log.write(globs.SEV_DEBUG, function='Report', action='buildWarningMessage', msg='Warning message subject: \'{}\''.format(subj))

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
    
    sender = globs.emailManager.getSmtpServer().options['sender']
    receiver = globs.optionManager.getRcOption(srcDest, 'receiver')
    if receiver is None:
        receiver = globs.emailManager.getSmtpServer().options['receiver']

    globs.log.write(globs.SEV_NOTICE, function='Report', action='buildWarningMessage', msg='Sending message to {}'.format(receiver))
    return warnHtml, warnText, subj, sender, receiver

def getLatestTimestamp(src, dest):
    globs.log.write(globs.SEV_NOTICE, function='Report', action='getLatestTimestamp', msg='Getting latest time stamp for {}{}{})'.format(src, globs.opts['srcdestdelimiter'], dest))

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
                globs.log.write(globs.SEV_DEBUG, function='Report', action='getLatestTimestamp', msg='Found an email. Returning latest timestamp from email: {}'.format(lastEmailStamp[0]))
                return lastEmailStamp[0]
            else:
                # Nothing newer in database - return latest time from backupsets
                globs.log.write(globs.SEV_DEBUG, function='Report', action='getLatestTimestamp', msg='No emails found. Returning latest timestamp from backupsets: {}'.format(lastTimestamp[0]))
                return lastTimestamp[0]
    else:
        # This should never happen
        globs.log.write(globs.SEV_NOTICE, function='Report', action='getLatestTimestamp', msg='Didn\'t find any timestamp for {}{}{}: something is wrong!'.format(src, globs.opts['srcdestdelimiter'], dest))
        return None

def pastBackupInterval(srcDest, days):
    # Get backup interval from rc file. Default is 0
    backupInterval = globs.optionManager.getRcOption(srcDest, 'backupinterval')
    if backupInterval is None:
        backupInterval = 0
    else:
        backupInterval = int(backupInterval)    # Change value to an int type

    # If we're not past the backup interval, skip reporting this src/dest as missing
    retval = False                      # Not yet past the backup interval
    if days >= backupInterval:
        retval = True                     # At or past the backup interval

    globs.log.write(globs.SEV_NOTICE, function='Report', action='pastBackupInterval', msg='Is {} past its backup interval of {} days? {}'.format(srcDest, backupInterval, retval))
    return retval, backupInterval

# Truncate warning & error messages
def truncateWarnErrMsgs(field, msg, options):
    msgFldDefs = {'errors': 'truncateerror', 'messages': 'truncatemessage', 'warnings':'truncatewarning', 'logdata': 'truncatelogdata'}
    
    msgRet = msg
    msgLen = options[msgFldDefs[field]]

    if msgLen != 0:
        globs.log.write(globs.SEV_NOTICE, function='Report', action='truncateWarnErrMsgs', msg='Truncating {} message to {} characters.'.format(field, msgLen))
        msgRet = msg[:msgLen] if len(msg) > msgLen else msg  
    
    return msgRet

# Class for report management
class Report:
    def __init__(self):
        globs.log.write(globs.SEV_NOTICE, function='Report', action='Init', msg='Initializing report object.')

        # Initialize fomatted report list
        self.formattedReports = {'html': None, 'txt': None, 'csv': None, 'json': None}

        self.rStruct = {}
        self.validConfig = True     # Is the report config valid? Default to true for now. Alter if false later
        
        # Read in the default options
        self.rStruct['defaults'] = globs.optionManager.getRcSection('report')

        # Fix some of the data field types - integers
        for item in intFields:
            self.rStruct['defaults'][item] = int(self.rStruct['defaults'][item])

        # Fix some of the data field types - boolean
        for item in boolFields:
            self.rStruct['defaults'][item] = self.rStruct['defaults'][item].lower() in ('true')   
            
        # Get reports that need to run as defined in [report]layout option
        if globs.opts['layout'] != None:
            self.rStruct['defaults']['layout'] = globs.opts['layout']
        layoutSections = splitRcIntoList(self.rStruct['defaults']['layout'])
        self.rStruct['sections'] = []

        validReportSpec = self.validateReportFields()
        if not validReportSpec:
            globs.closeEverythingAndExit(1)

        # Now, loop through each report and get the specific configurations
        for section in layoutSections:
            globs.log.write(globs.SEV_NOTICE, function='Report', action='Init', msg='Getting configuration for {} report.'.format(section))

            rIndex = len(self.rStruct['sections'])   # This will be the index number of the next element we add
            self.rStruct['sections'].append({})
 
            # Get section name & type
            self.rStruct['sections'][rIndex]['name'] = section[0]
            self.rStruct['sections'][rIndex]['type'] = globs.optionManager.getRcOption(section[0], 'type')

            if self.rStruct['sections'][rIndex]['type'] == 'report':
                # Copy default options to report-specific options
                self.rStruct['sections'][rIndex]['options'] = self.rStruct['defaults'].copy()

                # Get report-specific options
                optionTmp = globs.optionManager.getRcSection(section[0])
                for optTmp in optionTmp:
                    self.rStruct['sections'][rIndex]['options'][optTmp] = optionTmp[optTmp]

                # Fix some of the data field types - integers
                for item in intFields:
                    if type(self.rStruct['sections'][rIndex]['options'][item]) is not int:
                        self.rStruct['sections'][rIndex]['options'][item] = int(self.rStruct['sections'][rIndex]['options'][item])

                # Fix some of the data field types - boolean
                for item in boolFields:
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

                # Get report-specific options - There must be a better way to do this
                optionTmp = globs.optionManager.getRcSection(section[0])
                for optTmp in optionTmp:
                    # Check for type
                    if optionTmp[optTmp].lower() in ['true', 'false']: # Boolean
                        self.rStruct['sections'][rIndex]['options'][optTmp] = True if optionTmp[optTmp].lower() == 'true' else False
                    else: # Integer or string
                        result = re.findall(r"\d+",optionTmp[optTmp])
                        if len(result) != 0: #Integer
                            self.rStruct['sections'][rIndex]['options'][optTmp] = int(optionTmp[optTmp])
                        else:
                            self.rStruct['sections'][rIndex]['options'][optTmp] = optionTmp[optTmp]

                # Fix some of the data field types - integers
                #for item in ('border', 'padding', 'normaldays', 'warningdays'):
                for item in intFields:
                    if type(self.rStruct['sections'][rIndex]['options'][item]) is not int:
                        self.rStruct['sections'][rIndex]['options'][item] = int(self.rStruct['sections'][rIndex]['options'][item])
            elif self.rStruct['sections'][rIndex]['type'] == 'lastseen':
                # Get default options
                self.rStruct['sections'][rIndex]['options'] = self.rStruct['defaults'].copy()

                # Get report-specific options
                optionTmp = globs.optionManager.getRcSection(section[0])
                for optTmp in optionTmp:
                    self.rStruct['sections'][rIndex]['options'][optTmp] = optionTmp[optTmp]

                # Fix some of the data field types - integers
                for item in intFields:
                    if type(self.rStruct['sections'][rIndex]['options'][item]) is not int:
                        self.rStruct['sections'][rIndex]['options'][item] = int(self.rStruct['sections'][rIndex]['options'][item])
            
            elif self.rStruct['sections'][rIndex]['type'] == 'offline':
                # Get default options
                self.rStruct['sections'][rIndex]['options'] = self.rStruct['defaults'].copy()

                # Get report-specific options
                optionTmp = globs.optionManager.getRcSection(section[0])
                for optTmp in optionTmp:
                    self.rStruct['sections'][rIndex]['options'][optTmp] = optionTmp[optTmp]

                # Fix some of the data field types - boolean
                if type (self.rStruct['sections'][rIndex]['options']['suppresscolumntitles']) is not bool:
                    self.rStruct['sections'][rIndex]['options']['suppresscolumntitles'] = self.rStruct['sections'][rIndex]['options']['suppresscolumntitles'].lower() in ('true')   

        # Add a section for runtime, if necessary
        if self.rStruct['defaults']['includeruntime'] == True:
            globs.log.write(globs.SEV_NOTICE, function='Report', action='Init', msg='Adding runtime report.')
            rIndex = len(self.rStruct['sections'])   # This will be the index number of the next element we add
            self.rStruct['sections'].append({})
 
            # Get section name & type & default options
            self.rStruct['sections'][rIndex]['name'] = 'runtime'
            self.rStruct['sections'][rIndex]['type'] = 'runtime'
            self.rStruct['sections'][rIndex]['options'] = self.rStruct['defaults'].copy()

        return None

    # Determine if a column specified in the .rc file is a valid column name
    def validateColumns(self, section, colSpec):
        globs.log.write(globs.SEV_NOTICE, function='Report', action='validateColumns', msg='Validating columns for [{}] report section.'.format(section))

        errRate = 0
        colList = colSpec
        # The first time around (checking the default colums) colList comes in as a string
        # By the time the individual report columns come in for checking, they have been converted to lists
        # Check if they're already lists to avoid program crashes
        if isinstance(colSpec, str):
            colList = splitRcIntoList(colSpec)

        for i in range(len(colList)):
            if colList[i][0] not in colNames:
                globs.log.write(globs.SEV_ERROR, function='Report', action='validateColumns', msg='ERROR: [{}] section: Column \'{}\' is an undefined field.'.format(section, colList[i][0]))
                errRate += 1
            if len(colList[i]) != 2:
                globs.log.write(globs.SEV_WARNING, function='Report', action='validateColumns', msg='WARNING: [{}] section: Column \'{}\' does not have a title definition. Defaulting to column name as title.'.format(section, colList[i][0]))
            elif colList[i][1] =='':
                globs.log.write(globs.SEV_WARNING, function='Report', action='validateColumns', msg='WARNING: [{}] section: Title field for column \'{}\' is empty. This is not an error, but that column will not have a title when printed.'.format(section, colList[i][0]))

        return errRate

    # Is the field valid for the specified report?
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
        globs.log.write(globs.SEV_NOTICE, function='Report', action='validateReportFields', msg='Validating report specifications in .rc file.')
        anyProblems = 0
        
        # First, check the default [report]columns section for validity
        anyProblems = self.validateColumns('report', self.rStruct['defaults']['columns'])

        # Now, validate each report in the [report]layout= option
        sectionList = splitRcIntoList(self.rStruct['defaults']['layout'])
        for i in range(len(sectionList)):
            sect = globs.optionManager.getRcSection(sectionList[i][0])
            #Section does not exist
            if sect == None: 
                globs.log.write(globs.SEV_ERROR, function='Report', action='validateReportFields', msg='ERROR: [report] section or command line specifies a report named \'{}\' but there is no corresponding \'[{}]\' section defined in the .rc file.'.format(sectionList[i][0], sectionList[i][0]))
                anyProblems += 1
            # Section doesn't have a 'type' field
            elif 'type' not in sect:
                globs.log.write(globs.SEV_ERROR,function='Report', action='validateReportFields', msg='ERROR: No \'type\' option in [{}] section. Valid types are \'report\', \'noactivity\', or \'lastseen\''.format(sectionList[i][0]))
                anyProblems += 1
            # Section has an invalid type field
            elif sect['type'] not in ['report', 'noactivity', 'lastseen', 'offline']:
                globs.log.write(globs.SEV_ERROR,function='Report', action='validateReportFields', msg='ERROR: [{}] section: invalid section type: \'{}\'. Must be \'report\', \'noactivity\', \'lastseen\', or \'offline\''.format(sectionList[i][0], sect['type']))
                anyProblems += 1
            # OK so far, check the section for correctness
            else:
                if 'columns' in sect:
                    anyProblems += self.validateColumns(sectionList[i][0], sect['columns'])

                for optName in sect:    # Check that each option is valid
                    # type and groupheading fields are OK
                    if optName in ['type', 'groupheading']:
                        continue
                    # Check syntax of groupby and column fields
                    if optName in ['groupby', 'columnsort']:    # See if these two fields are specified correctly
                        oList = splitRcIntoList(sect[optName])
                        for j in range(len(oList)):
                            if oList[j][0] not in colNames:
                                globs.log.write(globs.SEV_ERROR, function='Report', action='validateReportFields', msg='ERROR: [{}] section, \'{}\' option: invalid field name: \'{}\'. Must use a valid field name for this.'.format(sectionList[i][0], optName, oList[j][0]))
                                anyProblems += 1
                            if oList[j][1] not in ['ascending', 'descending']:
                                globs.log.write(globs.SEV_ERROR, function='Report', action='validateReportFields', msg='ERROR: [{}] section, \'{}\' option, \'{}\' field: invalid sort order: \'{}\'. Must be \'ascending\' or \'descending\'.'.format(sectionList[i][0], optName, oList[j][0], oList[j][1]))
                                anyProblems += 1
                    # Something else (weird) is happening
                    else:
                        if not self.isValidReportField(optName):
                            globs.log.write(globs.SEV_ERROR, function='Report', action='validateReportFields', msg='ERROR: [{}] section: invalid option: \'{}\'.'.format(sectionList[i][0], optName))
                            anyProblems += 1

        globs.log.write(globs.SEV_NOTICE, function='Report', action='validateReportFields', msg='Found {} report validation errors.'.format(anyProblems))
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
        globs.log.write(globs.SEV_NOTICE, function='Report', action='extractReportData', msg='Extracting report data.')

        # Initialize report table. Delete all existing rows
        dbCursor = globs.db.execSqlStmt("DELETE FROM report")
        globs.db.dbCommit()

        # Select source/destination pairs from database
        sqlStmt = "SELECT source, destination, lastTimestamp, lastFileCount, lastFileSize, dupversion FROM backupsets ORDER BY source, destination"

        # Loop through backupsets table and then get latest activity for each src/dest pair
        dbCursor = globs.db.execSqlStmt(sqlStmt)
        bkSetRows = dbCursor.fetchall()
        globs.log.write(globs.SEV_DEBUG, function='Report', action='extractReportData', msg='Backup set rows=[{}]'.format(bkSetRows))
        for source, destination, lastTimestamp, lastFileCount, lastFileSize, lastdupversion in bkSetRows:
            globs.log.write(globs.SEV_DEBUG, function='Report', action='extractReportData', msg='Next email record: Src={} Dest={} lastTimestamp={} lastFileCount={} lastFileSize={}  dupversion={}'.format(source, 
                destination, lastTimestamp, lastFileCount, lastFileSize, lastdupversion))

            # Select all activity for src/dest pair since last report run
            sqlStmt = 'SELECT dupVersion, endTimestamp, beginTimeStamp, duration, examinedFiles, sizeOfExaminedFiles, addedFiles, deletedFiles, modifiedFiles, \
                filesWithError, parsedResult, warnings, errors, messages, logdata, bytesUploaded, bytesDownloaded FROM emails WHERE sourceComp=\'{}\' AND destComp=\'{}\' \
                AND  endTimestamp > {} order by endTimestamp'.format(source, destination, lastTimestamp)
            dbCursor = globs.db.execSqlStmt(sqlStmt)

            emailRows = dbCursor.fetchall()
            globs.log.write(globs.SEV_DEBUG, function='Report', action='extractReportData', msg='Email rows=[{}]'.format(emailRows))
            if emailRows: 
                # Loop through each new activity and report
                for dupversion, endTimeStamp, beginTimeStamp, duration, examinedFiles, sizeOfExaminedFiles, addedFiles, deletedFiles, modifiedFiles, \
                    filesWithError, parsedResult, warnings, errors, messages, logdata, bytesUploaded, bytesDownloaded in emailRows:
            
                    # Determine file count & size difference from last run
                    examinedFilesDelta = examinedFiles - lastFileCount
                    globs.log.write(globs.SEV_DEBUG, function='Report', action='extractReportData', msg='Calculating examined files difference: {} - {} = {}'.format(examinedFiles, lastFileCount, examinedFilesDelta))
                    fileSizeDelta = sizeOfExaminedFiles - lastFileSize
                    globs.log.write(globs.SEV_DEBUG, function='Report', action='extractReportData', msg='Calculating examined file size difference: {} - {} = {}'.format(sizeOfExaminedFiles, lastFileSize, fileSizeDelta))

                    # Create date & time fields from timestamp field.
                    # This makes it much easier to extract & sort later on rather than trying to manipulate the timestamp at runtime
                    soloDate, soloTime = drdatetime.fromTimestamp(endTimeStamp, dfmt='YYYY-MM-DD')
                    soloDate += ' 00:00:00'
                    soloTime = '2000-01-01 ' + soloTime
                    reportDateStamp = drdatetime.toTimestamp(soloDate, 'YYYY-MM-DD', 'HH:MM:SS')
                    reportTimeStamp = drdatetime.toTimestamp(soloTime, 'YYYY-MM-DD', 'HH:MM:SS')
                    
                    # Convert from timestamp to date & time strings
                    sqlStmt = "INSERT INTO report (source, destination, timestamp, date, time, duration, examinedFiles, examinedFilesDelta, sizeOfExaminedFiles, fileSizeDelta, \
                        addedFiles, deletedFiles, modifiedFiles, filesWithError, parsedResult, messages, warnings, errors, dupversion, logdata, bytesUploaded, bytesDownloaded) \
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
                    rptData = (source, destination, endTimeStamp, reportDateStamp, reportTimeStamp, duration, examinedFiles, examinedFilesDelta, sizeOfExaminedFiles, fileSizeDelta, addedFiles, deletedFiles, modifiedFiles, filesWithError, parsedResult, messages, warnings, errors, dupversion, logdata, bytesUploaded, bytesDownloaded)
                    globs.db.execReportInsertSql(sqlStmt, rptData)

                    # Update latest activity into into backupsets
                    # Issue #138 - If the run was an error, there might not be a version number (depending on the Duplicati version)
                    # Get the current values of these fields, use them if the new ones are invalid.
                    sqlStmt = 'SELECT lastFileCount, lastFileSize, lasttimestamp, dupversion FROM backupsets WHERE source=\'{}\' AND destination=\'{}\''.format(source, destination)
                    dbCursor = globs.db.execSqlStmt(sqlStmt)
                    setRow = dbCursor.fetchone()
                    if dupversion == '':
                        dupversion = setRow[3]

                    sqlStmt = 'UPDATE backupsets SET lastFileCount={}, lastFileSize={}, lasttimestamp=\'{}\', dupversion=\'{}\' WHERE source=\'{}\' AND destination=\'{}\''.format(examinedFiles, sizeOfExaminedFiles, endTimeStamp, dupversion, source, destination)
                    globs.db.execSqlStmt(sqlStmt)
                    globs.db.dbCommit()

                    # Set last file count & size the latest information
                    lastFileCount = examinedFiles
                    lastFileSize = sizeOfExaminedFiles
        return None

    # Create report by looping through report sections
    def createReport(self, reportStructure, startTime):
        globs.log.write(globs.SEV_NOTICE, function='Report', action='createReport', msg='Beginning report creation.')

        reportOutput = {}
        reportOutput['sections'] = []

        # Loop through report configurations
        for reportSection in reportStructure['sections']:
            globs.log.write(globs.SEV_NOTICE, function='Report', action='createReport', msg='Creating report for {}.'.format(reportSection))
            if reportSection['type'] == 'report':
                if 'groupby' in reportSection['options']:
                    reportOutput['sections'].append(self.buildReportOutputYesGroups(reportSection))
                else:
                    reportOutput['sections'].append(self.buildReportOutputNoGroups(reportSection))
            elif reportSection['type'] == 'noactivity':
                reportOutput['sections'].append(self.buildNoActivityOutput(reportSection))
            elif reportSection['type'] == 'lastseen':
                reportOutput['sections'].append(self.buildLastSeenOutput(reportSection))
            elif reportSection['type'] == 'runtime':
                reportOutput['sections'].append(self.buildRuntimeOutput(reportSection, startTime))
            elif reportSection['type'] == 'offline':
                reportOutput['sections'].append(self.buildOfflineOutput(reportSection))
        return reportOutput

    # Manage the formatted Report storage in the class
    # Basically, if a report in a given format has already been generated, just return it. 
    # Otherwise, generate it, store it, and return it.
    def createFormattedOutput(self, reportOutput, type):
        globs.log.write(globs.SEV_NOTICE, function='Report', action='createFormattedOutput', msg='Creating formatted output for {} format'.format(type))

        # Has report already been created?
        if self.formattedReports[type] == None:
            # No. generate the report
            if type == 'html':
                self.formattedReports[type] = self.createHtmlFormat(globs.report.rStruct, reportOutput)
            elif type == 'txt':
                self.formattedReports[type] = self.createTextFormat(globs.report.rStruct, reportOutput) 
            elif type == 'csv':
                self.formattedReports[type] = self.createCsvFormat(globs.report.rStruct, reportOutput) 
            elif type == 'json':
                self.formattedReports[type] = self.createJsonFormat(globs.report.rStruct, reportOutput) 
        else:
            globs.log.write(globs.SEV_NOTICE, function='Report', action='createFormattedOutput', msg='{} report format already exists'.format(type))

        # Return what you got
        return self.formattedReports[type]

    # Perform some Python-Fu to update a tuple
    def updateTuple(self, tup, pos, newVal):
        listFromTup = list(tup)
        listFromTup[pos] = newVal
        newTup = tuple(listFromTup)
        return newTup 
    
    # Build "Program Running Time" report
    def buildRuntimeOutput(self, reportStructure, startTime):
        globs.log.write(globs.SEV_NOTICE, function='Report', action='buildRuntimeOutput', msg='Calculating running time.')

        timeDiff = time.time() - startTime
        runTime = time.strftime("%Hh:%Mm:%Ss", time.gmtime(timeDiff))

        singleReport = {}
        singleReport['name'] = 'runtime'
        singleReport['inlineColumnCount'] = 1
        singleReport['inlineColumnNames'] = []
        singleReport['inlineColumnNames'].append(['runtime', 'Runing Time', '#FFFFFF', toMarkup()]) # Column names are white and bold
        singleReport['title'] = 'Running Time'

        # Insert runningtime
        singleReport['dataRows'] = []
        singleReport['dataRows'].append([])
        singleReport['dataRows'][0].append([dataRowTypes['singleLine'], 1])
        singleReport['dataRows'][0].append(['Running Time: {}'.format(runTime), '#FFFFFF', toMarkup()])

        globs.log.write(globs.SEV_DEBUG, function='Report', action='buildRuntimeOutput', msg='Running time was {}.'.format(runTime))
        return singleReport

    
    def buildReport_Initialize(self, reportStructure):
        # singleReport is the output for just this specific report. 
        # It will be appended to reportOutput once it is filled in.
        # This is how we produce multiple reports from the same run.
        singleReport = {}

        # Copy basic report information from the report definition
        singleReport['name'] = reportStructure['name']
        singleReport['columnCount'] = len(reportStructure['options']['columns'])
        singleReport['columnNames'] = []
        globs.log.write(globs.SEV_NOTICE, function='Report', action='buildReport_Initialize', msg='Building single report: {}.'.format(singleReport['name']))
        
        # Each column gets a ['name', 'title', 'bgcolor', markup] list assigned to it
        for i in range(len(reportStructure['options']['columns'])):
            markup = toMarkup(bold=True, align=fldDefs[reportStructure['options']['columns'][i][0]][0])
            singleReport['columnNames'].append([reportStructure['options']['columns'][i][0], reportStructure['options']['columns'][i][1], '#FFFFFF', markup]) # Column names are white and bold
        
        # Assign the report title
        singleReport['title'] = reportStructure['options']['title']

        # If we're not showing errors, messages, etc inline, get an adjusted list of the inline column names and count
        # Use InlineColumnCount and inlineColumnnames throughout the rest of the routine to keep columns in sync
        # adjustColumnCountInfo() handles that for us
        singleReport['inlineColumnCount'], singleReport['inlineColumnNames'] = adjustColumnCountInfo(singleReport['columnCount'], singleReport['columnNames'], reportStructure['options']['weminline'])

        # dataRowIndex keeps track of what row we're currently adding to dataRows.
        # dataRows.append(), then increment index, then append data fields to dataRows[dataRowIndex]
        dataRowIndex = -1
        
        # 'dataRows' holds the resulting output data for the table
        singleReport['dataRows'] = []

        # Add the title row to the report
        singleReport['dataRows'].append([])
        dataRowIndex += 1
        # Title rows get a ['rptTitleType',columnCount], ['title', bgcolor, markup] list assignment. 
        # columCount = inlineColumnCount, because the single title row spans all columns in the report
        singleReport['dataRows'][dataRowIndex].append([dataRowTypes['rptTitle'], singleReport['inlineColumnCount']])
        singleReport['dataRows'][dataRowIndex].append([singleReport['title'], reportStructure['options']['titlebg'], toMarkup(bold=True, align="center")])

        return dataRowIndex, singleReport

    def buildReport_PrintGroup(self, groupName, reportStructure, singleReport, dataRowIndex):
        globs.log.write(globs.SEV_NOTICE, function='Report', action='buildReport_PrintGroup', msg='Printing group heading row.')
        # Build the subheading (title) for the group
        if 'groupheading' in reportStructure['options']:                    # Group heading already defined
            grpHeading = reportStructure['options']['groupheading']
        else:                                                               # Group heading not defined. Build it from 'groupby' columns
            grpHeading = ''
            for i in range(len(groupName)):
                grpHeading += str(groupName[i]) + ' '

        # Perform keyword substutution on the group heading
        for keyWdTmp in keyWordList:
            for i in range(len(reportStructure['options']['groupby'])):
                if reportStructure['options']['groupby'][i][0] == keyWdTmp: # field is one of the groupbys. See if you need to substitute that value
                    # Check for timestmp expansion
                    if keyWdTmp == 'date':
                        dateStr, timeStr = drdatetime.fromTimestamp(groupName[i], dfmt=globs.opts['dateformat'], tfmt=globs.opts['timeformat'])
                        grpHeading = grpHeading.replace(keyWordList[keyWdTmp], dateStr)
                    elif keyWdTmp == 'time':
                        dateStr, timeStr = drdatetime.fromTimestamp(groupName[i], dfmt=globs.opts['dateformat'], tfmt=globs.opts['timeformat'])
                        grpHeading = grpHeading.replace(keyWordList[keyWdTmp], timeStr)
                    else:
                        grpHeading = grpHeading.replace(keyWordList[keyWdTmp], str(groupName[i]))

        singleReport['dataRows'].append([])
        dataRowIndex += 1
        singleReport['dataRows'][dataRowIndex].append([dataRowTypes['grpHeading'], singleReport['inlineColumnCount']])
        singleReport['dataRows'][dataRowIndex].append([grpHeading, reportStructure['options']['groupheadingbg'], toMarkup(align="center")])

        return dataRowIndex, singleReport

    def buildReport_PrintTitles(self, reportStructure, singleReport, dataRowIndex):
        globs.log.write(globs.SEV_NOTICE, function='Report', action='buildReport_PrintTitles', msg='Printing column title row.')
        # Add column headings
        # Column headings (or 'titles' - the usage varies throughout the code) get a starting list of ['rowHeadDataType',1] (because each title spans 1 column in the report)
        # Then a series of ['columTitle', bgcolor, markup] lists, one for each column
        if reportStructure['options']['suppresscolumntitles'] == False:
            singleReport['dataRows'].append([])
            dataRowIndex += 1
            singleReport['dataRows'][dataRowIndex].append([dataRowTypes['rowHead'], 1])
            for i in range(singleReport['inlineColumnCount']):
                # Get the formatting for the title.
                # The text of the heading comes from the inlineColumNames list
                # The formatting coms from the fldDefs{} dictionary
                markup = toMarkup(bold=True, align = fldDefs[singleReport['inlineColumnNames'][i][0]][0])
                newStr = '{:{fmt}}'.format(singleReport['inlineColumnNames'][i][1], fmt=fldDefs[singleReport['inlineColumnNames'][i][0]][1])
                singleReport['dataRows'][dataRowIndex].append([newStr, '#FFFFFF', markup])

        return dataRowIndex, singleReport

    def getBackgroundColor(self, reportStructure, fldName, column, value, durationZeroes=None):
        # Figure out the appropriate background. We'll need this in a couple of places

        bGroundFlds = {
            'messages': reportStructure['options']['jobmessagebg'],
            'warnings': reportStructure['options']['jobwarningbg'], 
            'errors': reportStructure['options']['joberrorbg'], 
            'logdata': reportStructure['options']['joblogdatabg']
            }

        # Default color is white (#FFFFFF)
        bground = '#FFFFFF'
        if value != '':
            if fldName in bGroundFlds:
                msgType = reportStructure['options']['columns'][column][0]
                bground = bGroundFlds[msgType]

        return bground

    def adjustTimeFields(self, fldName, value, fldDef, durationzeroes):
        if fldName == 'date':
            markup = toMarkup(align=fldDef[0])
            dateStr, timeStr = drdatetime.fromTimestamp(value, dfmt=globs.opts['dateformat'], tfmt=globs.opts['timeformat'])
            newStr = '{:{fmt}}'.format(dateStr, fmt=fldDef[2])
        elif fldName == 'time':
            markup = toMarkup(align=fldDef[0])
            dateStr, timeStr = drdatetime.fromTimestamp(value, dfmt=globs.opts['dateformat'], tfmt=globs.opts['timeformat'])
            newStr = '{:{fmt}}'.format(timeStr, fmt=fldDef[2])
        elif fldName == 'duration':
            markup = toMarkup(align=fldDef[0])
            tDiff = drdatetime.timeDiff(value, durationzeroes)
            newStr = '{:{fmt}}'.format(tDiff, fmt=fldDef[2])

        return newStr, markup

    def checkWemFields(self, msg, reportOptions, column):
        shouldContinue = False
        truncatedMsg = msg

        # For these rows, each will go on a separate line, so put them in their own list for now.
        # If weminline == True, we would treat them line any other row
        if msg == '': 
            shouldContinue = True
        else: # Not empty. Let's see what kind of message it is. Then see if we want to display those (as per the .rc file options) and what the backgound color is
            msgType = reportOptions['columns'][column][0]
            if msgType == 'messages':
                if reportOptions['displaymessages'] == False:
                    shouldContinue = True
            elif msgType == 'warnings':
                if reportOptions['displaywarnings'] == False:
                    shouldContinue = True
            elif msgType == 'errors':
                if reportOptions['displayerrors'] == False:
                    shouldContinue = True
            elif msgType == 'logdata':
                if reportOptions['displaylogdata'] == False:
                    shouldContinue = True
            truncatedMsg = truncateWarnErrMsgs(msgType, msg, reportOptions)

        return shouldContinue, truncatedMsg
    
    def adjustFileSizeDisplay(self, field, sizeDisplay, singleRow, i):
        returnTup = singleRow

        if field in sizeFields and sizeDisplay != 'none': # Translate to 'mb' or 'gb'
            val = singleRow[i]
            if sizeDisplay[:2].lower() == 'mb':
                val = val / 1000000.00
            else:
                val = val / 1000000000.00
            
            returnTup = self.updateTuple(singleRow, i, val)  # Can't directly update a tuple, so need to perform some Python-Fu
        return returnTup
    
    # Crate a report that doesn't have any groups (groupby = None)
    # Take data from report table and build the resulting report structure.
    # Output structure will be used to generate the final report
    # 'reportStructure' is the report options as extracted from the .rc file
    # See docs/DataStructures/ConfigFormat for schema of reportStructure
    # See docs/DataStructures/ReportFormat for schema of reportOutput
    def buildReportOutputNoGroups(self, reportStructure):
        globs.log.write(globs.SEV_NOTICE, function='Report', action='buildReportOutputNoGroups', msg='Printing \'no group\' report output.')

        dataRowIndex, singleReport = self.buildReport_Initialize(reportStructure)
        dataRowIndex, singleReport = self.buildReport_PrintTitles(reportStructure, singleReport, dataRowIndex)

        # Build & execute the SQL statement to extract the rows from the report table
        sqlStmt = buildQuery(reportStructure['options'], groupby=False)
        dbCursor = globs.db.execSqlStmt(sqlStmt)
        rowList = dbCursor.fetchall()

        # Loop through all resulting Rows
        for singleRow in range(len(rowList)):
            
            # msgList holds the list of warn/err/log messages that aren't being displayed inline. Gets reset for each new data row extracted from the DB
            msgList = {}

            # Add another data row for this output
            singleReport['dataRows'].append([])
            dataRowIndex += 1

            # Data rows get a ['dataType', 1] list assignment to start
            # Then a series of [actualData, bgcolor, markup] lists, one for each column
            singleReport['dataRows'][dataRowIndex].append([dataRowTypes['data'], 1])

            # Print column values to dataRows
            # Here's where things get complicated. Buckle up, it's a bumpy ride
            
            # Loop through each column in the row
            for i in range(len(reportStructure['options']['columns'])):
                # Figure out the appropriate background. We'll need this in a couple of places
                # Default color is white (#FFFFFF)
                bground = self.getBackgroundColor(reportStructure, reportStructure['options']['columns'][i][0], i, rowList[singleRow][i])

                # See if we need to substitute date, time, or duration fields
                # All are stored as timestamp data, so they need to be converted to actual dates & times
                if reportStructure['options']['columns'][i][0] in timestampFields:
                    fldName = reportStructure['options']['columns'][i][0]
                    newStr, markup = self.adjustTimeFields(fldName, rowList[singleRow][i], fldDefs[fldName], reportStructure['options']['durationzeroes'])
                    singleReport['dataRows'][dataRowIndex].append([newStr, bground, markup])
                # Format message/warning/log lines properly
                elif ((reportStructure['options']['columns'][i][0] in wemFields) and (reportStructure['options']['weminline'] is False)):
                    shouldContinue, truncatedMsg  = self.checkWemFields(rowList[singleRow][i], reportStructure['options'], i)
                    if shouldContinue:
                        continue
                    markup = toMarkup(align=fldDefs[msgType][0])
                    # Error message lines get a [message, bground, markup, ColTitle] list assigned to it.
                    # Do all that stuff and add it to msgList for now.
                    msgList[reportStructure['options']['columns'][i][0]] = [truncatedMsg, bground, markup, reportStructure['options']['columns'][i][1]]
                # See if the field is one of the numeric fields. Need to add commas, right justify, & possibly reduce scale (mb/gb)
                elif reportStructure['options']['columns'][i][0] in numberFields:
                    rowList[singleRow] = self.adjustFileSizeDisplay(reportStructure['options']['columns'][i][0], reportStructure['options']['sizedisplay'], rowList[singleRow], i)
                    markup = toMarkup(align='right')
                    newStr = '{:{fmt}}'.format(rowList[singleRow][i], fmt=fldDefs[reportStructure['options']['columns'][i][0]][2])
                    singleReport['dataRows'][dataRowIndex].append([newStr, bground, markup])
                else:  # After all that checking, this is just a plain-old data field :-(
                    # See if we need to truncate WEM messages
                    msg = rowList[singleRow][i]
                    msgType = reportStructure['options']['columns'][i][0]
                    if reportStructure['options']['columns'][i][0] in wemFields:
                        msg = truncateWarnErrMsgs(msgType, msg, reportStructure['options'])
                    markup = toMarkup(align='left')
                    newStr = '{:{fmt}}'.format(msg, fmt=fldDefs[reportStructure['options']['columns'][i][0]][2])
                    singleReport['dataRows'][dataRowIndex].append([newStr, bground, markup])

            # If there are warnings, errors, messages to output and we don't want them inline, print separate lines after the main columns
            # WEM lines get [wemData, columnCount], [message] lists assigned to them
            if len(msgList) != 0 and reportStructure['options']['weminline'] is False:       
                for msg in msgList:
                    singleReport['dataRows'].append([])
                    dataRowIndex += 1
                    singleReport['dataRows'][dataRowIndex].append([dataRowTypes['wemData'], singleReport['inlineColumnCount']])
                    singleReport['dataRows'][dataRowIndex].append(msgList[msg])

        if len(rowList) == 0:    # No activity
            singleReport['dataRows'].append([])
            dataRowIndex += 1
            singleReport['dataRows'][dataRowIndex].append([dataRowTypes['data'], singleReport['inlineColumnCount']])
            singleReport['dataRows'][dataRowIndex].append(['No Activity', '#FFFFFF', toMarkup(italic=True)])

        return singleReport

    # Crate a report that doesn't have any groups (groupby = Yes)
    # Take data from report table and build the resulting report structure.
    # Output structure will be used to generate the final report
    # 'reportStructure' is the report options as extracted from the .rc file
    # See docs/DataStructures/ConfigFormat for schema of reportStructure
    # See docs/DataStructures/ReportFormat for schema of reportOutput
    def buildReportOutputYesGroups(self, reportStructure):
        globs.log.write(globs.SEV_NOTICE, function='Report', action='buildReportOutputYesGroups', msg='Printing \'grouped\' report output.')

        dataRowIndex, singleReport = self.buildReport_Initialize(reportStructure)

        sqlStmt = buildQuery(reportStructure['options'], groupby=True)
        dbCursor = globs.db.execSqlStmt(sqlStmt)
        groupList = dbCursor.fetchall()

        # Loop through the defined sections and create a new section for each group
        for groupName in groupList:

            dataRowIndex, singleReport =  self.buildReport_PrintGroup(groupName, reportStructure, singleReport, dataRowIndex)
            # If we're repeating column titles, print titles at the top of each group
            if reportStructure['options']['repeatcolumntitles'] == True and reportStructure['options']['suppresscolumntitles'] == False:
                dataRowIndex, singleReport = self.buildReport_PrintTitles(reportStructure, singleReport, dataRowIndex)

            sqlStmt = buildQuery(reportStructure['options'], whereOpts = groupName)
            dbCursor = globs.db.execSqlStmt(sqlStmt)
            rowList = dbCursor.fetchall()

            # Loop through all rows for that section
            for singleRow in range(len(rowList)):
                # msgList holds the list of warn/err/log messages that aren't being displayed inline. Gets reset for each new data row extracted from the DB
                msgList = {}

                # Add another data row for this output
                singleReport['dataRows'].append([])
                dataRowIndex += 1

                # Data rows get a ['dataType', 1] list assignment to start
                # Then a series of [actualData, bgcolor, markup] lists, one for each column
                singleReport['dataRows'][dataRowIndex].append([dataRowTypes['data'], 1])

                # Print column values to dataRows
                # Here's where things get complicated. Buckle up, it's a bumpy ride
            
                # Loop through each column in the row
                for i in range(len(reportStructure['options']['columns'])):
                
                    # Figure out the appropriate background. We'll need this in a couple of places
                    # Default color is white (#FFFFFF)
                    bground = self.getBackgroundColor(reportStructure, reportStructure['options']['columns'][i][0], i, rowList[singleRow][i])

                    # See if we need to substitute date, time, or duration fields
                    # All are stored as timestamp data, so they need to be converted to actual dates & times
                    if reportStructure['options']['columns'][i][0] in timestampFields:
                        fldName = reportStructure['options']['columns'][i][0]
                        newStr, markup = self.adjustTimeFields(fldName, rowList[singleRow][i], fldDefs[fldName], reportStructure['options']['durationzeroes'])
                        singleReport['dataRows'][dataRowIndex].append([newStr, bground, markup])
                    # Format message/warning/log lines properly
                    elif ((reportStructure['options']['columns'][i][0] in wemFields) and (reportStructure['options']['weminline'] is False)):
                        shouldContinue, truncatedMsg  = self.checkWemFields(rowList[singleRow][i], reportStructure['options'], i)
                        if shouldContinue:
                            continue
                        markup = toMarkup(align=fldDefs[msgType][0])
                        # Error message lines get a [message, bground, markup, ColTitle] list assigned to it.
                        # Do all that stuff and add it to msgList for now.
                        msgList[reportStructure['options']['columns'][i][0]] = [truncatedMsg, bground, markup, reportStructure['options']['columns'][i][1]]
                    # See if the field is one of the numeric fields. Need to add commas, right justify, & possibly reduce scale (mb/gb)
                    elif reportStructure['options']['columns'][i][0] in numberFields:
                        rowList[singleRow] = self.adjustFileSizeDisplay(reportStructure['options']['columns'][i][0], reportStructure['options']['sizedisplay'], rowList[singleRow], i)
                        markup = toMarkup(align='right')
                        newStr = '{:{fmt}}'.format(rowList[singleRow][i], fmt=fldDefs[reportStructure['options']['columns'][i][0]][2])
                        singleReport['dataRows'][dataRowIndex].append([newStr, bground, markup])
                    else:  # After all that checking, this is just a plain-old data field :-(
                        # See if we need to truncate WEM messages
                        msg = rowList[singleRow][i]
                        msgType = reportStructure['options']['columns'][i][0]
                        if reportStructure['options']['columns'][i][0] in wemFields:
                            msg = truncatedMsg = truncateWarnErrMsgs(msgType, msg, reportStructure['options'])
                        markup = toMarkup(align='left')
                        newStr = '{:{fmt}}'.format(msg, fmt=fldDefs[reportStructure['options']['columns'][i][0]][2])
                        singleReport['dataRows'][dataRowIndex].append([newStr, bground, markup])

                # If there are warnings, errors, messages to output and we don't want them inline, print separate lines after the main columns
                # WEM lines get [wemData, columnCount], [message] lists assigned to them
                if len(msgList) != 0 and reportStructure['options']['weminline'] is False:       
                    for msg in msgList:
                        singleReport['dataRows'].append([])
                        dataRowIndex += 1
                        singleReport['dataRows'][dataRowIndex].append([dataRowTypes['wemData'], singleReport['inlineColumnCount']])
                        singleReport['dataRows'][dataRowIndex].append(msgList[msg])

            if len(rowList) == 0:    # No activity
                singleReport['dataRows'].append([])
                dataRowIndex += 1
                singleReport['dataRows'][dataRowIndex].append([dataRowTypes['singleLine'], singleReport['inlineColumnCount']])
                singleReport['dataRows'][dataRowIndex].append(['No Activity', '#FFFFFF', toMarkup(italic=True)])

        if len(groupList) == 0:    # No activity
            singleReport['dataRows'].append([])
            dataRowIndex += 1
            singleReport['dataRows'][dataRowIndex].append([dataRowTypes['data'], singleReport['inlineColumnCount']])
            singleReport['dataRows'][dataRowIndex].append(['No Activity', '#FFFFFF', toMarkup(italic=True)])

        return singleReport

    def buildNoActivityOutput(self, reportStructure):
        globs.log.write(globs.SEV_NOTICE, function='Report', action='buildNoActivityOutput', msg='Printing \'No Activity\' report output.')

        singleReport = {}

        # Copy basic report information from the report definition
        singleReport['name'] = reportStructure['name']
        singleReport['title'] = reportStructure['options']['title']
        singleReport['columnCount'] = 3
        singleReport['columnNames'] = []

        markup = toMarkup(bold=True)
        titleBg = reportStructure['options']['titlebg']
        singleReport['columnNames'].append(['source', 'Source', titleBg, markup])
        singleReport['columnNames'].append(['destination', 'Destination', titleBg, markup])
        singleReport['columnNames'].append(['lastseen', 'Last Seen', titleBg, markup])
        singleReport['inlineColumnCount'] = 3
        singleReport['inlineColumnNames'] = singleReport['columnNames']

        dataRowIndex = -1
        singleReport['dataRows'] = []

        # Add the title row to the report
        singleReport['dataRows'].append([])
        dataRowIndex += 1
        # Title rows get a ['rptTitleType',columnCount], ['title', bgcolor, markup] list assignment. 
        # columCount = inlineColumnCount, because the single title row spans all columns in the report
        singleReport['dataRows'][dataRowIndex].append([dataRowTypes['rptTitle'], singleReport['inlineColumnCount']])
        singleReport['dataRows'][dataRowIndex].append([singleReport['title'], reportStructure['options']['titlebg'], toMarkup(bold=True, align="center")])

        # Add column headings
        # Column headings (or 'titles' - the usage varies throughout the code) get a starting list of ['rowHeadDataType',1] (because each title spans 1 column in the report)
        # Then a series of ['columTitle', bgcolor, markup] lists, one for each column
        if reportStructure['options']['suppresscolumntitles'] == False:
            singleReport['dataRows'].append([])
            dataRowIndex += 1
            singleReport['dataRows'][dataRowIndex].append([dataRowTypes['rowHead'], 1])
            for i in range(singleReport['inlineColumnCount']):
                # Get the formatting for the title.
                # The text of the heading comes from the inlineColumNames list
                # The formatting coms from the fldDefs{} dictionary
                markup = toMarkup(bold=True, align = fldDefs[singleReport['inlineColumnNames'][i][0]][0])
                newStr = '{:{fmt}}'.format(singleReport['inlineColumnNames'][i][1], fmt=fldDefs[singleReport['inlineColumnNames'][i][0]][1])
                singleReport['dataRows'][dataRowIndex].append([newStr, '#FFFFFF', markup])

        # Select all source/destination pairs (& last seen timestamp) from the backupset list 
        sqlStmt = "SELECT DISTINCT source, destination, lasttimestamp FROM backupsets"
        dbCursor = globs.db.execSqlStmt(sqlStmt)
        sourceDestList = dbCursor.fetchall()

        for source, destination, lastTimestamp in sourceDestList:
            sqlStmt = "SELECT count(*) FROM report WHERE source='{}' and destination='{}'".format(source, destination)
            dbCursor = globs.db.execSqlStmt(sqlStmt)
            countRows = dbCursor.fetchone()

            if countRows[0] == 0:
                # Calculate days since last activity & set background accordingly
                srcDest = '{}{}{}'.format(source, globs.opts['srcdestdelimiter'], destination)
                diff = drdatetime.daysSince(lastTimestamp)
                pastInterval, interval = pastBackupInterval(srcDest, diff)

                if interval == 0:   # Normal backup times apply
                    bgColor = reportStructure['options']['normalbg']
                    if diff > reportStructure['options']['normaldays']:
                        bgColor = reportStructure['options']['warningbg']
                    if diff > reportStructure['options']['warningdays']:
                        bgColor = reportStructure['options']['errorbg']
                else:   # Backup interval in play
                    bgColor = reportStructure['options']['normalbg']
                    if diff > interval:
                        bgColor = reportStructure['options']['warningbg']
                    if diff > (interval + int(reportStructure['options']['warningdays'])):
                        bgColor = reportStructure['options']['errorbg']

                # Add another data row for this output
                singleReport['dataRows'].append([])
                dataRowIndex += 1

                # Add row descriptor information
                singleReport['dataRows'][dataRowIndex].append([dataRowTypes['data'], 1])

                # If src/dest is known offline, add an indicator
                srcDest = '{}{}{}'.format(source, globs.opts['srcdestdelimiter'], destination)
                offline = globs.optionManager.getRcOption(srcDest, 'offline')
                isOffline = False
                if offline != None:  
                    if offline.lower() in ('true'):
                        isOffline = True
                globs.log.write(globs.SEV_DEBUG, function='Report', action='buildNoActivityOutput', msg='SrcDest=[{}] isOffline=[{}]'.format(srcDest, isOffline))
                if isOffline and reportStructure['options']['showoffline'] == False:  # don't want to show offline backups
                    continue

                markupPlain = toMarkup()
                markupItal = toMarkup(italic=True)
                # See if we're past the backup interval before reporting
                singleReport['dataRows'][dataRowIndex].append([source, '#FFFFFF', markupPlain])
                singleReport['dataRows'][dataRowIndex].append([destination,'#FFFFFF', markupPlain])
                if pastInterval is False:
                    globs.log.write(globs.SEV_DEBUG, function='Report', action='buildNoActivityOutput', msg='SrcDest=[{}] DaysDiff=[{}]. Skip reporting'.format(srcDest, diff))
                    if isOffline:
                        singleReport['dataRows'][dataRowIndex].append(['[OFFLINE] {} days ago. Backup interval is {} days.'.format(diff, interval), bgColor, markupPlain])
                    else:
                        singleReport['dataRows'][dataRowIndex].append(['{} days ago. Backup interval is {} days.'.format(diff, interval), bgColor, markupPlain])
                else:
                    lastDateStr, lastTimeStr = drdatetime.fromTimestamp(lastTimestamp)
                    if isOffline:
                        singleReport['dataRows'][dataRowIndex].append(['[OFFLINE] Last activity on {} at {} ({} days ago)'.format(lastDateStr, lastTimeStr, diff), bgColor, markupItal])
                    else:
                        singleReport['dataRows'][dataRowIndex].append(['Last activity on {} at {} ({} days ago)'.format(lastDateStr, lastTimeStr, diff), bgColor, markupItal])
    
        if dataRowIndex == -1:  # No rows in unseen table
            singleReport['dataRows'].append([])
            dataRowIndex += 1
            singleReport['dataRows'][dataRowIndex].append([dataRowTypes['data'], singleReport['inlineColumnCount']])
            singleReport['dataRows'][dataRowIndex].append(['No Activity', '#FFFFFF', toMarkup(italic=True)])

        return singleReport

    def buildLastSeenOutput(self, reportStructure):
        globs.log.write(globs.SEV_NOTICE, function='Report', action='buildLastSeenOutput', msg='Printing \'Last Seen\' report output.')

        singleReport = {}

        # Copy basic report information from the report definition
        singleReport['name'] = reportStructure['name']
        singleReport['title'] = reportStructure['options']['title']
        singleReport['columnCount'] = 3
        singleReport['columnNames'] = []

        markup = toMarkup(bold=True)
        titleBg = reportStructure['options']['titlebg']
        singleReport['columnNames'].append(['source', 'Source', titleBg, markup])
        singleReport['columnNames'].append(['destination', 'Destination', titleBg, markup])
        singleReport['columnNames'].append(['dupversion', 'Duplicati Version', titleBg, markup])
        singleReport['columnNames'].append(['lastseen', 'Last Seen', titleBg, markup])
        singleReport['inlineColumnCount'] = 4
        singleReport['inlineColumnNames'] = singleReport['columnNames']

        dataRowIndex = -1
        singleReport['dataRows'] = []

        # Add the title row to the report
        singleReport['dataRows'].append([])
        dataRowIndex += 1
        # Title rows get a ['rptTitleType',columnCount], ['title', bgcolor, markup] list assignment. 
        # columCount = inlineColumnCount, because the single title row spans all columns in the report
        singleReport['dataRows'][dataRowIndex].append([dataRowTypes['rptTitle'], singleReport['inlineColumnCount']])
        singleReport['dataRows'][dataRowIndex].append([singleReport['title'], reportStructure['options']['titlebg'], toMarkup(bold=True, align="center")])

        # Add column headings
        # Column headings (or 'titles' - the usage varies throughout the code) get a starting list of ['rowHeadDataType',1] (because each title spans 1 column in the report)
        # Then a series of ['columTitle', bgcolor, markup] lists, one for each column
        if reportStructure['options']['suppresscolumntitles'] == False:
            singleReport['dataRows'].append([])
            dataRowIndex += 1
            singleReport['dataRows'][dataRowIndex].append([dataRowTypes['rowHead'], 1])
            for i in range(singleReport['inlineColumnCount']):
                # Get the formatting for the title.
                # The text of the heading comes from the inlineColumNames list
                # The formatting coms from the fldDefs{} dictionary
                markup = toMarkup(bold=True, align = fldDefs[singleReport['inlineColumnNames'][i][0]][0])
                newStr = '{:{fmt}}'.format(singleReport['inlineColumnNames'][i][1], fmt=fldDefs[singleReport['inlineColumnNames'][i][0]][1])
                singleReport['dataRows'][dataRowIndex].append([newStr, '#FFFFFF', markup])

        # Select all source/destination pairs (& last seen timestamp) from the backupset list 
        sqlStmt = "SELECT source, destination, dupversion, lastTimestamp FROM backupsets ORDER BY source, destination"
        dbCursor = globs.db.execSqlStmt(sqlStmt)
        sourceDestList = dbCursor.fetchall()
        globs.log.write(globs.SEV_DEBUG, function='Report', action='buildLastSeenOutput', msg='sourceDestList=[{}]'.format(sourceDestList))

        for source, destination, dupversion, lastTimestamp in sourceDestList:
            # If src/dest is known offline, skip
            srcDest = source + globs.opts['srcdestdelimiter'] + destination
            
            # See if the S/D job is offline
            isOffline = False
            offline = globs.optionManager.getRcOption(srcDest, 'offline')
            if offline != None:  
                if offline.lower() in ('true'):
                    isOffline = True
            globs.log.write(globs.SEV_DEBUG, function='Report', action='buildNoActivityOutput', msg='SrcDest=[{}] isOffline=[{}]'.format(srcDest, isOffline))
            if isOffline and reportStructure['options']['showoffline'] == False:  # don't want to show offline backups
                continue

            lastDate = drdatetime.fromTimestamp(lastTimestamp)
            diff = drdatetime.daysSince(lastTimestamp)

            # Calculate days since last activity & set background accordingly
            pastInterval, interval = pastBackupInterval(srcDest, diff)

            # This section is ripe for optimization
            if interval == 0:   # Normal backup times apply
                bgColor = reportStructure['options']['normalbg']
                if diff > reportStructure['options']['normaldays']:
                    bgColor = reportStructure['options']['warningbg']
                if diff > reportStructure['options']['warningdays']:
                    bgColor = reportStructure['options']['errorbg']
            else:   # Backup interval in play
                bgColor = reportStructure['options']['normalbg']
                if diff > interval:
                    bgColor = reportStructure['options']['warningbg']
                if diff > (interval + int(reportStructure['options']['warningdays'])):
                    bgColor = reportStructure['options']['errorbg']

            
            # Add another data row for this output
            singleReport['dataRows'].append([])
            dataRowIndex += 1

            # Add row descriptor information
            singleReport['dataRows'][dataRowIndex].append([dataRowTypes['data'], 1])

            markupPlain = toMarkup()
            markupItal = toMarkup(italic=True)
            # See if we're past the backup interval before reporting
            singleReport['dataRows'][dataRowIndex].append([source, '#FFFFFF', markupPlain])
            singleReport['dataRows'][dataRowIndex].append([destination,'#FFFFFF', markupPlain])
            singleReport['dataRows'][dataRowIndex].append([dupversion,'#FFFFFF', markupPlain])
            if pastInterval is False:
                globs.log.write(globs.SEV_DEBUG, function='Report', action='buildLastSeenOutput', msg='SrcDest=[{}] DaysDiff=[{}]. Skip reporting'.format(srcDest, diff))
                if isOffline == False:
                    singleReport['dataRows'][dataRowIndex].append(['{} days ago. Backup interval is {} days.'.format(diff, interval), bgColor, markupPlain])
                elif reportStructure['options']['showoffline']:
                    singleReport['dataRows'][dataRowIndex].append(['[OFFLINE] {} days ago. Backup interval is {} days.'.format(diff, interval), bgColor, markupPlain])
            else:
                lastDateStr, lastTimeStr = drdatetime.fromTimestamp(lastTimestamp)
                if isOffline == False:
                    singleReport['dataRows'][dataRowIndex].append(['Last activity on {} at {} ({} days ago)'.format(lastDateStr, lastTimeStr, diff), bgColor, markupItal])
                elif reportStructure['options']['showoffline']:
                    singleReport['dataRows'][dataRowIndex].append(['[OFFLINE] Last activity on {} at {} ({} days ago)'.format(lastDateStr, lastTimeStr, diff), bgColor, markupItal])

        return singleReport

    def buildOfflineOutput(self, reportStructure):
        globs.log.write(globs.SEV_NOTICE, function='Report', action='buildOfflineOutput', msg='Printing \'Offline\' report output.')

        singleReport = {}

        # Copy basic report information from the report definition
        singleReport['name'] = reportStructure['name']
        singleReport['title'] = reportStructure['options']['title']
        singleReport['columnCount'] = 1
        singleReport['columnNames'] = []

        markup = toMarkup(bold=True)
        titleBg = reportStructure['options']['titlebg']
        singleReport['columnNames'].append(['srcdest', 'Source{}Destination'.format(globs.opts['srcdestdelimiter']), titleBg, markup])
        singleReport['inlineColumnCount'] = 1
        singleReport['inlineColumnNames'] = singleReport['columnNames']

        dataRowIndex = -1
        singleReport['dataRows'] = []

        # Add the title row to the report
        singleReport['dataRows'].append([])
        dataRowIndex += 1
        # Title rows get a ['rptTitleType',columnCount], ['title', bgcolor, markup] list assignment. 
        # columCount = inlineColumnCount, because the single title row spans all columns in the report
        singleReport['dataRows'][dataRowIndex].append([dataRowTypes['rptTitle'], singleReport['inlineColumnCount']])
        singleReport['dataRows'][dataRowIndex].append([singleReport['title'], reportStructure['options']['titlebg'], toMarkup(bold=True, align="center")])

        # Add column headings
        # Column headings (or 'titles' - the usage varies throughout the code) get a starting list of ['rowHeadDataType',1] (because each title spans 1 column in the report)
        # Then a series of ['columTitle', bgcolor, markup] lists, one for each column
        if reportStructure['options']['suppresscolumntitles'] == False:
            singleReport['dataRows'].append([])
            dataRowIndex += 1
            singleReport['dataRows'][dataRowIndex].append([dataRowTypes['rowHead'], 1])
            for i in range(singleReport['inlineColumnCount']):
                # Get the formatting for the title.
                # The text of the heading comes from the inlineColumNames list
                # The formatting coms from the fldDefs{} dictionary
                markup = toMarkup(bold=True, align = fldDefs[singleReport['inlineColumnNames'][i][0]][0])
                newStr = '{:{fmt}}'.format(singleReport['inlineColumnNames'][i][1], fmt=fldDefs[singleReport['inlineColumnNames'][i][0]][1])
                singleReport['dataRows'][dataRowIndex].append([newStr, '#FFFFFF', markup])

        # Walk through .rc file looking for 'offline=true'
        offlineCount = 0
        for each_section in globs.optionManager.parser.sections():
            hasOffline = globs.optionManager.getRcOption(each_section,'offline')
            if hasOffline != None and hasOffline.lower() == 'true':
                singleReport['dataRows'].append([])
                dataRowIndex += 1
                offlineCount += 1

                # Add row descriptor information
                singleReport['dataRows'][dataRowIndex].append([dataRowTypes['data'], 1])
                singleReport['dataRows'][dataRowIndex].append([each_section, '#FFFFFF', toMarkup()])

        if offlineCount == 0:
            singleReport['dataRows'].append([])
            dataRowIndex += 1
            singleReport['dataRows'][dataRowIndex].append([dataRowTypes['data'], 1])
            singleReport['dataRows'][dataRowIndex].append(['None', '#FFFFFF', toMarkup(italic=True)])


        return singleReport

    def createHtmlFormat(self, reportStructure, reportOutput):
        globs.log.write(globs.SEV_NOTICE, function='Report', action='createHtmlFormat', msg='Creating HTML formatted output.')
        msgHtml = '<html><head></head><body>\n'
        sectionIndex = -1
        for reportSection in reportOutput['sections']:
            sectionIndex += 1
            rptName = reportSection['name']
            rptOptions = reportStructure['sections'][sectionIndex]['options']
            
            # Start table
            msgHtml += '<table border={} cellpadding="{}">\n'.format(rptOptions['border'], rptOptions['padding'])

            for dataRowIndex in range(len(reportSection['dataRows'])):
                rowType, colspan = reportSection['dataRows'][dataRowIndex][0]
                if rowType == dataRowTypes['rptTitle']:
                    start, end, align = fromMarkup(reportSection['dataRows'][dataRowIndex][1][2])
                    msgHtml += '<tr><td align=\"{}\" colspan=\"{}\" bgcolor=\"{}\">{}{}{}</td></tr>\n'.format(align, colspan, reportSection['dataRows'][dataRowIndex][1][1], start, reportSection['dataRows'][dataRowIndex][1][0], end)
                elif rowType == dataRowTypes['grpHeading']:
                    start, end, align = fromMarkup(reportSection['dataRows'][dataRowIndex][1][2])
                    msgHtml += '<tr><td align=\"{}\" colspan="{}" bgcolor="{}">{}{}{}</td></tr>\n'.format(align, colspan, reportSection['dataRows'][dataRowIndex][1][1], start, reportSection['dataRows'][dataRowIndex][1][0], end)
                elif rowType in [dataRowTypes['rowHead'], dataRowTypes['data']]:
                    msgHtml += '<tr>'
                    for column in range(1,len(reportSection['dataRows'][dataRowIndex])):
                        element = reportSection['dataRows'][dataRowIndex][column]
                        start, end, align = fromMarkup(element[2])
                        msgHtml += '<td align=\"{}\" colspan=\"{}\" bgcolor=\"{}\" >{}{}{}</td>'.format(align, colspan, element[1], start, element[0], end)
                    msgHtml += '</tr>\n'
                elif rowType == dataRowTypes['wemData']:
                    start, end, align = fromMarkup(reportSection['dataRows'][dataRowIndex][1][2])
                    msgHtml += '<tr><td align=\"{}\" colspan="{}" bgcolor="{}"><details><summary>{}</summary><p>{}{}{}</td></tr>'.format(align, colspan, reportSection['dataRows'][dataRowIndex][1][1], reportSection['dataRows'][dataRowIndex][1][3], start, reportSection['dataRows'][dataRowIndex][1][0], end)
                elif rowType == dataRowTypes['singleLine']:
                    start, end, align = fromMarkup(reportSection['dataRows'][dataRowIndex][1][2])
                    msgHtml += '<tr><td align=\"{}\" colspan="{}" bgcolor="{}">{}{}{}</td></tr>\n'.format(align, colspan, reportSection['dataRows'][dataRowIndex][1][1], start, reportSection['dataRows'][dataRowIndex][1][0], end)
                else:
                    pass    # Invalid data row descriptor

            msgHtml += '</table><br>\n'

        msgHtml += '<br>Report generated by <a href=\'https://github.com/HandyGuySoftware/dupReport\'>dupReport</a> Version {}.{}.{} ({})<br>\n'.format(globs.version[0], globs.version[1], globs.version[2], globs.status)
        msgHtml += '</body></html>\n'

        return msgHtml

    def createTextFormat(self, reportStructure, reportOutput):
        globs.log.write(globs.SEV_NOTICE, function='Report', action='createTextFormat', msg='Creating text formatted output.')
        msgText = ''
        SectionIndex = -1
        for reportSection in reportOutput['sections']:
            SectionIndex += 1
            rptName = reportSection['name']
            rptOptions = reportStructure['sections'][SectionIndex]['options']
            
            # Start table
            for dataRowIndex in range(len(reportSection['dataRows'])):
                rowType, colspan = reportSection['dataRows'][dataRowIndex][0]
                if rowType in [dataRowTypes['rptTitle'], dataRowTypes['grpHeading'], dataRowTypes['wemData'], dataRowTypes['singleLine']]:
                    msgText += '{}\n'.format(reportSection['dataRows'][dataRowIndex][1][0])
                elif rowType in [dataRowTypes['rowHead'], dataRowTypes['data']]:
                    for column in range(1,len(reportSection['dataRows'][dataRowIndex])):
                        element = reportSection['dataRows'][dataRowIndex][column]
                        msgText += '{}'.format(element[0])
                    msgText += '\n'
                else:
                    pass    # Invalid data row descriptor

            msgText += '\n'

        msgText += 'Report generated by dupReport (https://github.com/HandyGuySoftware/dupReport) Version {}.{}.{} ({})\n'.format(globs.version[0], globs.version[1], globs.version[2], globs.status)

        return msgText

    def createCsvFormat(self, reportStructure, reportOutput):
        globs.log.write(globs.SEV_NOTICE, function='Report', action='createCsvFormat', msg='Creating CSV formatted output.')
        msgCsv = ''
        SectionIndex = -1
        for reportSection in reportOutput['sections']:
            SectionIndex += 1
            rptName = reportSection['name']
            rptOptions = reportStructure['sections'][SectionIndex]['options']
            
            # Start table
            for dataRowIndex in range(len(reportSection['dataRows'])):
                rowType, colspan = reportSection['dataRows'][dataRowIndex][0]
                if rowType in [dataRowTypes['rptTitle'], dataRowTypes['grpHeading'], dataRowTypes['wemData'], dataRowTypes['singleLine']]:
                    msgCsv += '\"{}\"\n'.format(reportSection['dataRows'][dataRowIndex][1][0].strip())
                elif rowType in [dataRowTypes['rowHead'], dataRowTypes['data']]:
                    for column in range(1,len(reportSection['dataRows'][dataRowIndex])):
                        element = reportSection['dataRows'][dataRowIndex][column]
                        msgCsv += '\"{}\",'.format(element[0].strip())
                    msgCsv += '\n'
                else:
                    pass    # Invalid data row descriptor
        msgCsv += '\"Report generated by dupReport (https://github.com/HandyGuySoftware/dupReport) Version {}.{}.{} ({})\"\n'.format(globs.version[0], globs.version[1], globs.version[2], globs.status)

        return msgCsv

    def createJsonFormat(self, reportStructure, reportOutput):
        globs.log.write(globs.SEV_NOTICE, function='Report', action='createJsonFormat', msg='Creating JSON formatted output.')
        return reportOutput

