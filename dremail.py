#####
#
# Module name:  dremail.com
# Purpose:      Manage email connections for dupReport
# 
# Notes:
#
#####

# Import system modules
import imaplib
import poplib
import email
import re
import datetime
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# Import dupReport modules
import globs
import drdatetime


#Define message segments (line parts) for Duplicati result email messages
# lineParts[] are the individual line items in the Duplicati status email report.
# 1 - internal variable name
# 2 - Duplicati name from email and regex to find it
# 3 - regex flags. 0=none.
# 4 - field Type (0=int or 1=str)
lineParts = [
    ('deletedFiles','DeletedFiles: \d+', 0, 0),
    ('deletedFolders', 'DeletedFolders: \d+', 0, 0),
    ('modifiedFiles', 'ModifiedFiles: \d+', 0, 0),
    ('examinedFiles', 'ExaminedFiles: \d+', 0, 0),
    ('openedFiles', 'OpenedFiles: \d+', 0, 0),
    ('addedFiles', 'AddedFiles: \d+', 0, 0),
    ('sizeOfModifiedFiles', 'SizeOfModifiedFiles: \d+', 0, 0),
    ('sizeOfAddedFiles', 'SizeOfAddedFiles: \d+', 0, 0),
    ('sizeOfExaminedFiles', 'SizeOfExaminedFiles: \d+', 0, 0),
    ('sizeOfOpenedFiles', 'SizeOfOpenedFiles: \d+', 0, 0),
    ('notProcessedFiles', 'NotProcessedFiles: \d+', 0, 0),
    ('addedFolders', 'AddedFolders: \d+', 0, 0),
    ('tooLargeFiles', 'TooLargeFiles: \d+', 0, 0),
    ('filesWithError', 'FilesWithError: \d+', 0, 0),
    ('modifiedFolders', 'ModifiedFolders: \d+', 0, 0),
    ('modifiedSymlinks', 'ModifiedSymlinks: \d+', 0, 0),
    ('addedSymlinks', 'AddedSymlinks: \d+', 0, 0),
    ('deletedSymlinks', 'DeletedSymlinks: \d+', 0, 0),
    ('partialBackup', 'PartialBackup: \w+', 0, 1),
    ('dryRun', 'Dryrun: \w+', 0, 1),
    ('mainOperation', 'MainOperation: \w+', 0, 1),
    ('parsedResult', 'ParsedResult: \w+', 0, 1),
    ('verboseOutput', 'VerboseOutput: \w+', 0, 1),
    ('verboseErrors', 'VerboseErrors: \w+', 0, 1),
    ('endTimeStr', 'EndTime: .*', 0, 1),
    ('beginTimeStr', 'BeginTime: .*', 0, 1),
    ('duration', 'Duration: .*', 0, 1),
    ('messages', 'Messages: \[.*^\]', re.MULTILINE|re.DOTALL, 1),
    ('warnings', 'Warnings: \[.*^\]', re.MULTILINE|re.DOTALL, 1),
    ('errors', 'Errors: \[.*^\]', re.MULTILINE|re.DOTALL, 1),
    ('details','Details: .*', re.MULTILINE|re.DOTALL, 1),
    ('failed', 'Failed: .*', re.MULTILINE|re.DOTALL, 1),
    ]


