#####
#
# Module name:  dupApprise.py
# Purpose:      Management class for Apprise notification service
# 
# Notes: Uses the Apprise push notification utility from @caronc
#        https://github.com/caronc/apprise
#        For any Apprise support or feature requests, please see the Apprise GitHub site
#
#####

# Import system modules
import db
import drdatetime

# Import dupReport modules
import globs

class dupApprise:
    appriseConn = None
    appriseOpts = None
    services = None

    def __init__(self):
        globs.log.write(1, function='Apprise', action='Init', msg='Initializing Apprise support')

        #import apprise

        # Read name/value pairs from [apprise] section
        self.appriseOpts = globs.optionManager.getRcSection('apprise')

        if 'services' not in self.appriseOpts:
            globs.log.write(1, function='Apprise', action='Init', msg='Error: No services defined for Apprise notification')
            globs.closeEverythingAndExit(1)  # Abort program. Can't continue

        # Set defaults for missing values
        self.appriseOpts['title'] = 'Apprise Notification for #SRCDEST# Backup' if 'title' not in self.appriseOpts else self.appriseOpts['title']
        self.appriseOpts['body'] = 'Completed at #COMPLETETIME#: #RESULT# - #ERRMSG#' if 'body' not in self.appriseOpts else self.appriseOpts['body']
        self.appriseOpts['titletruncate'] = '0' if 'titletruncate' else self.appriseOpts['titletruncate']
        self.appriseOpts['bodytruncate'] = '0' if 'bodytruncate' not in self.appriseOpts else self.appriseOpts['bodytruncate']
        self.appriseOpts['msglevel'] = 'failure' if 'msglevel' not in self.appriseOpts else self.appriseOpts['msglevel']

        # Normalize .rc values
        self.appriseOpts['titletruncate'] = int(self.appriseOpts['titletruncate'])
        self.appriseOpts['bodytruncate'] = int(self.appriseOpts['bodytruncate'])
        self.appriseOpts['msglevel'] = self.appriseOpts['msglevel'].lower()
        
        # Check for correct message level indicator
        if self.appriseOpts['msglevel'] not in ('success', 'warning', 'failure'):
            globs.log.write(1, function='Apprise', action='Init', msg='Error: Bad apprise message level: {}'.format(self.appriseOpts['msglevel']))
            globs.closeEverythingAndExit(1)  # Abort program. Can't continue.

        # Initialize apprise library
        result = self.appriseConn = apprise.Apprise()
        globs.log.write(1, function='Apprise', action='Init', msg='Initializing Apprise library. Result={}'.format(result))

        # Add individual service URLs to connection
        self.services =  self.appriseOpts['services'].split(",")
        for i in self.services:
            result = self.appriseConn.add(i)
            globs.log.write(1, function='Apprise', action='Init', msg='Added service {}, result={}'.format(i, result))

        globs.log.write(1, function='Apprise', action='Init', msg='Apprise Initialization complete.')
        return None

    def parseMessage(self, msg, source, destination, result, message, warningmessage, errormessage, completetime):
        globs.log.write(1, function='Apprise', action='parseMessage', msg=msg)

        newMsg = msg
        newMsg = newMsg.replace('#SOURCE#',source)
        newMsg = newMsg.replace('#DESTINATION#',destination)
        newMsg = newMsg.replace('#SRCDEST#','{}{}{}'.format(source, globs.opts['srcdestdelimiter'], destination))
        newMsg = newMsg.replace('#RESULT#',result)
        newMsg = newMsg.replace('#MESSAGE#',message)
        newMsg = newMsg.replace('#ERRMSG#',errormessage)
        newMsg = newMsg.replace('#WARNMSG#',warningmessage)
        newMsg = newMsg.replace('#COMPLETETIME#','{} {}'.format(completetime[0], completetime[1]))

        globs.log.write(1, function='Apprise', action='parseMessage', msg='New message=[{}]'.format(newMsg))
        return newMsg

    def sendNotifications(self):
        sqlStmt = "SELECT source, destination, parsedResult, messages, warnings, errors, timestamp FROM report ORDER BY source"
        dbCursor = globs.db.execSqlStmt(sqlStmt)
        reportRows = dbCursor.fetchall()

        for source, destination, parsedResult, messages, warnings, errors, timestamp in reportRows:
            globs.log.write(1, function='Apprise', action='sendNotifications', msg='Preparing Apprise message for {}-{}, parsedResult={} msglevel={}'.format(source, destination, parsedResult, self.appriseOpts['msglevel']))

            # See if we need to send a notification based on the result status
            if self.appriseOpts['msglevel'] == 'warning':
                if parsedResult.lower() not in ('warning', 'failure'):
                    globs.log.write(1, function='Apprise', action='sendNotifications', msg='Msglevel mismatch at warning level - skipping')
                    continue
            elif self.appriseOpts['msglevel'] == 'failure':
                if parsedResult.lower() != 'failure':
                    globs.log.write(1, function='Apprise', action='sendNotifications', msg='Msglevel mismatch at failure level - skipping')
                    continue

            globs.log.write(3, function='Apprise', action='sendNotifications', msg='Apprise message is sendable.')
           
            newTitle = self.parseMessage(self.appriseOpts['title'], source, destination, parsedResult, messages, warnings, errors, drdatetime.fromTimestamp(timestamp))
            newBody = self.parseMessage(self.appriseOpts['body'], source, destination, parsedResult, messages, warnings, errors, drdatetime.fromTimestamp(timestamp))

            tLen = self.appriseOpts['titletruncate']
            if  tLen != 0:
                newTitle = (newTitle[:tLen]) if len(newTitle) > tLen else newTitle  
            bLen = self.appriseOpts['bodytruncate']
            if  bLen!= 0:
                newBody = (newBody[:bLen]) if len(newBody) > bLen else newBody  

            globs.log.write(3, function='Apprise', action='sendNotifications', msg='Sending notification: Title=[{}] Body=[{}]'.format(newTitle, newBody))
            result = self.appriseConn.notify(title=newTitle, body=newBody)
            globs.log.write(1, function='Apprise', action='sendNotifications', msg='Apprise sent. Result={}.'.format(result))

        return
