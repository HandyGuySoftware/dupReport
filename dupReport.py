#!/usr/bin/env python3

#
# dupReport.py
#
# Print summary reports from Duplicati backup service # # Stephen Fried, October 2017 #

import os
import sys
import imaplib
import getpass
import email
import datetime
import sqlite3
import re
import time
import argparse
import poplib
import os.path
import smtplib
import configparser
from configparser import SafeConfigParser 
import email
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# Define version info
version=[2,0,2]     # Program Version
dbversion=[1,0,0]   # Required DB version
copyright='2017'

# Define global variables
options={}        # Parsed and read options from command line & .rc file
logFile = None    # Handle for log file
emailText=[]      # List of email text components
emailFormat=[]    # Corresponding list of emial components print formats
dbName='dupReport.db'
logName='dupReport.log'
rcName='dupReport.rc'

# Execute a Sqlite command and manage exceptions
def exec_sqlite(conn, stmt):
    curs = conn.cursor()

    try:
        curs.execute(stmt)
    except sqlite3.Error as err:
        sys.stderr.write('SQLite error: {}\n'.format(err.args[0]))
        write_log_entry(1, 'SQLite error: {}\n'.format(err.args[0]))
        sys.exit(1) # Abort program. Can't continue with DB error
    return curs


# Initialize database to empty, default tables
def db_initialize(conn):

    # Drop any tables that might already exist in the database
    exec_sqlite(conn,"drop table if exists version")
    exec_sqlite(conn,"drop table if exists emails")
    exec_sqlite(conn,"drop table if exists backupsets")
    exec_sqlite(conn,"drop index if exists emailindx")
    exec_sqlite(conn,"drop index if exists srcdestindx")
 
    # version table holds current database version.
    # Has no real purpose now, but will be useful if need to change database formats later
    exec_sqlite(conn,"create table version (desc varchar(20), major int, minor int, subminor int)")
    exec_sqlite(conn,"insert into version(desc, major, minor, subminor) values (\'database\',{},{},{})".format(dbversion[0], dbversion[1],dbversion[2]))

    # emails table holds information about all emails received
    sqlStmt = "create table emails (messageId varchar(50), sourceComp varchar(50), destComp varchar(50), \
        emailDate varchar(50), emailTime varchar(50), deletedFiles int, deletedFolders int, modifiedFiles int, \
        examinedFiles int, openedFiles int, addedFiles int, sizeOfModifiedFiles int, sizeOfAddedFiles int, sizeOfExaminedFiles int, \
        sizeOfOpenedFiles int, notProcessedFiles int, addedFolders int, tooLargeFiles int, filesWithError int, \
        modifiedFolders int, modifiedSymlinks int, addedSymlinks int, deletedSymlinks int, partialBackup varchar(30), \
        dryRun varchar(30), mainOperation varchar(30), parsedResult varchar(30), verboseOutput varchar(30), \
        verboseErrors varchar(30), endDate varchar(30), endTime varchar(30), beginDate varchar(30), beginTime varchar(30), \
        duration varchar(30), messages varchar(255), warnings varchar(255), errors varchar(255), failedMsg varchar(100))"
    exec_sqlite(conn,sqlStmt)
    exec_sqlite(conn,"create index emailindx on emails (messageId)")
    exec_sqlite(conn,"create index srcdestindx on emails (sourceComp, destComp)")

    # backup sets contains information on all source-destination pairs in the backups
    exec_sqlite(conn,"create table backupsets (source varchar(20), destination varchar(20), lastFileCount integer, lastFileSize integer, \
        lastDate varchar(50), lastTime varchar(50))")

    conn.commit()


def curr_db_version():
    # Get current database version in use
    dbConn = sqlite3.connect(options['dbpath'])
    dbCursor = exec_sqlite(dbConn, 'SELECT major, minor, subminor FROM  version WHERE desc = \'database\'')
    maj, min, subm = dbCursor.fetchone()

    if (maj == dbversion[0]) and (min == dbversion[1]) and (subm == dbversion[2]):
        res = True
    else:
        res = False

    return maj, min, subm, res

# Initialize RC file to default values
def rc_initialize(fname):
# See if RC file has all the parts needed before proceeding with the rest of the program
    rcParts= [
        ('main','dbpath',get_script_path()),
        ('main','logpath',get_script_path()),
        ('main','verbose','1'),
        ('main','logappend','false'),
        ('main','sizereduce','none'),
        ('main','subjectregex','^Duplicati Backup report for'),
        ('main','summarysubject','Duplicati Backup Summary Report'),
        ('main','srcregex','\w*'),
        ('main','destregex','\w*'),
        ('main','srcdestdelimiter','-'),
        ('main','border','1'),
        ('main','padding','5'),
        ('incoming','transport','imap'),
        ('incoming','server','localhost'),
        ('incoming','port','993'),
        ('incoming','encryption','tls'),
        ('incoming','account','someacct@hostmail.com'),
        ('incoming','password','********'),
        ('incoming','folder','INBOX'),
        ('outgoing','server','localhost'),
        ('outgoing','port','587'),
        ('outgoing','encryption','tls'),
        ('outgoing','account','someacct@hostmail.com'),
        ('outgoing','password','********'),
        ('outgoing','sender','sender@hostmail.com'),
        ('outgoing','receiver','receiver@hostmail.com'),
        ]

    rcParser = configparser.SafeConfigParser()
    rcParser.read(fname)

    # Flag to see if any RC parts have changed
    newRc=False

    for section, option, default in rcParts:
        if rcParser.has_section(section) == False:
            rcParser.add_section(section)
            newRc=True
        if rcParser.has_option(section, option) == False:
            rcParser.set(section, option, default)
            newRc=True

    # save updated RC configuration to a file
    with open(fname, 'w') as configfile:
        rcParser.write(configfile)
    return newRc


