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
    'logdata':              ('left',        '50',       '50')
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
colNames = ['source','destination','date','time','examinedFiles','examinedFilesDelta','sizeOfExaminedFiles','fileSizeDelta','addedFiles','deletedFiles','modifiedFiles','filesWithError','parsedResult','messages','warnings','errors','duration','logdata','dupversion']

# List of allowable keyword substitutions
keyWordList = { 
    #  database field: keyword mask
    'source':       '#SOURCE#',
    'destination':  '#DESTINATION#', 
    'date':         '#DATE#', 
    'time':         '#TIME#'
    }

markupDefs = {
    'bold':         0x01,
    'italic':       0x02,
    'underline':    0x04,
    'left':         0x08,
    'center':       0x10,
    'right':        0x20
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
            if newColNames[i][0] in ['messages', 'warnings', 'errors', 'logdata']:
                newColNames.pop(i)
                newColCount -= 1
    
    return newColCount, newColNames

def sendReportToFiles(reportOutput):
    
    # Loop through filespec list provided on command line
    # Split into file names and formats
    for fspec in globs.ofileList:
        fsplit = fspec[0].split(',')
        fileName = fsplit[0]
        format = fsplit[1]

        msgContent = globs.report.createFormattedOutput(reportOutput, format) 
        if fileName == 'stdout':
            sys.stdout.write(msgContent)
        elif fileName == 'stderr':
            sys.stderr.write(msgContent)
        else:
            try:
                outfile = open(fileName,'w')
            except (OSError, IOError):
                sys.stderr.write('Error opening output file: {}\n'.format(fileName))
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
    globs.log.write(1,'report.pastBackupWarningThreshold({}, {}, {})'.format(src, dest, nDays))

    srcDest = src + globs.opts['srcdestdelimiter'] + dest

    nbwVal = globs.optionManager.getRcOption(srcDest, 'nobackupwarn')
    if nbwVal is not None:
        nbwVal = int(nbwVal)    # getRcOption returns a string, we need an int
    else:
        nbwVal = nbWarnDefault

    globs.log.write(3,'Nobackup warning threshold is {} days.'.format(nbwVal))

    retVal = False
    if (nbwVal != 0) and (nDays >= nbwVal):     # Past threshold - need to warn
        retVal = True

    globs.log.write(3,'pastBackupWarningThreshold returning {}'.format(retVal))
    return retVal

def buildWarningMessage(source, destination, nDays, lastTimestamp, opts):
    globs.log.write(1,'buildWarningMessage({}, {}, {}, {})'.format(source, destination, nDays, lastTimestamp))
    lastDateStr, lastTimeStr = drdatetime.fromTimestamp(lastTimestamp)
    srcDest = source + globs.opts['srcdestdelimiter'] + destination

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
        for item in ('displaymessages', 'displaywarnings', 'displayerrors', 'displaylogdata', 'repeatcolumntitles', 'suppresscolumntitles', 'durationzeroes', 'weminline', 'includeruntime'):
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
                for item in ('border', 'padding', 'nobackupwarn', 'truncatemessage', 'truncatewarning', 'truncateerror', 'truncatelogdata'):
                    if type(self.rStruct['sections'][rIndex]['options'][item]) is not int:
                        self.rStruct['sections'][rIndex]['options'][item] = int(self.rStruct['sections'][rIndex]['options'][item])

                # Fix some of the data field types - boolean
                for item in ('displaymessages', 'displaywarnings', 'displayerrors', 'displaylogdata', 'repeatcolumntitles', 'suppresscolumntitles', 'durationzeroes', 'weminline'):
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
                optionTmp = globs.optionManager.getRcSection(section[0])
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
                optionTmp = globs.optionManager.getRcSection(section[0])
                for optTmp in optionTmp:
                    self.rStruct['sections'][rIndex]['options'][optTmp] = optionTmp[optTmp]

                # Fix some of the data field types - integers
                for item in ('border', 'padding', 'normaldays', 'warningdays'):
                    if type(self.rStruct['sections'][rIndex]['options'][item]) is not int:
                        self.rStruct['sections'][rIndex]['options'][item] = int(self.rStruct['sections'][rIndex]['options'][item])

        # Add a section for runtime, if necessary
        if self.rStruct['defaults']['includeruntime'] == True:
            rIndex = len(self.rStruct['sections'])   # This will be the index number of the next element we add
            self.rStruct['sections'].append({})
 
            # Get section name & type & default options
            self.rStruct['sections'][rIndex]['name'] = 'runtime'
            self.rStruct['sections'][rIndex]['type'] = 'runtime'
            self.rStruct['sections'][rIndex]['options'] = self.rStruct['defaults'].copy()

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
            #Section does not exist
            if sect == None: 
                globs.log.err('ERROR: [report] section or command line specifies a report named \'{}\' but there is no corresponding \'[{}]\' section defined in the .rc file.'.format(sectionList[i][0], sectionList[i][0]))
                globs.log.write(1, 'ERROR: [report] section or command line specifies a report named \'{}\' but there is no corresponding \'[{}]\' section defined in the .rc file.'.format(sectionList[i][0], sectionList[i][0]))
                anyProblems += 1
            # Section doesn't have a 'type' field
            elif 'type' not in sect:
                globs.log.err('ERROR: No \'type\' option in [{}] section. Valid types are \'report\', \'noactivity\', or \'lastseen\''.format(sectionList[i][0]))
                globs.log.write(1,'ERROR: No \'type\' option in [{}] section. Valid types are \'report\', \'noactivity\', or \'lastseen\''.format(sectionList[i][0]))
                anyProblems += 1
            # Section has an invalid type field
            elif sect['type'] not in ['report', 'noactivity', 'lastseen']:
                globs.log.write(1,'ERROR: [{}] section: invalid section type: \'{}\'. Must be \'report\', \'noactivity\', or \'lastseen\''.format(sectionList[i][0], sect['type']))
                globs.log.err('ERROR: [{}] section: invalid section type: \'{}\'. Must be \'report\', \'noactivity\', or \'lastseen\''.format(sectionList[i][0], sect['type']))
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
                                globs.log.err('ERROR: [{}] section, \'{}\' option: invalid field name: \'{}\'. Must use a valid field name for this.'.format(sectionList[i][0], optName, oList[j][0]))
                                globs.log.write(1,'ERROR: [{}] section, \'{}\' option: invalid field name: \'{}\'. Must use a valid field name for this.'.format(sectionList[i][0], optName, oList[j][0]))
                                anyProblems += 1
                            if oList[j][1] not in ['ascending', 'descending']:
                                globs.log.err('ERROR: [{}] section, \'{}\' option, \'{}\' field: invalid sort order: \'{}\'. Must be \'ascending\' or \'descending\'.'.format(sectionList[i][0], optName, oList[j][0], oList[j][1]))
                                globs.log.write(1,'ERROR: [{}] section, \'{}\' option, \'{}\' field: invalid sort order: \'{}\'. Must be \'ascending\' or \'descending\'.'.format(sectionList[i][0], optName, oList[j][0], oList[j][1]))
                                anyProblems += 1
                    # Something else (weird) is happening
                    else:
                        if not self.isValidReportField(optName):
                            globs.log.write(1,'ERROR: [{}] section: invalid option: \'{}\'.'.format(sectionList[i][0], optName))
                            globs.log.err('ERROR: [{}] section: invalid option: \'{}\'.'.format(sectionList[i][0], optName))
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
        sqlStmt = "SELECT source, destination, lastTimestamp, lastFileCount, lastFileSize, dupversion FROM backupsets ORDER BY source, destination"

        # Loop through backupsets table and then get latest activity for each src/dest pair
        dbCursor = globs.db.execSqlStmt(sqlStmt)
        bkSetRows = dbCursor.fetchall()
        globs.log.write(2, 'bkSetRows=[{}]'.format(bkSetRows))
        for source, destination, lastTimestamp, lastFileCount, lastFileSize, lastdupversion in bkSetRows:
            globs.log.write(3, 'Src=[{}] Dest=[{}] lastTimestamp=[{}] lastFileCount=[{}] lastFileSize=[{}]  dupversion=[{}]'.format(source, 
                destination, lastTimestamp, lastFileCount, lastFileSize, lastdupversion))

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
                        lasttimestamp=\'{}\', dupversion=\'{}\' WHERE source=\'{}\' AND destination=\'{}\''.format(examinedFiles, sizeOfExaminedFiles, \
                        endTimeStamp, dupversion, source, destination)
                    globs.db.execSqlStmt(sqlStmt)
                    globs.db.dbCommit()

                    # Set last file count & size the latest information
                    lastFileCount = examinedFiles
                    lastFileSize = sizeOfExaminedFiles

        return None

    def createReport(self, reportStructure, startTime):

        reportOutput = {}
        reportOutput['sections'] = []

        # Loop through report configurations
        for reportSection in reportStructure['sections']:
            if reportSection['type'] == 'report':
                if 'groupby' in reportSection['options']:
                    reportOutput['sections'].append(self.buildReportOutputYesGroups(reportSection))
                else:
                    reportOutput['sections'].append(self.buildReportOutputNoGroups(reportSection))
            elif reportSection['type'] == 'noactivity':
                reportOutput['sections'].append(self.buildNoActivityOutput(reportSection))
            elif reportSection['type'] == 'lastseen':
                reportOutput['sections'].append(self.buildLastSeenOutput(reportSection))
            elif reportSection['type'] == 'lastseen':
                reportOutput['sections'].append(self.buildLastSeenOutput(reportSection))
            elif reportSection['type'] == 'runtime':
                reportOutput['sections'].append(self.buildRuntimeOutput(reportSection, startTime))
        
        return reportOutput

    # Manage the formattedReport dictionary in the class
    # Basically, if a report in a given format has already been generated, just return it. 
    # Otherwise, generate it, store it, and return it.
    def createFormattedOutput(self, reportOutput, type):
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

        runTime = time.time() - startTime

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
        singleReport['dataRows'][0].append(['Running Time: {:.3f} seconds.'.format(runTime), '#FFFFFF', toMarkup()])

        return singleReport

    # Crate a report that doesn't have any groups (groupby = None)
    # Take data from report table and build the resulting report structure.
    # Output structure will be used to generate the final report
    # 'reportStructure' is the report options as extracted from the .rc file
    # See docs/DataStructures/ConfigFormat for schema of reportStructure
    # See docs/DataStructures/ReportFormat for schema of reportOutput
    def buildReportOutputNoGroups(self, reportStructure):

        # singleReport is the output for just this specific report. 
        # It will be appended to reportOutput once it is filled in.
        # This is how we produce multiple reports from the same run.
        singleReport = {}

        # Copy basic report information from the report definition
        singleReport['name'] = reportStructure['name']
        singleReport['columnCount'] = len(reportStructure['options']['columns'])
        singleReport['columnNames'] = []
        
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
                
                # Figure out the appropriate background. backgrounds. We'll need this in a couple of places
                # Default color is white (#FFFFFF)
                bground = '#FFFFFF'
                if (reportStructure['options']['columns'][i][0] in ['messages', 'warnings', 'errors', 'logdata']) and (rowList[singleRow][i] != ''):
                    msgType = reportStructure['options']['columns'][i][0]
                    if msgType == 'messages':
                        bground = reportStructure['options']['jobmessagebg']
                    elif msgType == 'warnings':
                        bground = reportStructure['options']['jobwarningbg']
                    elif msgType == 'errors':
                        bground = reportStructure['options']['joberrorbg']
                    elif msgType == 'logdata':
                        bground = reportStructure['options']['joblogdatabg']
                
                # See if we need to substitute date, time, or duration fields
                # All are stored as timestamp data, so they need to be converted to actual dates & times
                if reportStructure['options']['columns'][i][0] == 'date':
                    markup = toMarkup(align=fldDefs['date'][0])
                    dateStr, timeStr = drdatetime.fromTimestamp(rowList[singleRow][i], dfmt=globs.opts['dateformat'], tfmt=globs.opts['timeformat'])
                    newStr = '{:{fmt}}'.format(dateStr, fmt=fldDefs['date'][2])
                    singleReport['dataRows'][dataRowIndex].append([newStr, bground, markup])
                elif reportStructure['options']['columns'][i][0] == 'time':
                    markup = toMarkup(align=fldDefs['time'][0])
                    dateStr, timeStr = drdatetime.fromTimestamp(rowList[singleRow][i], dfmt=globs.opts['dateformat'], tfmt=globs.opts['timeformat'])
                    newStr = '{:{fmt}}'.format(timeStr, fmt=fldDefs['time'][2])
                    singleReport['dataRows'][dataRowIndex].append([newStr, bground, markup])
                elif reportStructure['options']['columns'][i][0] == 'duration':
                    markup = toMarkup(align=fldDefs['duration'][0])
                    tDiff = drdatetime.timeDiff(rowList[singleRow][i], reportStructure['options']['durationzeroes'])
                    newStr = '{:{fmt}}'.format(tDiff, fmt=fldDefs['duration'][2])
                    singleReport['dataRows'][dataRowIndex].append([newStr, bground, markup])
                elif ((reportStructure['options']['columns'][i][0] in ['messages', 'warnings', 'errors', 'logdata']) and (reportStructure['options']['weminline'] is False)):
                    # For these rows, each will go on a separate line, so put them in their own list for now.
                    # If weminline == True, we would treat them line any other row
                    if rowList[singleRow][i] != '': # Not empty. Let's see what kind of message it is. Then see if we want to display those (as per the .rc file options) and what the backgound color is
                        msgType = reportStructure['options']['columns'][i][0]
                        if msgType == 'messages':
                            if reportStructure['options']['displaymessages'] == False:
                                continue
                        elif msgType == 'warnings':
                            if reportStructure['options']['displaywarnings'] == False:
                                continue
                        elif msgType == 'errors':
                            if reportStructure['options']['displayerrors'] == False:
                                continue
                        elif msgType == 'logdata':
                            if reportStructure['options']['displaylogdata'] == False:
                                continue
                        
                        # Are we truncating error messages?    
                        truncatedMsg = truncateWarnErrMsgs(msgType, rowList[singleRow][i], reportStructure['options'])
                        markup = toMarkup(align=fldDefs[msgType][0])
                        # Error message lines get a [message, bground, markup, ColTitle] list assigned to it.
                        # Do all that stuff and add it to msgList for now.
                        msgList[reportStructure['options']['columns'][i][0]] = [truncatedMsg, bground, markup, reportStructure['options']['columns'][i][1]]
                # See if the field is one of the numeric fields. Need to ass commas, right justify, & possibly reduce scale (mb/gb)
                elif reportStructure['options']['columns'][i][0] in ['examinedFiles', 'examinedFilesDelta', 'sizeOfExaminedFiles', 'fileSizeDelta', 'addedFiles', 'deletedFiles', 'modifiedFiles', 'filesWithError']:
                    if reportStructure['options']['columns'][i][0] in ['sizeOfExaminedFiles', 'fileSizeDelta'] and reportStructure['options']['sizedisplay'] != 'none': # Translate to 'mb' or 'gb'
                        val = rowList[singleRow][i]
                        if reportStructure['options']['sizedisplay'][:2].lower() == 'mb':
                            val = val / 1000000.00
                        else:
                            val = val / 1000000000.00
                        rowList[singleRow] = self.updateTuple(rowList[singleRow], i, val)  # Can't directly update a tuple, so need to perform some Python-Fu
                    markup = toMarkup(align='right')
                    newStr = '{:{fmt}}'.format(rowList[singleRow][i], fmt=fldDefs[reportStructure['options']['columns'][i][0]][2])
                    singleReport['dataRows'][dataRowIndex].append([newStr, bground, markup])
                else:  # After all that checking, this is just a plain-old data field :-(
                    # See if we need to truncate WEM messages
                    msg = rowList[singleRow][i]
                    msgType = reportStructure['options']['columns'][i][0]
                    if reportStructure['options']['columns'][i][0] in ['messages', 'warnings', 'errors', 'logdata']:
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
            singleReport['dataRows'][dataRowIndex].append([dataRowTypes['data'], singleReport['inlineColumnCount']])
            singleReport['dataRows'][dataRowIndex].append(['No Activity', '#FFFFFF', toMarkup(italic=True)])

        return singleReport

    # Crate a report that doesn't have any groups (groupby = None)
    # Take data from report table and build the resulting report structure.
    # Output structure will be used to generate the final report
    # 'reportStructure' is the report options as extracted from the .rc file
    # See docs/DataStructures/ConfigFormat for schema of reportStructure
    # See docs/DataStructures/ReportFormat for schema of reportOutput
    def buildReportOutputYesGroups(self, reportStructure):

        # singleReport is the output for just this specific report. 
        # It will be appended to reportOutput once it is filled in.
        # This is how we produce multiple reports from the same run.
        singleReport = {}

        # Copy basic report information from the report definition
        singleReport['name'] = reportStructure['name']
        singleReport['columnCount'] = len(reportStructure['options']['columns'])
        singleReport['columnNames'] = []
        
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

        # If we're not repeating column titles, print titles once at the top of the report
        if reportStructure['options']['repeatcolumntitles'] == False and reportStructure['options']['suppresscolumntitles'] == False:
            # Add column headings
            # Column headings (or 'titles' - the usage varies throughout the code) get a starting list of ['rowHeadDataType',1] (because each title spans 1 column in the report)
            # Then a series of ['columTitle', bgcolor, markup] lists, one for each column
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

        
        sqlStmt = buildQuery(reportStructure['options'], groupby=True)
        dbCursor = globs.db.execSqlStmt(sqlStmt)
        groupList = dbCursor.fetchall()

        # Loop through the defined sections and create a new section for each group
        for groupName in groupList:

            # Build the subheading (title) for the group
            if 'groupheading' in reportStructure['options']:                 # Group heading already defined
                grpHeading = reportStructure['options']['groupheading']
            else:                                                   # Group heading not defined. Build it from 'groupby' columns
                grpHeading = ''
                for i in range(len(groupName)):
                    grpHeading += str(groupName[i]) + ' '
                #singleReport['groups'][groupIndex]['groupHeading'] = grpHeading

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

            # If we're repeating column titles, print titles at the top of each group
            if reportStructure['options']['repeatcolumntitles'] == True and reportStructure['options']['suppresscolumntitles'] == False:
                # Add column headings
                # Column headings (or 'titles' - the usage varies throughout the code) get a starting list of ['rowHeadDataType',1] (because each title spans 1 column in the report)
                # Then a series of ['columTitle', bgcolor, markup] lists, one for each column
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
                
                    # Figure out the appropriate background. backgrounds. We'll need this in a couple of places
                    # Default color is white (#FFFFFF)
                    bground = '#FFFFFF'
                    if (reportStructure['options']['columns'][i][0] in ['messages', 'warnings', 'errors', 'logdata']) and (rowList[singleRow][i] != ''):
                        msgType = reportStructure['options']['columns'][i][0]
                        if msgType == 'messages':
                            bground = reportStructure['options']['jobmessagebg']
                        elif msgType == 'warnings':
                            bground = reportStructure['options']['jobwarningbg']
                        elif msgType == 'errors':
                            bground = reportStructure['options']['joberrorbg']
                        elif msgType == 'logdata':
                            bground = reportStructure['options']['joblogdatabg']

                    # See if we need to substitute date, time, or duration fields
                    # All are stored as timestamp data, so they need to be converted to actual dates & times
                    if reportStructure['options']['columns'][i][0] == 'date':
                        markup = toMarkup(align=fldDefs['date'][0])
                        dateStr, timeStr = drdatetime.fromTimestamp(rowList[singleRow][i], dfmt=globs.opts['dateformat'], tfmt=globs.opts['timeformat'])
                        newStr = '{:{fmt}}'.format(dateStr, fmt=fldDefs['date'][2])
                        singleReport['dataRows'][dataRowIndex].append([newStr, bground, markup])
                    elif reportStructure['options']['columns'][i][0] == 'time':
                        markup = toMarkup(align=fldDefs['time'][0])
                        dateStr, timeStr = drdatetime.fromTimestamp(rowList[singleRow][i], dfmt=globs.opts['dateformat'], tfmt=globs.opts['timeformat'])
                        newStr = '{:{fmt}}'.format(timeStr, fmt=fldDefs['time'][2])
                        singleReport['dataRows'][dataRowIndex].append([newStr, bground, markup])
                    elif reportStructure['options']['columns'][i][0] == 'duration':
                        markup = toMarkup(align=fldDefs['duration'][0])
                        tDiff = drdatetime.timeDiff(rowList[singleRow][i], reportStructure['options']['durationzeroes'])
                        newStr = '{:{fmt}}'.format(tDiff, fmt=fldDefs['duration'][2])
                        singleReport['dataRows'][dataRowIndex].append([newStr, bground, markup])
                    elif ((reportStructure['options']['columns'][i][0] in ['messages', 'warnings', 'errors', 'logdata']) and (reportStructure['options']['weminline'] is False)):
                        # For these rows, each will go on a separate line, so put them in their own list for now.
                        # If weminline == True, we would treat them line any other row
                        if rowList[singleRow][i] != '': # Not empty. Let's see what kind of message it is. Then see if we want to display those (as per the .rc file options) and what the backgound color is
                            msgType = reportStructure['options']['columns'][i][0]
                            if msgType == 'messages':
                                if reportStructure['options']['displaymessages'] == False:
                                    continue
                            elif msgType == 'warnings':
                                if reportStructure['options']['displaywarnings'] == False:
                                    continue
                            elif msgType == 'errors':
                                if reportStructure['options']['displayerrors'] == False:
                                    continue
                            elif msgType == 'logdata':
                                if reportStructure['options']['displaylogdata'] == False:
                                    continue
                        
                            # Ared we truncating error messages?    
                            truncatedMsg = truncateWarnErrMsgs(msgType, rowList[singleRow][i], reportStructure['options'])
                            markup = toMarkup(align=fldDefs[msgType][0])
                            # Error message lines get a [message, bground, markup, ColTitle] list assigned to it.
                            # Do all that stuff and add it to msgList for now.
                            msgList[reportStructure['options']['columns'][i][0]] = [truncatedMsg, bground, markup, reportStructure['options']['columns'][i][1]]
                    # See if the field is one of the numeric fields. Need to ass commas, right justify, & possibly reduce scale (mb/gb)
                    elif reportStructure['options']['columns'][i][0] in ['examinedFiles', 'examinedFilesDelta', 'sizeOfExaminedFiles', 'fileSizeDelta', 'addedFiles', 'deletedFiles', 'modifiedFiles', 'filesWithError']:
                        if reportStructure['options']['columns'][i][0] in ['sizeOfExaminedFiles', 'fileSizeDelta'] and reportStructure['options']['sizedisplay'] != 'none': # Translate to 'mb' or 'gb'
                            val = rowList[singleRow][i]
                            if reportStructure['options']['sizedisplay'][:2].lower() == 'mb':
                                val = val / 1000000.00
                            else:
                                val = val / 1000000000.00
                            rowList[singleRow] = self.updateTuple(rowList[singleRow], i, val)  # Can't directly update a tuple, so need to perform some Python-Fu
                        markup = toMarkup(align='right')
                        newStr = '{:{fmt}}'.format(rowList[singleRow][i], fmt=fldDefs[reportStructure['options']['columns'][i][0]][2])
                        singleReport['dataRows'][dataRowIndex].append([newStr, bground, markup])
                    else:  # After all that checking, this is just a plain-old data field :-(
                        # See if we need to truncate WEM messages
                        msg = rowList[singleRow][i]
                        msgType = reportStructure['options']['columns'][i][0]
                        if reportStructure['options']['columns'][i][0] in ['messages', 'warnings', 'errors', 'logdata']:
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
                if pastInterval is False:
                    globs.log.write(3, 'SrcDest=[{}] DaysDiff=[{}]. Skip reporting'.format(srcDest, diff))
                    singleReport['dataRows'][dataRowIndex].append(['{} days ago. Backup interval is {} days.'.format(diff, interval), bgColor, markupPlain])
                else:
                    lastDateStr, lastTimeStr = drdatetime.fromTimestamp(lastTimestamp)
                    singleReport['dataRows'][dataRowIndex].append(['Last activity on {} at {} ({} days ago)'.format(lastDateStr, lastTimeStr, diff), bgColor, markupItal])

    
        if dataRowIndex == -1:  # No rows in unseen table
            singleReport['dataRows'].append([])
            dataRowIndex += 1
            singleReport['dataRows'][dataRowIndex].append([dataRowTypes['data'], singleReport['inlineColumnCount']])
            singleReport['dataRows'][dataRowIndex].append(['No Activity', '#FFFFFF', toMarkup(italic=True)])

        return singleReport

    def buildLastSeenOutput(self, reportStructure):

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
        globs.log.write(3,'sourceDestList=[{}]'.format(sourceDestList))

        for source, destination, dupversion, lastTimestamp in sourceDestList:
            # If src/dest is known offline, skip
            srcDest = source + globs.opts['srcdestdelimiter'] + destination
            offline = globs.optionManager.getRcOption(srcDest, 'offline')
            if offline != None:  
                if offline.lower() in ('true'):
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
                globs.log.write(3, 'SrcDest=[{}] DaysDiff=[{}]. Skip reporting'.format(srcDest, diff))
                singleReport['dataRows'][dataRowIndex].append(['{} days ago. Backup interval is {} days.'.format(diff, interval), bgColor, markupPlain])
            else:
                lastDateStr, lastTimeStr = drdatetime.fromTimestamp(lastTimestamp)
                singleReport['dataRows'][dataRowIndex].append(['Last activity on {} at {} ({} days ago)'.format(lastDateStr, lastTimeStr, diff), bgColor, markupItal])

        return singleReport

    def createHtmlFormat(self, reportStructure, reportOutput):
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
                    msgHtml += '<tr><td align=\"{}\" colspan="{}" bgcolor="{}"><details><summary>{}</summary><p>{}{}{}</td></tr>\n'.format(align, colspan, reportSection['dataRows'][dataRowIndex][1][1], reportSection['dataRows'][dataRowIndex][1][3], start, reportSection['dataRows'][dataRowIndex][1][0], end)
                elif rowType == dataRowTypes['singleLine']:
                    start, end, align = fromMarkup(reportSection['dataRows'][dataRowIndex][1][2])
                    msgHtml += '<tr><td align=\"{}\" colspan="{}" bgcolor="{}">{}{}{}</td></tr>\n'.format(align, colspan, reportSection['dataRows'][dataRowIndex][1][1], start, reportSection['dataRows'][dataRowIndex][1][0], end)
                else:
                    pass    # Invalid data row descriptor

            msgHtml += '</table><br>'

        msgHtml += '<br>Report generated by <a href=\'https://github.com/HandyGuySoftware/dupReport\'>dupReport</a> Version {}.{}.{} ({})<br>'.format(globs.version[0], globs.version[1], globs.version[2], globs.status)
        msgHtml += '</body></html>\n'

        return msgHtml

    def createTextFormat(self, reportStructure, reportOutput):
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
                #elif rowType == dataRowTypes['grpHeading']:
                #    msgText += '{}\n'.format(reportSection['dataRows'][dataRowIndex][1][0])
                elif rowType in [dataRowTypes['rowHead'], dataRowTypes['data']]:
                    for column in range(1,len(reportSection['dataRows'][dataRowIndex])):
                        element = reportSection['dataRows'][dataRowIndex][column]
                        msgText += '{}'.format(element[0])
                    msgText += '\n'
                #elif rowType == dataRowTypes['wemData']:
                #    msgText += '{}\n'.format(reportSection['dataRows'][dataRowIndex][1][0])
                #elif rowType == dataRowTypes['singleLine']:
                #    msgText += '{}\n'.format(reportSection['dataRows'][dataRowIndex][1][0])
                else:
                    pass    # Invalid data row descriptor

            msgText += '\n'

        msgText += 'Report generated by dupReport (https://github.com/HandyGuySoftware/dupReport) Version {}.{}.{} ({})\n'.format(globs.version[0], globs.version[1], globs.version[2], globs.status)

        return msgText

    def createCsvFormat(self, reportStructure, reportOutput):
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
        return reportOutput

