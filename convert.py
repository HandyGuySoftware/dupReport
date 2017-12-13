#####
#
# Module name:  convert.py
# Purpose:      Convert older databases and .rc files to the latest format
# 
# Notes:
#
#####

# Import system modules
import sqlite3
import sys

# Import dupReport modules
import globs
import options
import db
import drdatetime

def convertRc(oMgr, fromVersion):
    optList = [
        ('main',        'dbpath',           'main',         'dbpath'),
        ('main',        'logpath',          'main',         'logpath'),
        ('main',        'verbose',          'main',         'verbose'),
        ('main',        'logappend',        'main',         'logappend'),
        ('main',        'sizereduce',       'report',       'sizedisplay'),
        ('main',        'subjectregex',     'main',         'subjectregex'),
        ('main',        'summarysubject',   'report',       'reporttitle'),
        ('main',        'srcregex',         'main',         'srcregex'),
        ('main',        'destregex',        'main',         'destregex'),
        ('main',        'srcdestdelimiter', 'main',         'srcdestdelimiter'),
        ('main',        'border',           'report',       'border'),
        ('main',        'padding',          'report',       'padding'),
        ('main',        'disperrors',       'report',       'displayerrors'),
        ('main',        'dispwarnings',     'report',       'displaywarnings'),
        ('main',        'dispmessages',     'report',       'displaymessages'),
        ('main',        'sortorder',        'report',       'sortby'),
        ('main',        'dateformat',       'main',         'dateformat'),
        ('main',        'timeformat',       'main',         'timeformat'),

        ('incoming',    'transport',        'incoming',     'intransport'),
        ('incoming',    'server',           'incoming',     'inserver'),
        ('incoming',    'port',             'incoming',     'inport'),
        ('incoming',    'encryption',       'incoming',     'inencryption'),
        ('incoming',    'account',          'incoming',     'inaccount'),
        ('incoming',    'password',         'incoming',     'inpassword'),
        ('incoming',    'folder',           'incoming',     'infolder'),

        ('outgoing',    'server',           'outgoing',     'outserver'),
        ('outgoing',    'port',             'outgoing',     'outport'),
        ('outgoing',    'encryption',       'outgoing',     'outencryption'),
        ('outgoing',    'account',          'outgoing',     'outaccount'),
        ('outgoing',    'password',         'outgoing',     'outpassword'),
        ('outgoing',    'sender',           'outgoing',     'outsender'),
        ('outgoing',    'receiver',         'outgoing',     'outreceiver')
        ]

    # Now, start adding back in secitons
    if oMgr.parser.has_section('main') is False:
        globs.log.write(1, 'Adding [main] section.')
        oMgr.addRcSection('main')
    globs.log.write(1, 'Updating version number.')
    oMgr.setRcOption('main', 'version', '{}.{}.{}'.format(globs.version[0],globs.version[1],globs.version[2]))

    if oMgr.parser.has_section('incoming') is False:
        globs.log.write(1, 'Adding [incoming] section.')
        oMgr.addRcSection('incoming')

    if oMgr.parser.has_section('outgoing') is False:
        globs.log.write(1, 'Adding [outgoing] section.')
        oMgr.addRcSection('outgoing')

    if oMgr.parser.has_section('report') is False:
        globs.log.write(1, 'Adding [report] section.')
        oMgr.addRcSection('report')

    if oMgr.parser.has_section('headings') is False:
        globs.log.write(1, 'Adding [headings] section.')
        oMgr.addRcSection('headings')

    for fromsection, fromoption, tosection, tooption in optList:
        globs.log.write(1, 'Updating [{}] {} to: [{}] {}'.format(fromsection, fromoption, tosection, tooption))
        value = oMgr.getRcOption(fromsection, fromoption)
        oMgr.clearRcOption(fromsection, fromoption)
        oMgr.setRcOption(tosection, tooption, value)

    # Adjusted format of sizeDisplay in version 2.1
    szDisp = oMgr.getRcOption('report', 'sizedisplay')
    if szDisp == 'none':
        oMgr.setRcOption('report', 'sizedisplay', 'byte')
    oMgr.setRcOption('report', 'showsizedisplay', 'true')
        

    globs.log.write(1, 'Writing new .rc file.')
    oMgr.updateRc()

    return None;