# Store command-line options
def parse_command_line():

    # Parse command line options with ArgParser library
    argParser = argparse.ArgumentParser(description='Process dupReport options.')
    argParser.add_argument("-r","--rcpath", help="Location of dupReport config directory.", action="store")
    argParser.add_argument("-d","--dbpath", help="Locatoin of dupReport database.", action="store")
    argParser.add_argument("-v", "--verbose", help="Log file verbosity. 0=none  1=verbose  2=Please make it stop!!! Same as [main]verbose= in rc file.", \
        type=int, action="store", choices=[0,1,2])
    argParser.add_argument("-V","--version", help="dupReport version and program info.", action="store_true")
    argParser.add_argument("-l","--logpath", help="Path to dupReport log file. (Default: 'dupReport.log'. Same as [main]logpath= in rc file.", action="store")
    argParser.add_argument("-a","--append", help="Append new logs to log file. Same as [main]logappend= in rc file.", action="store_true")
    argParser.add_argument("-m", "--mega", help="Convert file sizes to megabytes or gigabytes. Options are 'mega' 'giga' or 'none'. \
        Same as [main]sizereduce= in rc file.", action="store", choices=['mega','giga','none'])
    argParser.add_argument("-i", "--initdb", help="Initialize database.", action="store_true")

    opGroup = argParser.add_mutually_exclusive_group()
    opGroup.add_argument("-c", "--collect", help="Collect new emails only. (Don't run report)", action="store_true")
    opGroup.add_argument("-t", "--report", help="Run summary report only. (Don't collect emails)", action="store_true")

    args = argParser.parse_args()
    return args

# Read .rc file options
# Many command line options have .rc equivalents. 
# Command line options take precedence over .rc file options
def parse_config_file(rcPath, args):
    
    try:
        rcConfig = SafeConfigParser()
        rv=rcConfig.read(rcPath)
    except configparser.ParsingError as err:
        sys.stderr.write('RC Parse error: {}\n'.format(err.args[0]))
        sys.exit(1) # Abort program. Can't continue with RC error

    # OPTIMIZE - LOOP THIS
    try:
        options['dbpath'] = rcConfig.get('main','dbpath')
        options['logpath'] = rcConfig.get('main','logpath')
        options['verbose'] = rcConfig.getint('main','verbose')
        options['logappend'] = rcConfig.getboolean('main','logappend')
        options['sizereduce'] = rcConfig.get('main','sizereduce')
        options['subjectregex'] = rcConfig.get('main','subjectregex')
        options['srcregex'] = rcConfig.get('main','srcregex')
        options['destregex'] = rcConfig.get('main','destregex')
        options['srcdestdelimiter'] = rcConfig.get('main','srcdestdelimiter')
        options['summarysubject'] = rcConfig.get('main','summarysubject')
        options['border'] = rcConfig.get('main','border')
        options['padding'] = rcConfig.get('main','padding')

        options['intransport'] = rcConfig.get('incoming','transport')
        options['inserver'] = rcConfig.get('incoming','server')
        options['inport'] = rcConfig.get('incoming','port')
        options['inencryption'] = rcConfig.get('incoming','encryption')
        options['inaccount'] = rcConfig.get('incoming','account')
        options['inpassword'] = rcConfig.get('incoming','password')
        options['infolder'] = rcConfig.get('incoming','folder')

        options['outserver'] = rcConfig.get('outgoing','server')
        options['outport'] = rcConfig.get('outgoing','port')
        options['outencryption'] = rcConfig.get('outgoing','encryption')
        options['outaccount'] = rcConfig.get('outgoing','account')
        options['outpassword'] = rcConfig.get('outgoing','password')
        options['outsender'] = rcConfig.get('outgoing','sender')
        options['outreceiver'] = rcConfig.get('outgoing','receiver')
    except configparser.NoOptionError as err:
        sys.stderr.write('RC Parse error - No Option: {}\n'.format(err.args[0]))
        sys.exit(1) # Abort program. Can't continue with RC error
    except configparser.NoSectionError as err:
        sys.stderr.write('RC Parse error - No Section: {}\n'.format(err.args[0]))
        sys.exit(1) # Abort program. Can't continue with RC error

    # Now, overlay with command line options
    # Database Path
    if args.dbpath != None:  #dbPath specified on command line
        options['dbpath'] = '{}/{}'.format(args.dbpath, dbName) 
    elif options['dbpath'] == '':  # No command line & not specified in RC file
        options['dbpath'] = '{}/{}'.format(get_script_path(), dbName)
    else:  # Path specified in rc file. Add dbname for full path
        options['dbpath'] = '{}/{}'.format(options['dbpath'], dbName)

    # Log file path
    if args.logpath != None:  #logPath specified on command line
        options['logpath'] = '{}/{}'.format(args.logpath, logName)
    elif options['logpath'] == '':  # No command line & not specified in RC file
        options['logpath'] = '{}/{}'.format(get_script_path(), logName)
    else:  # Path specified in rc file. Add dbname for full path
        options['logpath'] = '{}/{}'.format(options['logpath'], logName)

    options['rcpath'] = rcPath

    if args.collect == True:
        options['collect'] = True
    if args.report == True:
        options['report'] = True
    if args.verbose != None:
        options['verbose'] = args.verbose
    if args.append == True:
        options['logappend'] = True
    if args.initdb == True:
        options['initdb'] = True
    if args.mega != None:
        options['sizereduce'] = args.mega

    return

