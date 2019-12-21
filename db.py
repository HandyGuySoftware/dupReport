#####
#
# Module name:  db.py
# Purpose:      Sqlite3 database class defnition & functions
# 
# Notes:
#
#####

# Import system modules
import sqlite3
import sys
import os

# Import dupReport modules
import globs
import drdatetime

class Database:
    dbConn = None
    def __init__(self, dbPath):
        globs.log.write(1, 'Database.__init__({})'.format(globs.maskData(dbPath)))

        # First, see if the database is there. If not, need to create it
        isThere = os.path.isfile(dbPath)

        if self.dbConn:     # If not None DB connection already exists. This is bad.
            globs.log.err('SQLite3 error: trying to reinitialize the database connection. Exiting program.')
            globs.closeEverythingAndExit(1) # Abort program. Can't continue with DB error

        try:
            self.dbConn = sqlite3.connect(dbPath)   # Connect to database
        except sqlite3.Error as err:
            globs.log.err('SQLite3 error connecting to {}: {}. Exiting program.'.format(dbPath, err.args[0]))
            globs.closeEverythingAndExit(1) # Abort program. Can't continue with DB error

        if not isThere:     # Database did not exist. Need to initialize contents
            self.dbInitialize()
        return None

    # Close database connection
    def dbClose(self):
        globs.log.write(1, 'Database.dbClose(): Closing database object.')

        # Don't attempt to close a non-existant conmnection
        if self.dbConn:
            self.dbConn.close()
        self.dbConn = None
        return None

    # Return True if need to upgrade DB, false if DB is current.
    def checkDbVersion(self):
        needToUpgrade = False

        globs.log.write(1, 'Database.checkDbVersion()')
        dbCursor = self.execSqlStmt('SELECT major, minor, subminor FROM version WHERE desc = \'database\'')
        maj, min, subm = dbCursor.fetchone()

        currVerNum = (maj * 100) + (min * 10) + subm
        newVerNum = (globs.dbVersion[0] * 100) + (globs.dbVersion[1] * 10) + globs.dbVersion[2]
        globs.log.write(3,'Database: current version={}  new version={}'.format(currVerNum, newVerNum))
        if currVerNum < newVerNum:
            globs.log.err('Database file {} is out of date. Needs update to latest version.'.format(globs.opts['dbpath']))
            needToUpgrade = True

        return needToUpgrade, currVerNum

    # Commit pending database transaction
    def dbCommit(self):
        globs.log.write(1, 'Database.dbCommit(): Committing transaction.')
        if self.dbConn:     # Don't try to commit to a nonexistant connection
            self.dbConn.commit()
        return None

    def execEmailInsertSql(self, mParts, sParts, dParts):  
        globs.log.write(1, 'db.execEmailInsertSql(()')
        globs.log.write(2, 'messageId={}  sourceComp={}  destComp={}'.format(mParts['messageId'], mParts['sourceComp'], mParts['destComp']))

        durVal = float(dParts['endTimestamp']) - float(dParts['beginTimestamp'])
        sqlStmt = "INSERT INTO emails(messageId, sourceComp, destComp, emailTimestamp, \
            deletedFiles, deletedFolders, modifiedFiles, examinedFiles, \
            openedFiles, addedFiles, sizeOfModifiedFiles, sizeOfAddedFiles, sizeOfExaminedFiles, \
            sizeOfOpenedFiles, notProcessedFiles, addedFolders, tooLargeFiles, filesWithError, \
            modifiedFolders, modifiedSymlinks, addedSymlinks, deletedSymlinks, partialBackup, \
            dryRun, mainOperation, parsedResult, verboseOutput, verboseErrors, endTimestamp, \
            beginTimestamp, duration, messages, warnings, errors, dbSeen, dupversion, logdata) \
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?, ?)"

        data  = (mParts['messageId'], mParts['sourceComp'], mParts['destComp'], mParts['emailTimestamp'], sParts['deletedFiles'], \
                sParts['deletedFolders'], sParts['modifiedFiles'], sParts['examinedFiles'], sParts['openedFiles'], \
                sParts['addedFiles'], sParts['sizeOfModifiedFiles'], sParts['sizeOfAddedFiles'], sParts['sizeOfExaminedFiles'], sParts['sizeOfOpenedFiles'], \
                sParts['notProcessedFiles'], sParts['addedFolders'], sParts['tooLargeFiles'], sParts['filesWithError'], \
                sParts['modifiedFolders'], sParts['modifiedSymlinks'], sParts['addedSymlinks'], sParts['deletedSymlinks'], \
                sParts['partialBackup'], sParts['dryRun'], sParts['mainOperation'], sParts['parsedResult'], sParts['verboseOutput'], \
                sParts['verboseErrors'], dParts['endTimestamp'], dParts['beginTimestamp'], \
                durVal, sParts['messages'], sParts['warnings'], sParts['errors'], sParts['dupversion'], sParts['logdata'])

        globs.log.write(3, 'sqlStmt=[{}]'.format(sqlStmt))
        globs.log.write(3, 'data=[{}]'.format(data))

        if not self.dbConn:
            return None

        # Set db cursor
        curs = self.dbConn.cursor()
        try:
            curs.execute(sqlStmt, data)
        except sqlite3.Error as err:
            globs.log.err('SQLite error: {}\n'.format(err.args[0]))
            globs.log.write(1, 'SQLite error: {}\n'.format(err.args[0]))
            globs.closeEverythingAndExit(1)  # Abort program. Can't continue with DB error
        
        self.dbCommit()
        return None

    def execReportInsertSql(self, sqlStmt, sqlData):  
        globs.log.write(1, 'db.execReportInsertSql(()')
        globs.log.write(3, 'sqlStmt=[{}]'.format(sqlStmt))
        globs.log.write(3, 'sqlData=[{}]'.format(sqlData))

        if not self.dbConn:
            return None

        # Set db cursor
        curs = self.dbConn.cursor()
        try:
            curs.execute(sqlStmt, sqlData)
        except sqlite3.Error as err:
            globs.log.err('SQLite error: {}\n'.format(err.args[0]))
            globs.log.write(1, 'SQLite error: {}\n'.format(err.args[0]))
            globs.closeEverythingAndExit(1)  # Abort program. Can't continue with DB error
        
        self.dbCommit()
        return None

    # Execute a Sqlite command and manage exceptions
    # Return the cursor object to the command result
    def execSqlStmt(self, stmt):
        globs.log.write(1, 'Database.execSqlStmt(): Executing SQL command.')
        globs.log.write(3, 'SQL stmt=[{}]'.format(stmt))

        if not self.dbConn:
            return None

        # Set db cursor
        curs = self.dbConn.cursor()
        try:
            curs.execute(stmt)
        except sqlite3.Error as err:
            globs.log.err('SQLite error: {}\n'.format(err.args[0]))
            globs.log.write(1, 'SQLite error: {}\n'.format(err.args[0]))
            globs.closeEverythingAndExit(1)  # Abort program. Can't continue with DB error
        
        # Return the cursor to the executed command result.    
        return curs

    # Initialize database to empty, default tables
    def dbInitialize(self):
        globs.log.write(1, 'Database.dbInitialize()')

        # Don't initialize a non-existant connection
        if not self.dbConn:
            return None

        # Drop any tables and indices that might already exist in the database
        self.execSqlStmt("drop table if exists version")
        self.execSqlStmt("drop table if exists emails")
        self.execSqlStmt("drop table if exists backupsets")
        self.execSqlStmt("drop table if exists report")
        self.execSqlStmt("drop index if exists emailindx")
        self.execSqlStmt("drop index if exists srcdestindx")
 
        # version table holds current database version.
        # Used to check for need to change database formats
        self.execSqlStmt("create table version (desc varchar(20), major int, minor int, subminor int)")
        self.execSqlStmt("insert into version(desc, major, minor, subminor) values (\'database\',{},{},{})".format(globs.dbVersion[0], globs.dbVersion[1], globs.dbVersion[2]))

        # emails table holds information about all emails received
        sqlStmt = "create table emails (messageId varchar(50), sourceComp varchar(50), destComp varchar(50), \
            emailTimestamp real, deletedFiles int, deletedFolders int, modifiedFiles int, \
            examinedFiles int, openedFiles int, addedFiles int, sizeOfModifiedFiles int, sizeOfAddedFiles int, sizeOfExaminedFiles int, \
            sizeOfOpenedFiles int, notProcessedFiles int, addedFolders int, tooLargeFiles int, filesWithError int, \
            modifiedFolders int, modifiedSymlinks int, addedSymlinks int, deletedSymlinks int, partialBackup varchar(30), \
            dryRun varchar(30), mainOperation varchar(30), parsedResult varchar(30), verboseOutput varchar(30), \
            verboseErrors varchar(30), endTimestamp real, \
            beginTimestamp real, duration real, messages varchar(255), warnings varchar(255), errors varchar(255), failedMsg varchar(100), dbSeen int, dupversion varchar(100), logdata varchar(255))"
        self.execSqlStmt(sqlStmt)
        self.execSqlStmt("create index emailindx on emails (messageId)")
        self.execSqlStmt("create index srcdestindx on emails (sourceComp, destComp)")

        sqlStmt = "create table report (source varchar(20), destination varchar(20), timestamp real, duration real, examinedFiles int, examinedFilesDelta int, \
            sizeOfExaminedFiles int, fileSizeDelta int, addedFiles int, deletedFiles int, modifiedFiles int, filesWithError int, parsedResult varchar(30), messages varchar(255), \
            warnings varchar(255), errors varchar(255), failedMsg varchar(100), dupversion varchar(100), logdata varchar(255))"
        self.execSqlStmt(sqlStmt)

        # backup sets contains information on all source-destination pairs in the backups
        self.execSqlStmt("create table backupsets (source varchar(20), destination varchar(20), lastFileCount integer, lastFileSize integer, \
            lastTimestamp real)")

        self.dbCommit()

        self.dbCompact()
        return None

    # See if a particular message ID is already in the database
    # Return True (already there) or False (not there)
    def searchForMessage(self, msgID):
        globs.log.write(1,'Database.searchForMessage({})'.format(msgID))
        sqlStmt = "SELECT messageId FROM emails WHERE messageId=\'{}\'".format(msgID)
        dbCursor = self.execSqlStmt(sqlStmt)
        idExists = dbCursor.fetchone()
        if idExists:
            globs.log.write(2,'Message [{}] already in email database'.format(msgID))
            return True

        return False

    def searchSrcDestPair(self, src, dest, add2Db = True):
        globs.log.write(1, 'Database.searchSrcDestPair({}, {})'.format(src, dest))
        sqlStmt = "SELECT source, destination FROM backupsets WHERE source=\'{}\' AND destination=\'{}\'".format(src, dest)
        dbCursor = self.execSqlStmt(sqlStmt)
        idExists = dbCursor.fetchone()
        if idExists:
            globs.log.write(2, "Source/Destination pair [{}/{}] already in database.".format(src, dest))
            return True

        if add2Db is True:
            sqlStmt = "INSERT INTO backupsets (source, destination, lastFileCount, lastFileSize, lastTimestamp) \
                VALUES ('{}', '{}', 0, 0, 0)".format(src, dest)
            globs.log.write(3, '{}'.format(sqlStmt))
            self.execSqlStmt(sqlStmt)
            self.dbCommit()
            globs.log.write(2, "Source/Destination pair [{}/{}] added to database".format(src, dest))

        return False

    # Roll back database to specific date/time
    # Datespec = Date & time to roll back to
    def rollback(self, datespec):
        globs.log.write(1,'db.rollback({})'.format(datespec))

        # Get timestamp for input date/time
        newTimeStamp = drdatetime.toTimestamp(datespec)

        # Delete all email records that happened after input datetime
        sqlStmt = 'DELETE FROM emails WHERE emailtimestamp > {}'.format(newTimeStamp)
        dbCursor = self.execSqlStmt(sqlStmt)

        # Delete all backup set records that happened after input datetime
        sqlStmt = 'SELECT source, destination FROM backupsets WHERE lastTimestamp > {}'.format(newTimeStamp)
        dbCursor = self.execSqlStmt(sqlStmt)
        setRows= dbCursor.fetchall()
        for source, destination in setRows:
            # Select largest timestamp from remaining data for that source/destination
            sqlStmt = 'select max(endTimeStamp), examinedFiles, sizeOfExaminedFiles from emails where sourceComp = \'{}\' and destComp= \'{}\''.format(source, destination)
            dbCursor = self.execSqlStmt(sqlStmt)
            emailTimestamp, examinedFiles, sizeOfExaminedFiles = dbCursor.fetchone()
            if emailTimestamp is None:
                # After the rollback, some srcdest pairs may have no corresponding entries in the the database, meaning they were not seen until after the rollback period
                # We should remove these from the database, to return it to the state it was in before the rollback.
                globs.log.write(2, 'Deleting {}{}{} from backupsets. Not seen until after rollback.'.format(source, globs.opts['srcdestdelimiter'], destination))
                sqlStmt = 'DELETE FROM backupsets WHERE source = \"{}\" AND destination = \"{}\"'.format(source, destination)
                dbCursor = self.execSqlStmt(sqlStmt)
            else:
                globs.log.write(2, 'Resetting {}{}{} to {}'.format(source, globs.opts['srcdestdelimiter'], destination, drdatetime.fromTimestamp(emailTimestamp)))
                # Update backupset table to reflect rolled-back date
                sqlStmt = 'update backupsets set lastFileCount={}, lastFileSize={}, lastTimestamp={} where source = \'{}\' and destination = \'{}\''.format(examinedFiles, sizeOfExaminedFiles, emailTimestamp, source, destination)
                dbCursor = self.execSqlStmt(sqlStmt)
            
        self.dbCommit()
        return None

    # Remove a source/destination pair from the database
    def removeSrcDest(self, source, destination):
        globs.log.write(1, 'db.removeSrcDest({}, {})'.format(source, destination))

        # Does the src/dest exist in the database?
        exists = self.searchSrcDestPair(source, destination, False)
        if not exists:
            globs.log.err('Pair {}{}{} does not exist in database. Check spelling and capitalization then try again.'.format(source, globs.opts['srcdestdelimiter'], destination))
            return False

        sqlStmt = "DELETE FROM backupsets WHERE source = \"{}\" AND destination = \"{}\"".format(source, destination)
        dbCursor = self.execSqlStmt(sqlStmt)

        sqlStmt = "DELETE FROM emails WHERE sourceComp = \"{}\" AND destComp = \"{}\"".format(source, destination)
        dbCursor = self.execSqlStmt(sqlStmt)

        self.dbCommit()

        globs.log.out('Pair {}{}{} removed from database.'.format(source, globs.opts['srcdestdelimiter'], destination))
        globs.log.out("Please remove all emails referencing the \'{}{}{}\' backup,\nor they will be added back into the database the next time dupReport is run.".format(source, globs.opts['srcdestdelimiter'], destination))

        return True

    # Purge database of old emails
    def purgeOldEmails(self):
        globs.log.write(1, 'db.purgeOldEmails()')

        globs.log.write(2, 'Purging unseen emails')
        self.execSqlStmt('DELETE FROM emails WHERE dbSeen = 0')
        self.dbCommit()

        self.dbCompact()

        return None

    # Compact database to eliminate unused space
    def dbCompact(self):
        globs.log.write(1, 'dbCompact()')

        # Need to reset connection isolation level in order to compress database
        # Why? Not sure, but see https://github.com/ghaering/pysqlite/issues/109 for details
        isoTmp = self.dbConn.isolation_level
        self.dbConn.isolation_level = None
        self.execSqlStmt('VACUUM')
        self.dbConn.isolation_level = isoTmp    # Re-set isolation level back to previous value
        self.dbCommit()

        globs.log.write(1, 'Database compacted')
        return None




        