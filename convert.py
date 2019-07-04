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
        # From-section  from-option         to-section      to-option
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

    if fromVersion < 210:
        # Start adding back in secitons
        if oMgr.parser.has_section('main') is False:
            globs.log.write(1, 'Adding [main] section.')
            oMgr.addRcSection('main')

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

        # Remove deprecated options
        if oMgr.parser.has_option('report', 'noactivitybg') == True:    # Deprecated in version 2.2.0
            oMgr.clearRcOption('report', 'noactivitybg')

        if oMgr.parser.has_option('main', 'version') == True:    # Deprecated in version 2.2.7 (renamed to 'rcversion')
            oMgr.clearRcOption('main', 'version')
    elif fromVersion < 300:
        # Remove deprecated options
        if oMgr.parser.has_option('report', 'noactivitybg') == True:    # Deprecated in version 2.2.0
            oMgr.clearRcOption('report', 'noactivitybg')

        if oMgr.parser.has_option('main', 'version') == True:    # Deprecated in version 2.2.7 (renamed to 'rcversion')
            oMgr.clearRcOption('main', 'version')

    globs.log.write(1, 'Updating version number.')
    oMgr.setRcOption('main', 'rcversion', '{}.{}.{}'.format(globs.rcVersion[0],globs.rcVersion[1],globs.rcVersion[2]))
    globs.log.write(1, 'Writing new .rc file.')
    oMgr.updateRc()

    return None;