def version_info():
    print('\n-----\ndupReport: A summary email report generator for Duplicati.')
    print('Program Version {}.{}.{}'.format(version[0], version[1], version[2]))
    
    maj, min, subm, res = curr_db_version()
    print('Database Version {}.{}.{}'.format(maj, min, subm))

    print('Copyright (c) {} Stephen Fried for HandyGuy Software'.format(copyright))
    print('Distributed under MIT License. See LICENSE file for details.\n-----\n')
    return

def get_script_path():
    return os.path.dirname(os.path.realpath(sys.argv[0]))

def search_message_part(part, mp, lines, typ, parts):
# Search for field in message
# part - section to search for
# mp - list of all message parts
# lines - 0=single line, 1=multi-line
# type - 0=int or 1=string
# parts - for text fields, the number of words expected in the line

    d=''
    m = re.compile(mp, lines).search(part)
    if m:
        if lines == 0:   # Single line result
            num=1
            while num <= parts:
                try:
                    d = d +  m.group().split()[num] + ' '
                    num += 1
                except IndexError:
                    break
        else:    # Multi-line result
            d = m.group()
            d = re.sub(re.compile(r'\s+'), ' ', d)
            d = re.sub(re.compile(r'\"'), '\'', d)
    else:  # Pattern not found
        if typ == 0:        # integer field
            d = '0'

    return d


# Check database for existing message ID
def db_search_message(messId):

    write_log_entry(2,'db_search_message({})\n'.format(messId))
    sqlStmt = "SELECT messageId FROM emails WHERE messageId=\'{}\'".format(messId)
    write_log_entry(2,'{}\n'.format(sqlStmt))
    dbCursor = exec_sqlite(dbConn,sqlStmt)
    idExists = dbCursor.fetchone()
    if idExists:
        write_log_entry(1,'Message [{}] already in email database\n'.format(messId))
        return True
    return False

# Check database for existing source/destination pair
# Insert if it doesn't exist
def db_search_srcdest_pair(src, dest):
    write_log_entry(2, 'db_search_srcdest_pair({}, {})\n'.format(src, dest))
    sqlStmt = "SELECT source, destination FROM backupsets WHERE source=\'{}\' AND destination=\'{}\'".format(src, dest)
    write_log_entry(2, '{}\n'.format(sqlStmt))
    dbCursor = exec_sqlite(dbConn, sqlStmt)
    idExists = dbCursor.fetchone()
    if idExists:
        write_log_entry(2, "Source/Destination pair [{}/{}] already in database".format(src, dest))
        return True

    sqlStmt = "INSERT INTO backupsets (source, destination, lastFileCount, lastFileSize, lastDate, lastTime) \
        VALUES ('{}', '{}', 0, 0, \'2000-01-01\', \'00:00:00\')".format(src, dest)
    write_log_entry(2, '{}\n'.format(sqlStmt))
    exec_sqlite(dbConn, sqlStmt)
    dbConn.commit()
    write_log_entry(2, "Pair [{}/{}] added to database".format(src, dest))

    return False


def convert_date_time(dtString):
    # Convert dates & times to normlalized forms. Input=[YYYY/MM/DD  HH:MM:SS]
    write_log_entry(2, 'convert_date_time: dtString=[{}]\n'.format(dtString))
    if dtString == '':
        return None

    datePart = re.split('/', dtString.split(' ')[0])
    endDate = "{:04d}/{:02d}/{:02d}".format(int(datePart[2]),int(datePart[0]),int(datePart[1]))

    timePart = re.split(':', dtString.split(' ')[1])
    if dtString.split(' ')[2] == "PM":  # Use 24-hour clock
        timePart[0] = int(timePart[0]) + 12
    endTime = "{:02d}:{:02d}:{:02d}".format(int(timePart[0]),int(timePart[1]),int(timePart[2]))

    write_log_entry(2, 'Convert_Date_Time: Converted date=[{}]  Time=[]\n'.format(endDate, endTime))

    return (endDate, endTime)