def convertDb(fromVersion):
    globs.log.write(1, 'Converting database to version 1.0.1')

    # Update DB version number
    globs.db.execSqlStmt("UPDATE version SET major = 1, minor = 0, subminor = 1 WHERE desc = 'database'")

    sqlStmt = "create table report (source varchar(20), destination varchar(20), timestamp real, examinedFiles int, examinedFilesDelta int, \
    sizeOfExaminedFiles int, fileSizeDelta int, addedFiles int, deletedFiles int, modifiedFiles int, filesWithError int, parsedResult varchar(30), messages varchar(255), \
    warnings varchar(255), errors varchar(255), failedMsg varchar(100))"
    globs.db.execSqlStmt(sqlStmt)
    
    # Add timestamp fields to tables
    globs.db.execSqlStmt("ALTER TABLE emails ADD COLUMN emailTimestamp real")
    globs.db.execSqlStmt("ALTER TABLE emails ADD COLUMN endTimestamp real")
    globs.db.execSqlStmt("ALTER TABLE emails ADD COLUMN beginTimestamp real")

    # Clean up bad data left from older versions. Not sure how this happened, but it really screws things up
    globs.db.execSqlStmt("DELETE FROM emails WHERE beginTime > '23:59:59' or endTime > '23:59:59'")

    # Loop through emails table
    dbCursor = globs.db.execSqlStmt("SELECT messageId, emailDate, emailTime, endDate, endTime, beginDate, beginTime FROM emails")
    emailRows = dbCursor.fetchall()
    for messageId, emailDate, emailTime, endDate, endTime, beginDate, beginTime in emailRows:
        # Create email timestamp
        dateStr = '{} {}'.format(emailDate,emailTime) 
        emailTimestamp = drdatetime.toTimestamp(dateStr, 'YYYY-MM-DD', 'HH:MM:SS')
        
        # Create endTime timestamp
        dateStr = '{} {}'.format(endDate,endTime) 
        endTimestamp = drdatetime.toTimestamp(dateStr, 'YYYY/MM/DD', 'HH:MM:SS')

        # Create beginTime timestamp
        dateStr = '{} {}'.format(beginDate,beginTime) 
        beginTimestamp = drdatetime.toTimestamp(dateStr, 'YYYY/MM/DD', 'HH:MM:SS')

        # Update emails table with new data
        if endTimestamp is not None and beginTimestamp is not None:
            sqlStmt = "UPDATE emails SET emailTimestamp = {}, endTimestamp = {}, beginTimestamp = {} WHERE messageId = \'{}\'".format(emailTimestamp, endTimestamp, beginTimestamp, messageId)
            globs.log.write(1, sqlStmt)
            globs.db.execSqlStmt(sqlStmt)

        globs.log.write(1, 'messageId:{}  emailDate={} emailTime={} emailTimestamp={} endDate={} endTime={} endTimestamp={} beginDate={} beginTime={} beginTimestamp={}'.format(messageId, emailDate, emailTime, emailTimestamp,\
            endDate, endTime, endTimestamp, beginDate, beginTime, beginTimestamp))

    globs.db.execSqlStmt("ALTER TABLE backupsets ADD COLUMN lastTimestamp real")
    dbCursor = globs.db.execSqlStmt("SELECT source, destination, lastDate, lastTime from backupsets")
    setRows = dbCursor.fetchall()
    for source, destination, lastDate, lastTime in setRows:
        dateStr = '{} {}'.format(lastDate,lastTime) 
        lastTimestamp = drdatetime.toTimestamp(dateStr, 'YYYY/MM/DD', 'HH:MM:SS')

        sqlStmt = "UPDATE backupsets SET lastTimestamp = {} WHERE source = \'{}\' AND destination = \'{}\'".format(lastTimestamp, source, destination)
        globs.db.execSqlStmt(sqlStmt)
        globs.log.write(1, 'Source={}  destination={} lastDate={} lastTime={} lastTimestamp={}'.format(source, destination, lastDate, lastTime, lastTimestamp))

    globs.db.dbCommit()
    return None