def convertDb(fromVersion):
    globs.log.write(1, 'convertDb(): Converting database from version {} to version {}.{}.{}'.format(fromVersion, globs.dbVersion[0], globs.dbVersion[1], globs.dbVersion[2]))

    # Database version history
    # 1.0.1 - Convert from character-based date/time to uynix timestamp format. 
    # 1.0.2 - Calculate & store duraction of backup
    # 1.0.3 - Store new logdata field and Duplicati version numbers (per backup)

    # Update DB version number
    globs.db.execSqlStmt("UPDATE version SET major = {}, minor = {}, subminor = {} WHERE desc = 'database'".format(globs.dbVersion[0], globs.dbVersion[1], globs.dbVersion[2]))

    if fromVersion == 100: # Upgrade from DB version 100 (original format). 
        sqlStmt = "create table report (source varchar(20), destination varchar(20), timestamp real, duration real, examinedFiles int, examinedFilesDelta int, \
        sizeOfExaminedFiles int, fileSizeDelta int, addedFiles int, deletedFiles int, modifiedFiles int, filesWithError int, parsedResult varchar(30), messages varchar(255), \
        warnings varchar(255), errors varchar(255), failedMsg varchar(100), dupversion varchar(100), logdata varchar(255))"
        globs.db.execSqlStmt(sqlStmt)
    
        # Clean up bad data in emails table left from older versions. Not sure how this happened, but it really screws things up
        globs.db.execSqlStmt("DELETE FROM emails WHERE beginTime > '23:59:59' or endTime > '23:59:59'")

        # In SQLite you can't just drop and add a column (of course :-(
        # You need to recreate the table with the new column & copy the data
        globs.db.execSqlStmt("ALTER TABLE emails RENAME TO _emails_old_")
        globs.db.execSqlStmt("CREATE TABLE emails (messageId varchar(50), sourceComp varchar(50), destComp varchar(50), emailTimestamp real, deletedFiles int, deletedFolders int, modifiedFiles int, \
            examinedFiles int, openedFiles int, addedFiles int, sizeOfModifiedFiles int, sizeOfAddedFiles int, sizeOfExaminedFiles int, sizeOfOpenedFiles int, notProcessedFiles int, addedFolders int, \
            tooLargeFiles int, filesWithError int, modifiedFolders int, modifiedSymlinks int, addedSymlinks int, deletedSymlinks int, partialBackup varchar(30), dryRun varchar(30), mainOperation varchar(30), \
            parsedResult varchar(30), verboseOutput varchar(30), verboseErrors varchar(30), endTimestamp real, beginTimestamp real, duration real, messages varchar(255), warnings varchar(255), errors varchar(255), \
            failedMsg varchar(100), dbSeen int, dupversion varchar(100), logdata varchar(255))")
        globs.db.execSqlStmt("INSERT INTO emails (messageId, sourceComp, destComp, deletedFiles, deletedFolders, modifiedFiles, examinedFiles, openedFiles, addedFiles, sizeOfModifiedFiles, sizeOfAddedFiles, \
            sizeOfExaminedFiles, sizeOfOpenedFiles, notProcessedFiles, addedFolders, tooLargeFiles, filesWithError, modifiedFolders, modifiedSymlinks, addedSymlinks, deletedSymlinks, partialBackup, dryRun, mainOperation, \
            parsedResult, verboseOutput, verboseErrors, messages, warnings, errors, failedMsg) SELECT messageId, sourceComp, destComp, deletedFiles, deletedFolders, \
            modifiedFiles, examinedFiles, openedFiles, addedFiles, sizeOfModifiedFiles, sizeOfAddedFiles, sizeOfExaminedFiles, sizeOfOpenedFiles, notProcessedFiles, addedFolders, tooLargeFiles, filesWithError, modifiedFolders, \
            modifiedSymlinks, addedSymlinks, deletedSymlinks, partialBackup, dryRun, mainOperation, parsedResult, verboseOutput, verboseErrors, messages, warnings, errors, failedMsg FROM _emails_old_")

        # Loop through emails table to update old char-based times to timestamps
        dbCursor = globs.db.execSqlStmt("SELECT messageId, emailDate, emailTime, endDate, endTime, beginDate, beginTime FROM _emails_old_")
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
                sqlStmt = "UPDATE emails SET emailTimestamp = {}, endTimestamp = {}, beginTimestamp = {}, duration = {} WHERE messageId = \'{}\'".format(emailTimestamp, endTimestamp, beginTimestamp, (endTimestamp - beginTimestamp), messageId)
                globs.log.write(1, sqlStmt)
                globs.db.execSqlStmt(sqlStmt)

            globs.log.write(1, 'messageId:{}  emailDate={} emailTime={} emailTimestamp={} endDate={} endTime={} endTimestamp={} beginDate={} beginTime={} beginTimestamp={} duration={}'.format(messageId, emailDate, emailTime, emailTimestamp,\
                endDate, endTime, endTimestamp, beginDate, beginTime, beginTimestamp, duration))
        globs.db.execSqlStmt("DROP TABLE _emails_old_")
 
        # Convert date/time to timestamps in backupsets table
        globs.db.execSqlStmt("ALTER TABLE backupsets ADD COLUMN lastTimestamp real")
        dbCursor = globs.db.execSqlStmt("SELECT source, destination, lastDate, lastTime from backupsets")
        setRows = dbCursor.fetchall()
        for source, destination, lastDate, lastTime in setRows:
            dateStr = '{} {}'.format(lastDate,lastTime) 
            lastTimestamp = drdatetime.toTimestamp(dateStr, 'YYYY/MM/DD', 'HH:MM:SS')

            sqlStmt = "UPDATE backupsets SET lastTimestamp = {} WHERE source = \'{}\' AND destination = \'{}\'".format(lastTimestamp, source, destination)
            globs.db.execSqlStmt(sqlStmt)
            globs.log.write(1, 'Source={}  destination={} lastDate={} lastTime={} lastTimestamp={}'.format(source, destination, lastDate, lastTime, lastTimestamp))
    elif fromVersion == 101: # Upgrade from version 101
        globs.db.execSqlStmt("ALTER TABLE report ADD COLUMN duration real")
        globs.db.execSqlStmt("ALTER TABLE report ADD COLUMN dupversion varchar(100)")
        globs.db.execSqlStmt("ALTER TABLE report ADD COLUMN logdata varchar(255)")
        globs.db.execSqlStmt("UPDATE report SET duration = 0")
        globs.db.execSqlStmt("UPDATE report SET dupversion = ''")
        globs.db.execSqlStmt("UPDATE report SET logdata = ''")

        # Need to change duration column from varchar to real
        # In SQLite you can't just drop and add a column (of course :-(
        # You need to recreate the table with the new column & copy the data
        globs.db.execSqlStmt("ALTER TABLE emails RENAME TO _emails_old_")
        globs.db.execSqlStmt("CREATE TABLE emails (messageId varchar(50), sourceComp varchar(50), destComp varchar(50), emailTimestamp real, deletedFiles int, deletedFolders int, modifiedFiles int, \
            examinedFiles int, openedFiles int, addedFiles int, sizeOfModifiedFiles int, sizeOfAddedFiles int, sizeOfExaminedFiles int, sizeOfOpenedFiles int, notProcessedFiles int, addedFolders int, \
            tooLargeFiles int, filesWithError int, modifiedFolders int, modifiedSymlinks int, addedSymlinks int, deletedSymlinks int, partialBackup varchar(30), dryRun varchar(30), mainOperation varchar(30), \
            parsedResult varchar(30), verboseOutput varchar(30), verboseErrors varchar(30), endTimestamp real, beginTimestamp real, duration real, messages varchar(255), warnings varchar(255), errors varchar(255), \
            failedMsg varchar(100), dbSeen int, dupversion varchar(100), logdata varchar(255))")
        globs.db.execSqlStmt("INSERT INTO emails (messageId, sourceComp, destComp, emailTimestamp, deletedFiles, deletedFolders, modifiedFiles, examinedFiles, openedFiles, addedFiles, sizeOfModifiedFiles, sizeOfAddedFiles, \
            sizeOfExaminedFiles, sizeOfOpenedFiles, notProcessedFiles, addedFolders, tooLargeFiles, filesWithError, modifiedFolders, modifiedSymlinks, addedSymlinks, deletedSymlinks, partialBackup, dryRun, mainOperation, \
            parsedResult, verboseOutput, verboseErrors, endTimestamp, beginTimestamp, messages, warnings, errors, failedMsg, dbSeen) SELECT messageId, sourceComp, destComp, emailTimestamp, deletedFiles, deletedFolders, \
            modifiedFiles, examinedFiles, openedFiles, addedFiles, sizeOfModifiedFiles, sizeOfAddedFiles, sizeOfExaminedFiles, sizeOfOpenedFiles, notProcessedFiles, addedFolders, tooLargeFiles, filesWithError, modifiedFolders, \
            modifiedSymlinks, addedSymlinks, deletedSymlinks, partialBackup, dryRun, mainOperation, parsedResult, verboseOutput, verboseErrors, endTimestamp, beginTimestamp, messages, warnings, errors, failedMsg, dbSeen FROM _emails_old_")

        # Loop through new emails table and set duration field
        dbCursor = globs.db.execSqlStmt("SELECT messageId, beginTimeStamp, endTimeStamp FROM emails")
        emailRows = dbCursor.fetchall()
        for messageId, beginTimeStamp, endTimeStamp in emailRows:
            # Update emails table with new data
            if endTimeStamp is not None and beginTimeStamp is not None:
                sqlStmt = "UPDATE emails SET duration = {} WHERE messageId = \'{}\'".format((endTimeStamp - beginTimeStamp), messageId)
                globs.log.write(1, sqlStmt)
                globs.db.execSqlStmt(sqlStmt)
        globs.db.execSqlStmt("DROP TABLE _emails_old_")
    elif fromVersion == 102: # Upgrade from version 102
        # Add dupversion & logdata fields to emails table
        globs.db.execSqlStmt("ALTER TABLE emails ADD COLUMN dupversion varchar(100)")
        globs.db.execSqlStmt("ALTER TABLE emails ADD COLUMN logdata varchar(255)")
        globs.db.execSqlStmt("UPDATE emails SET dupversion = ''")
        globs.db.execSqlStmt("UPDATE emails SET logdata = ''")

        # Add dupversion & logdata fields to report table
        globs.db.execSqlStmt("ALTER TABLE report ADD COLUMN dupversion varchar(100)")
        globs.db.execSqlStmt("ALTER TABLE report ADD COLUMN logdata varchar(255)")
        globs.db.execSqlStmt("UPDATE report SET dupversion = ''")
        globs.db.execSqlStmt("UPDATE report SET logdata = ''")

    globs.db.dbCommit()
    return None