# Build SQL statement to put into the emails table
def build_email_sql_statement(mParts, sParts, dParts):

    write_log_entry(2, 'build_email_sql_statement(): messageId={}  sourceComp={}  destComp={}'.format(mParts['messageId'],mParts['sourceComp'],mParts['destComp']))

    sqlStmt = "INSERT INTO emails(messageId, sourceComp, destComp, emailDate, emailTime, \
        deletedFiles, deletedFolders, modifiedFiles, examinedFiles, \
        openedFiles, addedFiles, sizeOfModifiedFiles, sizeOfAddedFiles, sizeOfExaminedFiles, \
        sizeOfOpenedFiles, notProcessedFiles, addedFolders, tooLargeFiles, filesWithError, \
        modifiedFolders, modifiedSymlinks, addedSymlinks, deletedSymlinks, partialBackup, \
        dryRun, mainOperation, parsedResult, verboseOutput, verboseErrors, endDate, endTime, \
        beginDate, beginTime, duration, messages, warnings, errors) \
        VALUES \
        ('{}', '{}', '{}', '{}', '{}', {}, {}, {}, {}, {}, {}, {}, {},{},{},{},{},{},{},{},{},{},{}, \
        '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', \"{}\", \"{}\", \"{}\")".format(mParts['messageId'], \
        mParts['sourceComp'], mParts['destComp'], mParts['emailDate'], mParts['emailTime'], sParts['deletedFiles'], \
        sParts['deletedFolders'], sParts['modifiedFiles'], sParts['examinedFiles'], sParts['openedFiles'], \
        sParts['addedFiles'], sParts['sizeOfModifiedFiles'], sParts['sizeOfAddedFiles'], sParts['sizeOfExaminedFiles'], sParts['sizeOfOpenedFiles'], \
        sParts['notProcessedFiles'], sParts['addedFolders'], sParts['tooLargeFiles'], sParts['filesWithError'], \
        sParts['modifiedFolders'], sParts['modifiedSymlinks'], sParts['addedSymlinks'], sParts['deletedSymlinks'], \
        sParts['partialBackup'], sParts['dryRun'], sParts['mainOperation'], sParts['parsedResult'], sParts['verboseOutput'], \
        sParts['verboseErrors'], dParts['endSaveDate'], dParts['endSaveTime'], dParts['beginSaveDate'], dParts['beginSaveTime'], \
        sParts['duration'], sParts['messages'], sParts['warnings'], sParts['errors'])
                
    write_log_entry(2, 'sqlStmt=[{}]\n'.format(sqlStmt))
    return sqlStmt

