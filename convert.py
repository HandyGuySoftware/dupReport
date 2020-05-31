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
from datetime import datetime
from shutil import copyfile

optList210 = [
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

sizeTranslate = { 'byte': 'byte', 'none': 'byte', 'mega': 'mb', 'giga': 'gb' }
v310Translate = {'source':'source','destination':'destination','date':'date','time':'time','dupversion':'dupversion','duration':'duration','files':'examinedFiles','filesplusminus':'examinedFilesDelta','size':'sizeOfExaminedFiles','sizeplusminus':'fileSizeDelta',
                 'errors':'errors','result':'parsedResult','joblogdata':'logdata','joberrors':'errors','added':'addedFiles','deleted':'deletedFiles','modified':'modifiedFiles','jobmessages':'messages','jobwarnings':'warnings'}

def moveOption(oMgr, fromSect, fromOpt, toSect, toOpt):
    globs.log.write(globs.SEV_DEBUG, function='Convert', action='moveOption', msg='Moving [{}]{} to: [{}]{}'.format(fromSect, fromOpt, toSect, toOpt))
    value = oMgr.getRcOption(fromSect, fromOpt)
    if value == None:
        value = ''
    oMgr.clearRcOption(fromSect, fromOpt)
    oMgr.setRcOption(toSect, toOpt, value)

def convertRc(oMgr, fromVersion):
    # Make backup copy of rc file
    now = datetime.now()
    dateStr = now.strftime('%Y%m%d-%H%M%S')
    rcFileName = oMgr.options['rcfilename']
    rcFileBackup = rcFileName + '.' + dateStr
    globs.log.write(globs.SEV_NOTICE, function='Convert', action='convertRc', msg='Backing up .rc file prior to conversion. Backup file is {}'.format(rcFileBackup))
    copyfile(rcFileName, rcFileBackup)

    doConvertRc(oMgr, fromVersion)
    globs.log.write(globs.SEV_NOTICE, function='Convert', action='convertRc', msg='Updating .rc file version number to {}.{}.{}.'.format(globs.rcVersion[0],globs.rcVersion[1],globs.rcVersion[2]))
    oMgr.setRcOption('main', 'rcversion', '{}.{}.{}'.format(globs.rcVersion[0],globs.rcVersion[1],globs.rcVersion[2]))
    oMgr.updateRc()
    return

def doConvertRc(oMgr, fromVersion):
    if fromVersion < 210:
        globs.log.write(globs.SEV_NOTICE, function='Convert', action='doConvertRc', msg='Updating .rc file from version {} to version 210.'.format(fromVersion))
        # Start adding back in secitons
        if oMgr.parser.has_section('main') is False:
            globs.log.write(globs.SEV_DEBUG, function='Convert', action='convertRc', msg='Adding [main] section.')
            oMgr.addRcSection('main')

        if oMgr.parser.has_section('incoming') is False:
            globs.log.write(globs.SEV_DEBUG, function='Convert', action='convertRc', msg='Adding [incoming] section.')
            oMgr.addRcSection('incoming')

        if oMgr.parser.has_section('outgoing') is False:
            globs.log.write(globs.SEV_DEBUG, function='Convert', action='convertRc', msg='Adding [outgoing] section.')
            oMgr.addRcSection('outgoing')

        if oMgr.parser.has_section('report') is False:
            globs.log.write(globs.SEV_DEBUG, function='Convert', action='convertRc', msg='Adding [report] section.')
            oMgr.addRcSection('report')

        if oMgr.parser.has_section('headings') is False:
            globs.log.write(globs.SEV_DEBUG, function='Convert', action='convertRc', msg='Adding [headings] section.')
            oMgr.addRcSection('headings')

        for fromsection, fromoption, tosection, tooption in optList210:
            moveOption(oMgr, fromsection, fromoption, tosection, tooption)

        # Adjusted format of sizeDisplay in version 2.1
        szDisp = oMgr.getRcOption('report', 'sizedisplay')
        if szDisp == 'none':
            oMgr.setRcOption('report', 'sizedisplay', 'byte')
        oMgr.setRcOption('report', 'showsizedisplay', 'true')

        oMgr.updateRc()
        doConvertRc(oMgr, 210)
    elif fromVersion < 300:
        globs.log.write(globs.SEV_NOTICE, function='Convert', action='doConvertRc', msg='Updating .rc file from version {} to version 300.'.format(fromVersion))
        # Remove deprecated options
        if oMgr.parser.has_option('report', 'noactivitybg') == True:    # Deprecated in version 2.2.0
            oMgr.clearRcOption('report', 'noactivitybg')

        if oMgr.parser.has_option('main', 'version') == True:    # Deprecated in version 2.2.7 (renamed to 'rcversion')
            oMgr.clearRcOption('main', 'version')

        oMgr.updateRc()
        doConvertRc(oMgr, 300)
    elif fromVersion < 310:
        globs.log.write(globs.SEV_NOTICE, function='Convert', action='doConvertRc', msg='Updating .rc file from version {} to version 310.'.format(fromVersion))
        # Adjust size display option
        value1 = oMgr.getRcOption('report', 'sizedisplay')
        value2 = oMgr.getRcOption('report', 'showsizedisplay')
        if value2.lower() == 'false':
            value1 = 'none'
        value1 = sizeTranslate[value1]
        oMgr.setRcOption('report', 'sizedisplay', value1)
        oMgr.clearRcOption('report', 'showsizedisplay')

        # Change basic report options
        reportTitle = oMgr.getRcOption('report', 'reporttitle')
        oMgr.setRcOption('report', 'title', 'Duplicati Backup Summary Report')
        oMgr.clearRcOption('report', 'reporttitle')
        oMgr.setRcOption('report', 'columns', 'source:Source, destination:Destination, date: Date, time: Time, dupversion:Version, duration:Duration, examinedFiles:Files, examinedFilesDelta:+/-, sizeOfExaminedFiles:Size, fileSizeDelta:+/-, addedFiles:Added, deletedFiles:Deleted, modifiedFiles:Modified, filesWithError:Errors, parsedResult:Result, messages:Messages, warnings:Warnings, errors:Errors, logdata:Log Data')
        oMgr.setRcOption('report', 'weminline', 'false')
        moveOption(oMgr, 'report', 'subheadbg', 'report', 'groupheadingbg')
       
        # Set up report sections
        mainReport = oMgr.getRcOption('report', 'style')    # This is the main report run
        oMgr.clearRcOption('report', 'style')

        # Add new sections using pre-defined defaults
        oMgr.addRcSection('srcdest')
        oMgr.addRcSection('bysrc')
        oMgr.addRcSection('bydest')
        oMgr.addRcSection('bydate')
        oMgr.addRcSection('noactivity')
        oMgr.addRcSection('lastseen')
        for section, option, default, cancontinue in options.rcParts:
            if section in ['srcdest','bysrc','bydest','bydate','noactivity','lastseen']:
                oMgr.setRcOption(section, option, default)
       
        # Now, set the default report to mimic what was in the old format
        oMgr.setRcOption(mainReport, 'title', reportTitle)
        oMgr.setRcOption('report', 'layout', mainReport + ', noactivity')

        # Update 'last seen' settings
        value1 = oMgr.getRcOption('report', 'lastseensummary')
        value2 = oMgr.getRcOption('report', 'lastseensummarytitle')
        if value1.lower() != 'none':
            oMgr.setRcOption('lastseen', 'title', value2)
            value3 = oMgr.getRcOption('report', 'layout')
            if value1.lower() == 'top':
                oMgr.setRcOption('report', 'layout', 'lastseen, ' + value3)
            else:
                oMgr.setRcOption('report', 'layout', value3 + ', lastseen')
        oMgr.clearRcOption('report', 'lastseensummary')
        oMgr.clearRcOption('report', 'lastseensummarytitle')
        
        # Adjust field background colors
        moveOption(oMgr, 'report', 'lastseenlow', 'report', 'normaldays')
        moveOption(oMgr, 'report', 'lastseenlowcolor', 'report', 'normalbg')
        moveOption(oMgr, 'report', 'lastseenmed', 'report', 'warningdays')
        moveOption(oMgr, 'report', 'lastseenmedcolor', 'report', 'warningbg')
        moveOption(oMgr, 'report', 'lastseenhighcolor', 'report', 'errorbg')

        # Convert headings to new 'columns' format
        headings = oMgr.getRcSection('headings')
        columns = ''
        colIndex = -1
        for columnName in headings:
            colIndex += 1
            if headings[columnName] != '':
                columns += v310Translate[columnName] + ':' + headings[columnName]
                if colIndex < len(headings)-1:
                    columns += ', '
        if columns[-2:] == ', ':
            columns = columns[:len(columns)-2:]
        oMgr.setRcOption(mainReport, 'columns', columns)
        oMgr.clearRcSection('headings')

        # Change to new email server format
        # Set [main]emailservers= option
        oMgr.setRcOption('main', 'emailservers', 'incoming, outgoing')

        # Move 'in*' to just '*'
        protocol = oMgr.getRcOption('incoming', 'intransport')
        oMgr.setRcOption('incoming', 'protocol', protocol)
        oMgr.clearRcOption('incoming', 'intransport')        
        oMgr.setRcOption('outgoing', 'protocol', 'smtp')

        for option in ['inserver', 'inport', 'inencryption', 'inaccount', 'inpassword', 'infolder', 'inkeepalive']:
            optVal = oMgr.getRcOption('incoming', option)
            oMgr.setRcOption('incoming', option[2:], optVal)
            oMgr.clearRcOption('incoming', option)
        for option in ['outserver', 'outport', 'outencryption', 'outaccount', 'outpassword', 'outsender', 'outsendername', 'outreceiver', 'outkeepalive']:
            optVal = oMgr.getRcOption('outgoing', option)
            oMgr.setRcOption('outgoing', option[3:], optVal)
            oMgr.clearRcOption('outgoing', option)

        # Move 'markread' to incoming
        markread = oMgr.getRcOption('main', 'markread')
        oMgr.setRcOption('incoming', 'markread', markread)
        oMgr.clearRcOption('main', 'markread')

        # Move logging levels
        verbose = oMgr.getRcOption('main', 'verbose')
        if verbose in ['1','2']:
            verbose = '5'
        elif verbose == '3':
            verbose = '7'
        oMgr.setRcOption('main', 'verbose', verbose)

        # Add authentication methods
        oMgr.setRcOption('incoming', 'authentication', 'basic')
        oMgr.setRcOption('outgoing', 'authentication', 'basic')

        # Update [apprise] section, if it exists. If it doesn't, default .rc routine will take care of it.
        if oMgr.hasSection('apprise'):
            oMgr.setRcOption('apprise', 'enabled', 'true')

        oMgr.updateRc()
        doConvertRc(oMgr, 310)
    else:
        pass

    return None;


def convertDb(fromVersion):
    # Make backup copy of datavase file
    now = datetime.now()
    dateStr = now.strftime('%Y%m%d-%H%M%S')
    dbFileName = globs.opts['dbpath']
    dbFileBackup = dbFileName + '.' + dateStr
    globs.log.write(globs.SEV_NOTICE, function='Convert', action='convertDb', msg='Backing up .rc file prior to conversion. Backup file is {}'.format(dbFileBackup))
    copyfile(dbFileName, dbFileBackup)

    doConvertDb(fromVersion)
    globs.log.write(globs.SEV_NOTICE, function='Convert', action='convertDb', msg='Updating database file version number to {}.{}.{}.'.format(globs.dbVersion[0], globs.dbVersion[1], globs.dbVersion[2]))
    globs.db.execSqlStmt("UPDATE version SET major = {}, minor = {}, subminor = {} WHERE desc = 'database'".format(globs.dbVersion[0], globs.dbVersion[1], globs.dbVersion[2]))
    globs.db.dbCommit()

def doConvertDb(fromVersion):
    globs.log.write(globs.SEV_NOTICE, function='Convert', action='doConvertDb', msg='Converting database from version {} to version {}.{}.{}'.format(fromVersion, globs.dbVersion[0], globs.dbVersion[1], globs.dbVersion[2]))

    # Database version history
    # 1.0.1 - Convert from character-based date/time to uynix timestamp format. 
    # 1.0.2 - Calculate & store duraction of backup
    # 1.0.3 - Store new logdata field and Duplicati version numbers (per backup)
    # 3.0.0 - changes to report table for dupReport 3.0.0

    # Update DB version number
    if fromVersion < 101: # Upgrade from DB version 100 (original format). 
        globs.log.write(globs.SEV_NOTICE, function='Convert', action='doConvertDb', msg='Converting database from version {} to version 101'.format(fromVersion))
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
                globs.log.write(globs.SEV_NOTICE, function='Convert', action='doConvertDb', msg=sqlStmt)
                globs.db.execSqlStmt(sqlStmt)

            globs.log.write(globs.SEV_NOTICE, function='Convert', action='doConvertDb', msg='messageId:{}  emailDate={} emailTime={} emailTimestamp={} endDate={} endTime={} endTimestamp={} beginDate={} beginTime={} beginTimestamp={} duration={}'.format(messageId, emailDate, emailTime, emailTimestamp,\
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
            globs.log.write(globs.SEV_NOTICE, function='Convert', action='doConvertDb', msg='Updating backupsets: Source={} destination={} lastDate={} lastTime={} lastTimestamp={}'.format(source, destination, lastDate, lastTime, lastTimestamp))
        doConvertDb(101)
    elif fromVersion < 102: # Upgrade from version 101
        globs.log.write(globs.SEV_NOTICE, function='Convert', action='doConvertDb', msg='Converting database from version {} to version 102'.format(fromVersion))
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
                globs.db.execSqlStmt(sqlStmt)
        globs.db.execSqlStmt("DROP TABLE _emails_old_")
        doConvertDb(102)
    elif fromVersion < 103: # Upgrade from version 102
        globs.log.write(globs.SEV_NOTICE, function='Convert', action='doConvertDb', msg='Converting database from version {} to version 103'.format(fromVersion))
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
        doConvertDb(103)
    elif fromVersion < 300: # Upgrade from version 103
        globs.log.write(globs.SEV_NOTICE, function='Convert', action='doConvertDb', msg='Converting database from version {} to version 300'.format(fromVersion))
        # Add date & time fields to reports table
        globs.db.execSqlStmt("ALTER TABLE report ADD COLUMN date real")
        globs.db.execSqlStmt("ALTER TABLE report ADD COLUMN time real")
        globs.db.execSqlStmt("ALTER TABLE backupsets ADD COLUMN dupversion varchar(100)")
        
        # Insert last dupversion for all existing backupset rows
        globs.db.execSqlStmt("UPDATE backupsets SET dupversion = (SELECT emails.dupversion FROM emails WHERE backupsets.source = emails.sourceComp and backupsets.destination = emails.destComp)")
        doConvertDb(300)
        pass
    else:
        pass

    return None