class EmailServer:
    def __init__(self):
        self.protocol = None
        self.address = None
        self.port = None
        self.encryption = None
        self.accountname = None
        self.passwd = None
        self.server = None
        self.newEmails = None      # List[] of new emails on server. Activated by connect()
        self.numEmails = None      # Number of emails in list
        self.nextEmail = None      # index into list of next email to be retrieved

    def dump(self):
        return 'protocol=[{}] address=[{}] port=[{}] account=[{}] passwd=[{}] encryption=[{}]'.format(self.protocol, self.address, self.port, self.accountname, self.passwd, self.encryption)

    def connect(self, prot, add, prt, acct, pwd, crypt=None):
        self.protocol = prot
        self.address = add
        self.port = prt
        self.encryption = crypt
        self.accountname = acct
        self.passwd = pwd
        self.server = None
        self.newEmails = 0      # List[] of new emails on server. Activated by connect()
        self.numEmails = 0      # Number of emails in list
        self.nextEmail = 0      # index into list of next email to be retrieved

        globs.log.write(1, 'EmailServer.Connect({})'.format(self.dump()))

        if self.protocol == 'pop3':
            globs.log.write(1,'Using POP3')
            try:
                if self.encryption is not None:
                    self.server = poplib.POP3_SSL(self.address,self.port)
                else:
                    self.server = poplib.POP3(self.address,self.port)
                retVal = self.server.user(self.accountname)
                globs.log.write(3,'Logged in. retVal={}'.format(retVal))
                retVal = self.server.pass_(self.passwd)
                globs.log.write(3,'Entered password. retVal={}'.format(retVal))
                return retVal.decode()
            except Exception:
                return None
        elif self.protocol == 'imap':
            globs.log.write(1,'Using IMAP')
            try:
                if self.encryption is not None:
                    self.server = imaplib.IMAP4_SSL(self.address,self.port)
                else:
                    self.server = imaplib.IMAP4(self.address,self.port)
                retVal, data = self.server.login(self.accountname, self.passwd)
                globs.log.write(3,'Logged in. retVal={} data={}'.format(retVal, data))
                return retVal
            except imaplib.IMAP4.error:
                return None
            except imaplib.socket.gaierror:
                return None
        elif self.protocol == 'smtp':
            globs.log.write(1,'Using SMTP')
            try:
                self.server = smtplib.SMTP('{}:{}'.format(self.address,self.port))
                if self.encryption is not None:   # Do we need to use SSL/TLS?
                    self.server.starttls()
                retVal, retMsg = self.server.login(self.accountname, self.passwd)
                globs.log.write(3,'Logged in. retVal={} retMsg={}'.format(retVal, retMsg))
                return retMsg.decode()
            except (smtplib.SMTPAuthenticationError, smtplib.SMTPConnectError, smtplib.SMTPSenderRefused):
                return None
        else:
            return None

    # Close email server connection
    def close(self):
        if self.protocol == 'pop3':
            self.server.quit()
        elif self.protocol == 'imap':
            self.server.close()
        elif self.protocol == 'smtp':
            self.server.quit()

        return None

    # Set the folder for retrieving incoming email.
    # Only useful for IMAP servers. POP3 doesn't use folders
    def setFolder(self, fname):
        globs.log.write(1,'setFolder({})'.format(fname))
        globs.log.write(3,'self.protocol=[{}]'.format(self.protocol))
        # Folder only valid on IMAP. Need a valid connection. Need a valid folder name. Handle pathological cases
        if ((self.protocol != 'imap') or (self.server is None) or (fname is None) or (fname == '')):
            return None
        retVal, data = self.server.select(fname)
        globs.log.write(3,'Setting folder. retVal={} data={}'.format(retVal, data))
        return retVal

    # Check if there are new messages waiting on the server
    # Return number of messages if there
    # Return None if empty
    def checkForMessages(self):
        if self.protocol == 'pop3':
            globs.log.write(1,'checkForMessages(POP3)')
            self.numEmails = len(self.server.list()[1])  # Get list of new emails
            globs.log.write(3,'Number of new emails: {}'.format(self.numEmails))
            if self.numEmails == 0:     # No new emails
                self.newEmails = None 
                self.nextEmail = 0
                return None
            self.newEmails = list(range(self.numEmails))
            self.nextEmail = 0
            return self.numEmails
        elif self.protocol == 'imap':
            globs.log.write(1,'checkForMessages(IMAP)')
            retVal, data = self.server.search(None, "ALL")
            globs.log.write(3,'Searching folder. retVal={} data={}'.format(retVal, data))
            if retVal != 'OK':          # No new emails
                self.newEmails = None
                self.numEmails = 0
                self.nextEmail = 0
                return None
            self.newEmails = list(data[0].split())   # Get list of new emails
            self.numEmails = len(self.newEmails)          
            self.nextEmail = 0
            return self.numEmails
        else:  # Invalid protocol
            return None
    
    # Retrieve next message from server
    # Returns body of message (type str) if more messages in queue
    # Returns None if no more messages
    def getNextMessage(self):
        globs.log.write(1, 'dremail.getNextMessage()')
        if self.newEmails == None:  # No new emails to get
            return None
        if self.nextEmail == self.numEmails: # Past last email on list
            return None
        if self.protocol == 'pop3':
            server_msg, body, octets = self.server.retr((self.newEmails[self.nextEmail])+1)
            globs.log.write(3, 'server_msg=[{}]  body=[{}]  octets=[{}]'.format(server_msg,body,octets))
            msgTmp=''
            for j in body:
                msgTmp += '{}\n'.format(j.decode("utf-8"))
            retMessage = email.message_from_string(msgTmp)  # Get message body
            self.nextEmail += 1
            return retMessage
        elif self.protocol == 'imap':
            retVal, data = self.server.fetch(self.newEmails[self.nextEmail],'(RFC822)') # Fetch message #num
            globs.log.write(3,'Server.fetch(): retVal=[{}] data=[{}]'.format(retVal,data))
            if retVal != 'OK':
                globs.log.write(1, 'ERROR getting message: {}'.format(self.nextEmail))
                return None
            globs.log.write(3,'data[0][1]=[{}]'.format(data[0][1]))
            retMessage = email.message_from_string(data[0][1].decode('utf-8'))  # Get message body
            globs.log.write(2, 'Next Message=[{}]'.format(retMessage))        
            self.nextEmail += 1
            return retMessage
        else:
            return None

    # Search for field in message
    # msgField - text to search against
    # regex - regex to search for
    # multiLine - 0=single line, 1=multi-line
    # type - 0=int or 1=string
    def searchMessagePart(self, msgField, regex, multiLine, typ):
        globs.log.write(1, 'EmailServer.searchMesagePart({}, {}, {}, {}'.format(msgField, regex, multiLine, typ))

        match = re.compile(regex, multiLine).search(msgField)  # Search msgField for regex match
        if match:  # Found a match - regex is in msgField
            if multiLine == 0:   # Single line result
                grpSplit =  match.group().split()  # Split matching text into "words"
                grpLen = len(grpSplit)
                retData = ''
                for num in range(1, len(grpSplit)):   # Loop through number of 'words' expeced
                    retData = retData + grpSplit[num]  # Add current 'word' to result
                    if (num < (grpLen - 1)):
                        retData = retData + ' '    # Add spaces between words, but not at the end
            else:    # Multi-line result
                retData = match.group()    # Group the multi-line data
                retData = re.sub(re.compile(r'\s+'), ' ', retData)  # Convert multiple white space to a single space
                retData = re.sub(re.compile(r'\"'), '\'', retData)  # Convert double quotes to single quotes
        else:  # Pattern not found
            if typ == 0:  # Integer field
                retData = '0'
            else:         # String field
                retData = ''

        return retData

    # Build SQL statement to put into the emails table
    def buildEmailSql(self, mParts, sParts, dParts):  

        globs.log.write(1, 'build_email_sql_statement(()')
        globs.log.write(2, 'messageId={}  sourceComp={}  destComp={}'.format(mParts['messageId'],mParts['sourceComp'],mParts['destComp']))

        sqlStmt = "INSERT INTO emails(messageId, sourceComp, destComp, emailTimestamp, \
            deletedFiles, deletedFolders, modifiedFiles, examinedFiles, \
            openedFiles, addedFiles, sizeOfModifiedFiles, sizeOfAddedFiles, sizeOfExaminedFiles, \
            sizeOfOpenedFiles, notProcessedFiles, addedFolders, tooLargeFiles, filesWithError, \
            modifiedFolders, modifiedSymlinks, addedSymlinks, deletedSymlinks, partialBackup, \
            dryRun, mainOperation, parsedResult, verboseOutput, verboseErrors, endTimestamp, \
            beginTimestamp, duration, messages, warnings, errors, dbSeen) \
            VALUES \
            ('{}', '{}', '{}', {}, {}, {}, {}, {}, {}, {}, {},{},{},{},{},{},{},{},{},{},{}, \
            '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', \"{}\", \"{}\", \"{}\", 1)".format(mParts['messageId'], \
            mParts['sourceComp'], mParts['destComp'], mParts['emailTimestamp'], sParts['deletedFiles'], \
            sParts['deletedFolders'], sParts['modifiedFiles'], sParts['examinedFiles'], sParts['openedFiles'], \
            sParts['addedFiles'], sParts['sizeOfModifiedFiles'], sParts['sizeOfAddedFiles'], sParts['sizeOfExaminedFiles'], sParts['sizeOfOpenedFiles'], \
            sParts['notProcessedFiles'], sParts['addedFolders'], sParts['tooLargeFiles'], sParts['filesWithError'], \
            sParts['modifiedFolders'], sParts['modifiedSymlinks'], sParts['addedSymlinks'], sParts['deletedSymlinks'], \
            sParts['partialBackup'], sParts['dryRun'], sParts['mainOperation'], sParts['parsedResult'], sParts['verboseOutput'], \
            sParts['verboseErrors'], dParts['endTimestamp'], dParts['beginTimestamp'], \
            sParts['duration'], sParts['messages'], sParts['warnings'], sParts['errors'])
                
        globs.log.write(3, 'sqlStmt=[{}]'.format(sqlStmt))
        return sqlStmt

    # Parse email message for relevant data useful by dupReport
    # Input is string with full message text
    # Returns msgParts{} (header info) and statusParts{} (Duplicati results)
    def processMessage(self, msg):

        globs.log.write(1,'EmailServer.process_message()')
    
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

        # Check all the vital parts to see if they're there
        # If any of these are missing it means:
        #   (1) they are not from Duplicati, and 
        #   (2) if we keep processing things will blow up down the line
        # To be safe, we'll just skip the message
        if msg['Message-Id'] is None or msg['Message-Id'] == '':
            globs.log.write(1,'No message-Id. Abandoning processMessage()')
            return None, None
        if msg['Subject'] is None or msg['Subject'] == '':
            globs.log.write(1,'No Subject. Abandoning processMessage()')
            return None, None
        if msg['Date'] is None or msg['Date'] == '':
            globs.log.write(1,'No Date. Abandoning processMessage()')
            return None, None

        # get Subject
        decode = email.header.decode_header(msg['Subject'])[0]
        msgParts['subject'] = decode[0]
        if (type(msgParts['subject']) is not str):  # Email encoded as a byte object - See Issue #14
            msgParts['subject'] = msgParts['subject'].decode('utf-8')
        globs.log.write(3, 'Subject=[{}]'.format(msgParts['subject']))

        # See if it's a message of interest
        # Match subject field against 'subjectregex' parameter from RC file (Default: 'Duplicati Backup report for...')
        if re.search(globs.opts['subjectregex'], msgParts['subject']) == None:
            globs.log.write(1, 'Message [{}] is not a Message of Interest. Skipping message.'.format(msg['Message-Id']))
            return None, None    # Not a message of Interest

        # Last chance to kick out bad messages
        # Get source & desination computers from email subject
        srcRegex = '{}{}'.format(globs.opts['srcregex'], re.escape(globs.opts['srcdestdelimiter']))
        destRegex = '{}{}'.format(re.escape(globs.opts['srcdestdelimiter']), globs.opts['destregex'])
        globs.log.write(3,'srcregex=[{}]  destRegex=[{}]'.format(srcRegex, destRegex))
        # Does the Subject have a proper source/destination pair?
        partsSrc = re.search(srcRegex, msgParts['subject'])
        partsDest = re.search(destRegex, msgParts['subject'])
        if (partsSrc is None) or (partsDest is None):    # Correct subject but delimeter not found. Something is wrong.
            globs.log.write(2,'srcdestdelimiter [{}] not found in subject. Skipping message.'.format(globs.opts['srcdestdelimiter']))
            return None, None
        
        # Get Message ID
        globs.log.write(3,'msg[Message-Id]=[{}]'.format(msg['Message-Id']))
        msgParts['messageId'] = email.header.decode_header(msg['Message-Id'])[0][0]
        globs.log.write(3,'msgParts[messageId]=[{}]'.format(msgParts['messageId']))
        if (type(msgParts['messageId']) is not str):  # Email encoded as a byte object - See Issue #14
            msgParts['messageId'] = msgParts['messageId'].decode('utf-8')
            globs.log.write(3, 'Revised messageId=[{}]'.format(msgParts['messageId']))

        # See if the record is already in the database, meaning we've seen it before
        if globs.db.searchForMessage(msgParts['messageId']):    # Message is already in database
            # Mark the email as being seen in the database
            globs.db.execSqlStmt('UPDATE emails SET dbSeen = 1 WHERE messageId = \"{}\"'.format(msgParts['messageId']))
            globs.db.dbCommit()
            return None, None

        # Message not yet in database. Proceed.
        globs.log.write(1, 'Message ID [{}] does not exist. Adding to DB'.format(msgParts['messageId']))

        dTup = email.utils.parsedate_tz(msg['Date'])
        if dTup:
            # See if there's timezone info in the email header data. May be 'None' if no TZ info in the date line
            # TZ info is represented by seconds offset from UTC
            # We don't need to adjust the email date for TimeZone info now, since date line in email already accounts for TZ.
            # All other calls to toTimestamp() should include timezone info
            msgParts['timezone'] = dTup[9]

            # Set date into a parseable string
            # It doesn't matter what date/time format we pass in (as long as it's valid)
            # When it comes back out, it'll be parsed into the user-defined format from the .rc file
            # For now, we'll use YYYY/MM/DD HH:MM:SS
            xDate = '{:04d}/{:02d}/{:02d} {:02d}:{:02d}:{:02d}'.format(dTup[0], dTup[1], dTup[2], dTup[3], dTup[4], dTup[5])  
            dtTimStmp = drdatetime.toTimestamp(xDate, dfmt='YYYY/MM/DD', tfmt='HH:MM:SS')  # Convert the string into a timestamp
            msgParts['emailTimestamp'] = dtTimStmp
            globs.log.write(3, 'emailDate=[{}]-[{}]'.format(dtTimStmp, drdatetime.fromTimestamp(dtTimStmp)))

        msgParts['sourceComp'] = re.search(srcRegex, msgParts['subject']).group().split(globs.opts['srcdestdelimiter'])[0]
        msgParts['destComp'] = re.search(destRegex, msgParts['subject']).group().split(globs.opts['srcdestdelimiter'])[1]
        globs.log.write(3, 'sourceComp=[{}] destComp=[{}] emailTimestamp=[{}] subject=[{}]'.format(msgParts['sourceComp'], \
            msgParts['destComp'], msgParts['emailTimestamp'], msgParts['subject']))

        # Search for source/destination pair in database. Add if not already there
        retVal = globs.db.searchSrcDestPair(msgParts['sourceComp'], msgParts['destComp'])    

        # Extract the body (payload) from the email
        msgParts['body'] = msg.get_payload()
        globs.log.write(3, 'Body=[{}]'.format(msgParts['body']))

        # Go through each element in lineParts{}, get the value from the body, and assign it to the corresponding element in statusParts{}
        for section,regex,flag,typ in lineParts:
            statusParts[section] = self.searchMessagePart(msgParts['body'], regex, flag, typ) # Get the field parts

        # Adjust fields if not a clean run
        globs.log.write(3, "statusParts['failed']=[{}]".format(statusParts['failed']))
        if statusParts['failed'] == '':  # Looks like a good run
            # See if there's a timestamp (xxxx.xxxx) already in the EndTime field
            # If so, use that, else calculate timestamp
            pat = re.compile('\(.*\)')

            match = re.search(pat, statusParts['endTimeStr'])
            if match:  # Timestamp found in line
                dateParts['endTimestamp'] = statusParts['endTimeStr'][match.regs[0][0]+1:match.regs[0][1]-1]
            else:  # No timestamp found. Calculate timestamp
                #dt, tm = drdatetime.getDateTimeFmt(msgParts['sourceComp'], msgParts['destComp'])
                dt, tm = globs.optionManager.getRcSectionDateTimeFmt(msgParts['sourceComp'], msgParts['destComp'])
                dateParts['endTimestamp'] = drdatetime.toTimestamp(statusParts['endTimeStr'], dfmt=dt, tfmt=tm, utcOffset=msgParts['timezone'])

            match = re.search(pat, statusParts['beginTimeStr'])
            if match:  # Timestamp found in line
                dateParts['beginTimestamp'] = statusParts['beginTimeStr'][match.regs[0][0]+1:match.regs[0][1]-1]
            else:  # No timestamp found. Calculate timestamp
                dateParts['beginTimestamp'] = drdatetime.toTimestamp(statusParts['beginTimeStr'], utcOffset=msgParts['timezone'])
        else:  # Something went wrong. Let's gather the details.
            statusParts['errors'] = statusParts['failed']
            statusParts['parsedResult'] = 'Failure'
            statusParts['warnings'] = statusParts['details']
            globs.log.write(2, 'Errors=[{}]'.format(statusParts['errors']))
            globs.log.write(2, 'Warnings=[{}]'.format(statusParts['warnings']))

            # Since the backup job report never ran, we'll use the email date/time as the report date/time
            dateParts['endTimestamp'] = msgParts['emailTimestamp']
            dateParts['beginTimestamp'] = msgParts['emailTimestamp']
            globs.log.write(3, 'Failure message. Replaced date/time: end=[{}]  begin=[{}]'.format(dateParts['endTimestamp'], dateParts['beginTimestamp'])), 

        # Replace commas (,) with newlines (\n) in message fields. Sqlite really doesn't like commas in SQL statements!
        for part in ['messages', 'warnings', 'errors']:
            if statusParts[part] != '':
                    statusParts[part] = statusParts[part].replace(',','\n')

        # If we're just collecting and get a warning/error, we may need to send an email to the admin
        if (globs.opts['collect'] is True) and (globs.opts['warnoncollect'] is True) and ((statusParts['warnings'] != '') or (statusParts['errors'] != '')):
            errMsg = 'Duplicati error(s) on backup job\n'
            errMsg += 'Message ID {} on {}\n'.format(msgParts['messageId'], msg['date'])
            errMsg += 'Subject: {}\n\n'.format(msgParts['subject'])
            if statusParts['warnings'] != '':
                errMsg += 'Warnings:' + statusParts['warnings'] + '\n\n'
            if statusParts['errors'] != '':
                errMsg += 'Errors:' + statusParts['warnings'] + '\n\n'

            globs.outServer.sendErrorEmail(errMsg)

        globs.log.write(3, 'endTimeStamp=[{}] beginTimeStamp=[{}]'.format(drdatetime.fromTimestamp(dateParts['endTimestamp']), drdatetime.fromTimestamp(dateParts['beginTimestamp'])))
            
        sqlStmt = self.buildEmailSql(msgParts, statusParts, dateParts)
        globs.db.execSqlStmt(sqlStmt)
        globs.db.dbCommit()

        return msgParts, statusParts

    # Send final email result
    def sendEmail(self, msgHtml, msgText = None, subject = None, sender = None, receiver = None):
        globs.log.write(2, 'sendEmail(msgHtml={}, msgText={}, subject={}, sender={}, receiver={})'.format(msgHtml, msgText, subject, sender, receiver))

        # Build email message
        msg = MIMEMultipart('alternative')

        if subject is None:
            subject = globs.report.reportOpts['reporttitle']
        msg['Subject'] = subject

        if sender is None:
            sender = globs.opts['outsender']
        msg['From'] = sender

        if receiver is None:
            receiver = globs.opts['outreceiver']
        msg['To'] = receiver

        # Record the MIME types of both parts - text/plain and text/html.
        # Attach parts into message container.
        # According to RFC 2046, the last part of a multipart message is best and preferred.
        # So attach text first, then HTML
        if msgText is not None:
            msgPart = MIMEText(msgText, 'plain')
            msg.attach(msgPart)
        if msgHtml is not None:
            msgPart = MIMEText(msgHtml, 'html')
            msg.attach(msgPart)

        # Send the message via local SMTP server.
        # The encode('utf-8') was added to deal with non-english character sets in emails. See Issue #26 for details
        self.server.sendmail(sender, receiver, msg.as_string().encode('utf-8'))

    # Send email for errors
    def sendErrorEmail(self, errText):
        globs.log.write(2, 'sendErrorEmail()')

        # Build email message
        msg = MIMEMultipart('alternative')
        msg['Subject'] = 'Duplicati Job Status Error'
        msg['From'] = globs.opts['outsender']
        msg['To'] = globs.opts['outreceiver']

        # Record the MIME type. Only need text type
        msgPart = MIMEText(errText, 'plain')
        msg.attach(msgPart)

        # Send the message via local SMTP server.
        # The encode('utf-8') was added to deal with non-english character sets in emails. See Issue #26 for details
        self.server.sendmail(globs.opts['outsender'], globs.opts['outreceiver'], msg.as_string().encode('utf-8'))