# Split downloaded message into constituent parts
def process_message(mess):

    write_log_entry(2,'process_message(): mess=[{}]'.format(mess))
    
    #Define lineParts
    #lineParts[] are the individual line items in the Duplicati status email report.
    #1 - internal variable name
    #2 - Duplicati name from email and regex to find it
    #3 - regex flags. 0=none.
    #4 - field Type (0=INT or 1=STR)
    #5 - Number of space-separated segments in that line
    lineParts = [
        ('deletedFiles','DeletedFiles: \d+', 0, 0, 1),
        ('deletedFolders', 'DeletedFolders: \d+', 0, 0, 1),
        ('modifiedFiles', 'ModifiedFiles: \d+', 0, 0, 1),
        ('examinedFiles', 'ExaminedFiles: \d+', 0, 0, 1),
        ('openedFiles', 'OpenedFiles: \d+', 0, 0, 1),
        ('addedFiles', 'AddedFiles: \d+', 0, 0, 1),
        ('sizeOfModifiedFiles', 'SizeOfModifiedFiles: \d+', 0, 0, 1),
        ('sizeOfAddedFiles', 'SizeOfAddedFiles: \d+', 0, 0, 1),
        ('sizeOfExaminedFiles', 'SizeOfExaminedFiles: \d+', 0, 0, 1),
        ('sizeOfOpenedFiles', 'SizeOfOpenedFiles: \d+', 0, 0, 1),
        ('notProcessedFiles', 'NotProcessedFiles: \d+', 0, 0, 1),
        ('addedFolders', 'AddedFolders: \d+', 0, 0, 1),
        ('tooLargeFiles', 'TooLargeFiles: \d+', 0, 0, 1),
        ('filesWithError', 'FilesWithError: \d+', 0, 0, 1),
        ('modifiedFolders', 'ModifiedFolders: \d+', 0, 0, 1),
        ('modifiedSymlinks', 'ModifiedSymlinks: \d+', 0, 0, 1),
        ('addedSymlinks', 'AddedSymlinks: \d+', 0, 0, 1),
        ('deletedSymlinks', 'DeletedSymlinks: \d+', 0, 0, 1),
        ('partialBackup', 'PartialBackup: \w+', 0, 1, 1),
        ('dryRun', 'Dryrun: \w+', 0, 1, 1),
        ('mainOperation', 'MainOperation: \w+', 0, 1, 1),
        ('parsedResult', 'ParsedResult: \w+', 0, 1, 1),
        ('verboseOutput', 'VerboseOutput: \w+', 0, 1, 1),
        ('verboseErrors', 'VerboseErrors: \w+', 0, 1, 1),
        ('endTimeStr', 'EndTime: .*', 0, 1, 3),
        ('beginTimeStr', 'BeginTime: .*', 0, 1, 3),
        ('duration', 'Duration: .*', 0, 1, 1),
        ('messages', 'Messages: \[.*^\]', re.MULTILINE|re.DOTALL, 1, 0),
        ('warnings', 'Warnings: \[.*^\]', re.MULTILINE|re.DOTALL, 1, 0),
        ('errors', 'Errors: \[.*^\]', re.MULTILINE|re.DOTALL, 1, 0),
        ('failed', 'Failed: .*', 0, 1, 100),
        ]


    # msgParts items:
    #    'messageID' - the message ID
    #    'subject' - the message subject
    #    'date'
    #    'time'
    #    'body' - Payload of message (i.e., not the Header)
    msgParts = {}

    # statusParts contains the individual lines from the Duplicati status emails
    statusParts = {}

    # dateParts contains the date & time strings for the SQL Query
    dateParts = {}

    # Get Message ID
    decode =  email.header.decode_header(mess['Message-Id'])[0]
    write_log_entry(2, 'decode=[{}]\n'.format(decode))
    msgParts['messageId'] = decode[0]
    write_log_entry(2, 'messageId=[{}]\n'.format(msgParts['messageId']))

    # See if the record is already in the database, meaning we've seen it before
    if db_search_message(msgParts['messageId']):
        return 1

    # Message not yet in database. Proceed
    write_log_entry(1, 'Message ID [{}] does not exist. Adding to DB\n'.format(msgParts['messageId']))

    decode = email.header.decode_header(mess['Subject'])[0]
    msgParts['subject'] = decode[0]
    write_log_entry(1, 'Subject=[{}].\n'.format(msgParts['subject']))

    date_tuple = email.utils.parsedate_tz(mess['Date'])
    if date_tuple:
        local_date = datetime.datetime.fromtimestamp(email.utils.mktime_tz(date_tuple))
        msgParts['emailDate'] = local_date.strftime("%Y-%m-%d")
        msgParts['emailTime'] = local_date.strftime("%H:%M:%S")

    # See if it's a message of interest
    # Match subjetc field against 'subjectregex' parameter from RC file (Default: 'Duplicati Backup report for...'
    if re.search(options['subjectregex'], msgParts['subject']) == None:
        write_log_entry(1, 'Message [{}] is not a Message of Interest\n'.format(msgParts['messageId']))
        return 1    # Not a message of Interest

    # Get source & desination computers from email subject
    srcRegex = '{}{}'.format(options['srcregex'], re.escape(options['srcdestdelimiter']))
    destRegex = '{}{}'.format(re.escape(options['srcdestdelimiter']), options['destregex'])
    write_log_entry(2,'srcregex=[{}]  destRegex=[{}]\n'.format(srcRegex, destRegex))

    partsSrc = re.search(srcRegex, msgParts['subject'])
    partsDest = re.search(destRegex, msgParts['subject'])
    if (partsSrc is None) or (partsDest is None):    # Correct subject but delim not found. Something is wrong.
        write_log_entry(2,'srcdestdelimiter [{}] not found in subject. Abandoning message.\n'.format(options['srcdestdelimiter']))
        return 1
        
    msgParts['sourceComp'] = re.search(srcRegex, msgParts['subject']).group().split(options['srcdestdelimiter'])[0]
    msgParts['destComp'] = re.search(destRegex, msgParts['subject']).group().split(options['srcdestdelimiter'])[1]
    write_log_entry(2, 'source=[{}] dest=[{}] Date=[{}]  Time=[{}] Subject=[{}]\n'.format(msgParts['sourceComp'], \
        msgParts['destComp'], msgParts['emailDate'], msgParts['emailTime'], msgParts['subject']))

    # Search for source/destination pair in database. Add if not already there
    db_search_srcdest_pair(msgParts['sourceComp'], msgParts['destComp'])    

    # Extract the body (payload) from the email
    msgParts['body'] = mess.get_payload()
    write_log_entry(2, 'Body=[{}]\n'.format(msgParts['body']))

    # Go through each element in lineParts{}, get the value from the body, and assign it to the corresponding element in statusParts{}
    for section,regex,flag,typ,parts in lineParts:
        statusParts[section] = search_message_part(msgParts['body'], regex, flag, typ, parts) # Get the field dats

    # Adjust fields if not a clean run
    write_log_entry(2, "statusParts['failed']=[{}]\n".format(statusParts['failed']))
    if statusParts['failed'] == '':
        # Convert dates & times to normlalized forms - YYYY/MM/DD  HH:MM:SS
        dateParts['endSaveDate'] = convert_date_time(statusParts['endTimeStr'])[0]
        dateParts['endSaveTime'] = convert_date_time(statusParts['endTimeStr'])[1]

        dateParts['beginSaveDate'] = convert_date_time(statusParts['beginTimeStr'])[0]
        dateParts['beginSaveTime'] = convert_date_time(statusParts['beginTimeStr'])[1]
    else:
        statusParts['errors'] = statusParts['failed']
        statusParts['parsedResult'] = 'Failure'
        dateParts['endSaveDate'] = ''
        dateParts['endSaveTime'] = ''
        dateParts['beginSaveDate'] = ''
        dateParts['beginSaveTime'] = ''

    if statusParts['messages'] != '':
        statusParts['messages'] = statusParts['messages'].replace(',','\n')
    if statusParts['warnings'] != '':
        statusParts['warnings'] = statusParts['warnings'].replace(',','\n')
    if statusParts['errors'] != '':
        statusParts['errors'] = statusParts['errors'].replace(',','\n')


    write_log_entry(2, 'endSaveDate=[{}] endSaveTime=[{}] beginSaveDate=[{}] beginSaveTime=[{}]\n'.format(dateParts['endSaveDate'], \
        dateParts['endSaveTime'], dateParts['beginSaveDate'], dateParts['beginSaveTime']))

    sqlStmt = build_email_sql_statement(msgParts, statusParts, dateParts)

    dbCursor.execute(sqlStmt)
    dbConn.commit()

    return msgParts

# Build list of text strings for sending final email
def create_email_text(txtTup,fmtTup):
    write_log_entry(2, 'create_email_text(): textTup={}  fmtTup={}'.format(txtTup,fmtTup))

    # Append text and formats tuples to email & format lists
    emailText.append(txtTup)
    emailFormat.append(fmtTup)

# Send final email result
def send_email():
    write_log_entry(2, 'Send_email()\n')
    msgText=''

    # Begin HTML output
    msgHtml='<html><head></head><body><table border={} cellpadding="{}">'.format(options['border'], options['padding'])

    # Loop through all text & format entries & build message as we go
    for txt,format in zip(emailText, emailFormat):
        write_log_entry(2, 'txt={}  format={}\n'.format(txt, format))
        msgHtml = msgHtml + '<tr>'  # New table row
        if len(txt) == 1:  # Single line of data = header. Center & bold
            msgText = msgText + '{}\n'.format(txt[0])
            msgHtml = msgHtml + '<td align="center" colspan = "11"><b>{}</b></td>'.format(txt[0])
        elif len(txt) == 2:  # Single line of data but != header. Center & italic
            msgText = '{}{}\n'.format(msgText, txt[0])
            msgHtml = '{}<td align="center" colspan = "11"><i>{}{}</i></td>'.format(msgHtml, txt[0], txt[1])
        else:
            for txt2,format2 in zip(txt,format):
                write_log_entry(2, 'txt2={}  fmt2={}\n'.format(txt2,format2))
                msgText = msgText + '{:{fmt}}'.format(txt2,fmt=format2)
                msgHtml = msgHtml + '<td align="right">{:{fmt}}</td>'.format(txt2,fmt=format2)
        msgText = msgText + '\n'
        msgHtml = msgHtml + '</tr>\n'
    msgHtml = msgHtml + '</table>\n'
    write_log_entry(2, 'msgtext={}\n'.format(msgText))
    write_log_entry(2, 'msgHtml={}\n'.format(msgHtml))

    # Build email message
    msg = MIMEMultipart('alternative')
    msg['Subject'] = options['summarysubject']
    msg['From'] = options['outsender']
    msg['To'] = options['outreceiver']

    # Record the MIME types of both parts - text/plain and text/html.
    part1 = MIMEText(msgText, 'plain')
    part2 = MIMEText(msgHtml, 'html')

    # Attach parts into message container.
    # According to RFC 2046, the last part of a multipart message, in this case
    # the HTML message, is best and preferred.
    msg.attach(part1)
    msg.attach(part2)

    # Send the message via local SMTP server.
    server = smtplib.SMTP('{}:{}'.format(options['outserver'], options['outport']))
    write_log_entry(2, 'Server=[{}]'.format(server))
    if options['outencryption'] == 'tls':   # Do we need to use SSL/TLS?
        server.starttls()
    server.login(options['outaccount'], options['outpassword'])
    server.sendmail(options['outsender'], options['outreceiver'], msg.as_string())
    server.quit() 
    

# Create summary report to email
# Creates tuples of fields and formats
# Add those tuples to final email through create_email_text()
def create_summary_report():

    sqlStmt = "SELECT source, destination, lastDate,lastTime,lastFileCount,lastFileSize from backupsets order by source, destination"
    write_log_entry(2, 'create_summary_report(): {}\n'.format(sqlStmt))

    tupFields = (options['summarysubject']+'\n',)
    tupFormats = ('^',)
    create_email_text(tupFields, tupFormats)

    if options['sizereduce'] == 'mega':   # Convert sizes to megabytes
        tupFields = ('Date','Time','Files','+/-','Size (MB)','+/- (MB)','Added','Deleted','Modified','Errors','Result')
    elif options['sizereduce'] == 'giga': # Convert sizes to gigabytes
        tupFields = ('Date','Time','Files','+/-','Size (GB)','+/- (GB)','Added','Deleted','Modified','Errors','Result')
    else:   # Report normal sizes
        tupFields = ('Date','Time','Files','+/-','Size','+/-','Added','Deleted','Modified','Errors','Result')
 
    tupFormats = ('11','9','>10','10','>18','18','>10','>10','>10','>10','<11')   # string formats for fields
    create_email_text(tupFields, tupFormats)

    # Loop through backupsets table and then get latest actibity for each src/dest pair
    dbCursor = exec_sqlite(dbConn, sqlStmt)
    bkSetRows = dbCursor.fetchall()
    write_log_entry(2, 'bkSetRows=[{}]\n'.format(bkSetRows))
    for source, destination, lastDate, lastTime, lastFileCount, lastFileSize in bkSetRows:
        write_log_entry(2, 'Src=[{}] Dest=[{}] lastDate=[{}] lastTime=[{}] lastFileCount=[{}] lastFileSize=[{}]\n'.format(source, 
            destination, lastDate, lastTime, lastFileCount, lastFileSize))
        tupFields = ('***** {} to {} *****'.format(source, destination),)
        tupFormats = ('',)
        create_email_text(tupFields, tupFormats)

        # Select all activity for src/dest pair since last report run
        sqlStmt = 'SELECT endDate, endtime, examinedFiles, sizeOfExaminedFiles, addedFiles, deletedFiles, modifiedFiles, \
            filesWithError, parsedResult, warnings, errors FROM emails WHERE sourceComp=\'{}\' AND destComp=\'{}\' \
            AND  ((endDate > \'{}\') OR  ((endDate == \'{}\') AND (endtime > \'{}\'))) order by endDate, endTime'.format(source, \
            destination, lastDate, lastDate, lastTime)
        write_log_entry(2, '{}\n'.format(sqlStmt))

        dbCursor = exec_sqlite(dbConn, sqlStmt)
        emailRows = dbCursor.fetchall()
        write_log_entry(2, 'emailRows=[{}]\n'.format(emailRows))
        if not emailRows: #NO rows found = no recent activity
            # Calculate days since last activity
            now = str(datetime.datetime.now()).split(' ')[0].split('-')
            then = lastDate.split('/')
            d0 = datetime.date(int(then[0]),int(then[1]), int(then[2]))
            d1 = datetime.date(int(now[0]),int(now[1]), int(now[2]))
            tupFields = ('No new activity. Last activity on {} at {} ({} days ago)'.format(lastDate, lastTime, (d1-d0).days),'',)
            tupFormats = ('','',)
            create_email_text(tupFields, tupFormats)
        else:
            # Loop through each new activity and report
            for endDate, endtime, examinedFiles, sizeOfExaminedFiles, addedFiles, deletedFiles, modifiedFiles, \
                filesWithError, parsedResult, warnings, errors in emailRows:
            
                # Determine file count & size diffeence from last run
                examinedFilesDelta = examinedFiles - lastFileCount
                write_log_entry(2, 'examinedFilesDelta = {} - {} = {}\n'.format(examinedFiles, lastFileCount, examinedFilesDelta))
                fileSizeDelta = sizeOfExaminedFiles - lastFileSize
                write_log_entry(2, 'fileSizeDelta = {} - {} = {}\n'.format(sizeOfExaminedFiles, lastFileSize, fileSizeDelta))

                if options['sizereduce'] == 'mega': 
                    tupFields = (endDate, endtime, examinedFiles, examinedFilesDelta, (sizeOfExaminedFiles / 1000000.00), (fileSizeDelta / 1000000.00), \
                        addedFiles, deletedFiles, modifiedFiles, filesWithError, parsedResult)
                    tupFormats = ('13','11','>12,','>+12,','>15,.2f','>+15,.2f','>12,','>12,','>12,','>12,','>13')
                elif options['sizereduce'] == 'giga':
                    tupFields = (endDate, endtime, examinedFiles, examinedFilesDelta, (sizeOfExaminedFiles / 1000000000.00), (fileSizeDelta / 1000000000.00), \
                        addedFiles, deletedFiles, modifiedFiles, filesWithError, parsedResult)
                    tupFormats = ('13','11','>12,','>+12,','>12,.2f','>+12,.2f','>12,','>12,','>12,','>12,','>13')
                else:
                    tupFields = (endDate, endtime, examinedFiles, examinedFilesDelta, sizeOfExaminedFiles, fileSizeDelta, \
                        addedFiles, deletedFiles, modifiedFiles, filesWithError, parsedResult)
                    tupFormats = ('13','11','>12,','>+12,','>20,','>+20,','>12,','>12,','>12,','>12,','>13')
                create_email_text(tupFields, tupFormats)

                if warnings != '':
                    create_email_text((warnings,'',),('','',))
                if errors != '':
                    create_email_text((errors,'',),('','',))

                # Update latest activity into into backupsets
                sqlStmt = 'UPDATE backupsets SET lastFileCount={}, lastFileSize={}, lastDate=\'{}\', \
                    lasttime=\'{}\' WHERE source=\'{}\' AND destination=\'{}\''.format(examinedFiles, sizeOfExaminedFiles, \
                    endDate, endtime, source, destination)
                write_log_entry(2, '{}\n'.format(sqlStmt))

                dbCursor = exec_sqlite(dbConn, sqlStmt)
                dbConn.commit()

                # Set last file count & size the latest information
                lastFileCount = examinedFiles
                lastFileSize = sizeOfExaminedFiles


# Find all new emails on server
def process_mailbox_pop(mBox):
    write_log_entry(2,'process_mailbox_pop()\n')

    # Open All Mail
    numMails = len(mBox.list()[1])
    write_log_entry(2,'process_mailbox_pop(): POP3: numMails=[{}]\n'.format(numMails))
    for i in range(numMails):
        server_msg, body, octets = mBox.retr(i+1)
        write_log_entry(2, 'server_msg=[{}]  body=[{}]  octets=[{}]\n'.format(server_msg,body,octets))
        msg=''
        for j in body:
            msg = msg + '{}\n'.format(j.decode("utf-8"))
        msg2 = email.message_from_string(msg)  # Get message body
        write_log_entry(2, 'msg2=[{}]'.format(msg2))
        mParts = process_message(msg2)

    return None


# Find all new emails on server
def process_mailbox_imap(mBox):
    # Open All Mail
    write_log_entry(2,'process_mailbox_imap()\n')
    rv, data = mBox.search(None, "ALL")
    if rv != 'OK':
        write_log_entry(2, 'No messages found!\n')
        return

    write_log_entry(2,'search data=[{}]\n'.format(data))
    # Loop through every emial in the mail box
    # data[] contains all the record numbers in the mailbox.
    # Loop through these to get all the existing messages
    for num in data[0].split():
        write_log_entry(2,'num=[{}]\n'.format(num))
        rv, data = mBox.fetch(num,'(RFC822)') # Fetch message #num
        write_log_entry(2,'rv=[{}] data=[{}]\n'.format(rv,data))
        if rv != 'OK':
            write_log_entry(1, 'ERROR getting message: {}\n'.format(num))
            return

        write_log_entry(2,'data[0][1]=[{}]\n'.format(data[0][1]))
        msg = email.message_from_string(data[0][1].decode('utf-8'))  # Get message body
        write_log_entry(2, 'msg=[{}]\n'.format(msg))        
        mParts = process_message(msg)                # Process message into parts

    return None


# Write a message to the log file
def write_log_entry(level, entry):
    if level <= options['verbose']:
        logFile.write(entry)
    return

if __name__ == "__main__":
    # Start Program Timer
    startTime = time.time()

    # Start by parsing command line.
    # We're specifically looking for dbPath or rcPath.
    # We'll look for the rest later.
    cmdLine = parse_command_line()

    # Get operating parameters from .rc file, overlay with command line options
    if cmdLine.rcpath != None:  # RC Path specified on command line
        options['rcpath'] = '{}/{}'.format(cmdLine.rcpath, rcName)
    else: # RC path not specified on command line. use default location
        options['rcpath'] = '{}/{}'.format(get_script_path(), rcName)

    needToExit=False   # Will be true if rc file or db file needs changing
    # Initialize RC file
    if rc_initialize(options['rcpath']): #RC file changed or initialized. Can't continue with manual configuration
        sys.stderr.write('RC file {} initialized or changed. Please configure file before running program again.\n'.format(options['rcpath']))
        needToExit=True  #Can't continue if RC gets initialized - need to editparameters

    # Get additional options from config file
    parse_config_file(options['rcpath'], cmdLine)

    # Next, let's check if the DB exists or needs initializing
    if ((os.path.isfile(options['dbpath']) is not True) or ('initdb' in options)): # DB file doesn't exist or forced initialization
        sys.stderr.write('Database {} needs initializing.\n'.format(options['dbpath']))
        dbConn = sqlite3.connect(options['dbpath'])
        db_initialize(dbConn)
        dbConn.commit()
        dbConn.close()
        sys.stderr.write('Database {} initialized. Exiting program.\n'.format(options['dbpath']))
        needToExit=True

    maj, min, subm, res = curr_db_version()
    if res == False:
        sys.stderr.write('Database version mismatch. {}.{}.{} required. Current version is {}.{}.{}.\n'.format(dbversion[0], dbversion[1], dbversion[2],
            maj, min, subm))
        sys.stderr.write('Run program with \'-i\' option to update database.\n')
        needToExit = True

    if needToExit:
        sys.exit(1)

    if cmdLine.version == True:   # Print version info & exit
        version_info()
        sys.exit(0)

    # Open log file
    if ('logappend' in options) and (options['logappend'] is True):
        logFile = open(options['logpath'],'a')
    else:
        logFile = open(options['logpath'],'w')

    # Open SQLITE database
    dbConn = sqlite3.connect(options['dbpath'])
    dbCursor = dbConn.cursor()

    # Write startup information to log file
    write_log_entry(1,'******** dupReport Log - Start: {}\n'.format(time.asctime(time.localtime(time.time()))))
    write_log_entry(1,'Logfile=[{}]  appendlog=[{}]  logLevel=[{}]\n'.format(options['logpath'], options['logappend'], \
        options['verbose']))
    write_log_entry(2,'Config file options: {}\n'.format(options));
    write_log_entry(2,'dbPath={}  rcpath={}\n'.format(options['dbpath'], options['rcpath']))
    
    if ('collect' in options) or ('report' not in options):
        if options['intransport'] == 'pop3':   # Incoming transport = POP3
            write_log_entry(2,'Using POP3 incoming transport. Server={} Port={} Encryption={}\n'.format(options['inserver'], \
                options['inport'],options['inencryption']))
            # Open incoming mailbox
            try:
                if options['inencryption'] == 'ssl':
                    mailBox = poplib.POP3_SSL(options['inserver'],options['inport'])
                else:
                    mailBox = poplib.POP3(options['inserver'],options['inport'])
                rv = mailBox.user(options['inaccount'])
                write_log_entry(2,'POP3 user()=[{}]\n'.format(rv))
                rv = mailBox.pass_(options['inpassword'])
                write_log_entry(2,'POP3 password()=[{}]\n'.format(rv))
            except Exception as err:
                write_log_entry(2,'Failed to connect to POP server: {}\n'.format(e.args))
                sys.exit(1)

            rv, items, octets = mailBox.list()
            write_log_entry(2,'mailBox.list() rv=[{}]  items=[{}]  octets=[{}]'.format(rv,items,octets))

            process_mailbox_pop(mailBox)
            mailBox.quit()
        elif options['intransport'] == 'imap':   # Incoming transport = IMAP
            write_log_entry(2,'Using IMAP incoming transport. Server={} Port={} Encryption={}\n'.format(options['inserver'], \
                options['inport'],options['inencryption']))
            if (options['inencryption'] == 'ssl') or (options['inencryption'] == 'tls'):
                mailBox = imaplib.IMAP4_SSL(options['inserver'], options['inport'])
            else:
                mailBox = imaplib.IMAP4(options['inserver'], options['inport'])
            try:
                rv, data = mailBox.login(options['inaccount'], options['inpassword'])
            except imaplib.IMAP4.error:
                write_log_entry(1,'email server LOGIN FAILED!!! \n')
                sys.exit(1)

            write_log_entry(2,'rv={}\ndata={}\n'.format(rv, data))

            rv, mailboxes = mailBox.list()
            if rv == 'OK':
                write_log_entry(2,'Mailboxes: {}\n'.format(mailboxes))

            rv, data = mailBox.select(options['infolder'])
            write_log_entry(2,'rv=[{}] data=[{}]\n'.format(rv, data))
            if rv == 'OK':
                write_log_entry(1, 'Processing mailbox...\n')
                process_mailbox_imap(mailBox)
            mailBox.logout()
        else:
            write_log_entry(1,'Unknown incoming transport: {}\n'.format(options['intransport']))

    if ('report' in options) or ('collect' not in options):
        # All email has been collected. Create the report
        create_summary_report()

        # Calculate running time
        runningTime = 'Running Time: {:.3f} seconds.\n'.format(time.time() - startTime)
        create_email_text((runningTime,),('',))
    
        # Send the report through email
        send_email()

    dbConn.commit()    # Commit any remaining database transactions
    dbConn.close()     # Close database

    write_log_entry(1,'Program completed - exiting\n')
    # Close log file
    logFile.close()    

    sys.exit(0)
