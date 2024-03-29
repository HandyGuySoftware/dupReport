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
import quopri
import base64
import re
import datetime
import time
import smtplib
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import json
import ssl
import sys

# Import dupReport modules
import globs
import drdatetime
import report


#Define message segments (line parts) for Duplicati result email messages
# lineParts[] are the individual line items in the Duplicati status email report.
#
#   [0]internal name        [1] Duplicati email string      [2]regex flags (0 = none)   [3]field Type (0=int or 1=str)  [4] JSON field name
lineParts = [
    ('deletedFiles',        r'DeletedFiles: \d+',            0,                          0,                              'DeletedFiles'),
    ('deletedFolders',      r'DeletedFolders: \d+',          0,                          0,                              'DeletedFolders'),
    ('modifiedFiles',       r'ModifiedFiles: \d+',           0,                          0,                              'ModifiedFiles'),
    ('examinedFiles',       r'ExaminedFiles: \d+',           0,                          0,                              'ExaminedFiles'),
    ('openedFiles',         r'OpenedFiles: \d+',             0,                          0,                              'OpenedFiles'),
    ('addedFiles',          r'AddedFiles: \d+',              0,                          0,                              'AddedFiles'),
    ('sizeOfModifiedFiles', r'SizeOfModifiedFiles: .*',      0,                          0,                              'SizeOfModifiedFiles'),
    ('sizeOfAddedFiles',    r'SizeOfAddedFiles: .*',         0,                          0,                              'SizeOfAddedFiles'),
    ('sizeOfExaminedFiles', r'SizeOfExaminedFiles: .*',      0,                          0,                              'SizeOfExaminedFiles'),
    ('sizeOfOpenedFiles',   r'SizeOfOpenedFiles: .*',        0,                          0,                              'SizeOfOpenedFiles'),
    ('notProcessedFiles',   r'NotProcessedFiles: \d+',       0,                          0,                              'NotProcessedFiles'),
    ('addedFolders',        r'AddedFolders: \d+',            0,                          0,                              'AddedFolders'),
    ('tooLargeFiles',       r'TooLargeFiles: \d+',           0,                          0,                              'TooLargeFiles'),
    ('filesWithError',      r'FilesWithError: \d+',          0,                          0,                              'FilesWithError'),
    ('modifiedFolders',     r'ModifiedFolders: \d+',         0,                          0,                              'ModifiedFolders'),
    ('modifiedSymlinks',    r'ModifiedSymlinks: \d+',        0,                          0,                              'ModifiedSymlinks'),
    ('addedSymlinks',       r'AddedSymlinks: \d+',           0,                          0,                              'AddedSymlinks'),
    ('deletedSymlinks',     r'DeletedSymlinks: \d+',         0,                          0,                              'DeletedSymlinks'),
    ('bytesUploaded',       r'BytesUploaded: .*',            0,                          0,                              'BytesUploaded'),
    ('bytesDownloaded',     r'BytesDownloaded: .*',          0,                          0,                              'BytesDownloaded'),
    ('partialBackup',       r'PartialBackup: \w+',           0,                          1,                              'PartialBackup'),
    ('dryRun',              r'Dryrun: \w+',                  0,                          1,                              'Dryrun'),
    ('mainOperation',       r'MainOperation: \w+',           0,                          1,                              'MainOperation'),
    ('parsedResult',        r'ParsedResult: \w+',            0,                          1,                              'ParsedResult'),
    ('verboseOutput',       r'VerboseOutput: \w+',           0,                          1,                              ''),                        # No JSON equivalent
    ('verboseErrors',       r'VerboseErrors: \w+',           0,                          1,                              ''),                        # No JSON equivalent
    ('endTimeStr',          r'EndTime: .*',                  0,                          1,                              'EndTime'),
    ('beginTimeStr',        r'BeginTime: .*',                0,                          1,                              'BeginTime'),
    ('dupversion',          r'Version: .*',                  0,                          1,                              'Version'),
    ('messages',            r'Messages: \[.*^\]',            re.MULTILINE|re.DOTALL,     1,                              ''),                        # No JSON equivalent
    ('warnings',            r'Warnings: \[.*^\]',            re.MULTILINE|re.DOTALL,     1,                              ''),                        # No JSON equivalent
    ('errors',              r'Errors: \[.*^\]',              re.MULTILINE|re.DOTALL,     1,                              ''),                        # No JSON equivalent
    ('limitedMessages',     r'LimitedMessages: \[.*^\]',     re.MULTILINE|re.DOTALL,     1,                              ''),                        # No JSON equivalent
    ('limitedWarnings',     r'LimitedWarnings: \[.*^\]',     re.MULTILINE|re.DOTALL,     1,                              ''),                        # No JSON equivalent
    ('limitedErrors',       r'LimitedErrors: \[.*^\]',       re.MULTILINE|re.DOTALL,     1,                              ''),                        # No JSON equivalent
    ('logdata',             r'Log data:(.*?)\n(.*?)(?=\Z)',  re.MULTILINE|re.DOTALL,     1,                              'LogLines'),
    ('details',             r'Details: .*',                  re.MULTILINE|re.DOTALL,     1,                              ''),                        # No JSON equivalent
    ('failed',              r'Failed: .*',                   re.MULTILINE|re.DOTALL,     1,                              ''),                        # No JSON equivalent
    ]

serverRcParts = {
    'imap': ['protocol', 'server', 'port', 'encryption', 'account', 'password', 'keepalive', 'folder', 'unreadonly', 'markread', 'authentication'],
    'pop3': ['protocol', 'server', 'port', 'encryption', 'account', 'password', 'keepalive', 'authentication'],
    'smtp': ['protocol', 'server', 'port', 'encryption', 'account', 'password', 'keepalive', 'sender', 'sendername', 'receiver', 'authentication']
    }

class EmailManager:
    def __init__(self):
        globs.log.write(globs.SEV_NOTICE, function='EmailManager', action='Init', msg='Initializing Email Manager.')

        self.incoming = {}  # Dictionary of incoming email servers. Order of elements is unimportant
        self.outgoing = []  # List of outgoing SMTP servers. Need to save elements in order specified.

        validList = True
        serverlist = [x.strip() for x in globs.opts['emailservers'].split(',')]
        for server in serverlist:
            isValid, options = self.validateServerOptions(server)
            if isValid:
                if options['protocol'] in ['imap', 'pop3']:
                    self.incoming[server] =  EmailServer(server, options)
                else: # Smtp
                    # Before you go blindly opening up an outgoing connection....
                    # We don't need to open an outbound (smtp) email server if we're not sending email
                    # But... you'll need one for Apprise support if you're using Apprise to notify you through email.
                    # Thus, you may not want to also send redundant emails through dupReport.
                    # However, if you haven't supressed backup warnings (i.e., -w), you'll still need an outgoing server connection
                    # So, basically, if you've suppressed BOTH backup warnings AND outgoing email, skip opening the outgoing server
                    # If EITHER of these is false (i.e., you want either of these to work), open the server connection
                    if not globs.opts['stopbackupwarn'] or not globs.opts['nomail']:
                        self.outgoing.append(EmailServer(server, options))
            else:
                isValid = False

        if len(self.incoming) == 0:
            globs.log.write(globs.SEV_NOTICE, function='EmailManager', action='Init', msg='No incoming email server(s) specified.')
            isValid = False
        if len(self.outgoing) == 0:
            globs.log.write(globs.SEV_NOTICE, function='EmailManager', action='Init', msg='No outgoing email server(s) specified.')
            isValid = False

        if not isValid:
            globs.closeEverythingAndExit(1)

        return None

    # Return the first available outgoing SMTP server
    def getSmtpServer(self):
        globs.log.write(globs.SEV_NOTICE, function='EmailManager', action='getSmtpServer', msg='Looking for outgoing SMTP server.')
        for i in range(len(self.outgoing)):
            self.outgoing[i].connect()
            if self.outgoing[i].available == True:
                return self.outgoing[i]

        globs.log.write(globs.SEV_NOTICE, function='EmailManager', action='getSmtpServer', msg='Unable to find any available outgoing SMTP servers.')
        return None

    def checkForNewMessages(self):
        globs.log.write(globs.SEV_NOTICE, function='EmailManager', action='checkForNewMessages', msg='Checking inbound servers for new email messages.')
        for server in self.incoming:
            # Get new messages on server
            progCount = 0   # Count for progress indicator
            newMessages = self.incoming[server].checkForMessages()
            globs.log.write(globs.SEV_NOTICE, function='EmailManager', action='checkForNewMessages', msg='Found {} new messages on server {}'.format(newMessages, self.incoming[server].options['server']))
            if newMessages > 0:
                nxtMsg = self.incoming[server].processNextMessage()
                while nxtMsg is not None:
                    if globs.opts['showprogress'] > 0:
                        progCount += 1
                        if (progCount % globs.opts['showprogress']) == 0:
                            globs.log.out('.', newline = False)
                    nxtMsg = self.incoming[server].processNextMessage()
                if globs.opts['showprogress'] > 0:
                    globs.log.out(' ')   # Add newline at end.

                # Do we want to mark messages as 'read/seen'? (Only works for IMAP)
                if self.incoming[server].options['protocol'] == 'imap':
                    if self.incoming[server].options['markread'] is True:
                        self.incoming[server].markMessagesRead()
        return

    def sendEmail(self, **kwargs):
        svr = self.getSmtpServer()

        # Issue #169. program would crash if no valid SMTP server was connected (probably because of bad login credentials).
        # If so, just quietly log the message and return.
        if svr is None:
            globs.log.write(globs.SEV_NOTICE, function='EmailManager', action='sendEmail', msg="Can't send outgoing email. No valid SMTP server connected. Check logs for connection problems.")
        else:
            self.getSmtpServer().sendEmail(**kwargs)

    # Validate the .rc file options for an email server
    # Return true/false if options are valid and list of options
    def validateServerOptions(self, server):
        globs.log.write(globs.SEV_NOTICE, function='EmailManager', action='validateServerOptions', msg='Validating .rc file options for server {}'.format(server))

        options = {}
        isValid = True
        rcOptions = globs.optionManager.getRcSection(server)

        # Make sure there is a valid protocol field in the spec. Without this, all else is useless
        if rcOptions is None:
            globs.log.write(globs.SEV_NOTICE, function='EmailManager', action='validateServerOptions', msg='No specification found in .rc file for email server \'{}\''.format(server))
            isValid = False
        elif 'protocol' not in rcOptions:
            globs.log.write(globs.SEV_NOTICE, function='EmailManager', action='validateServerOptions', msg='No protocol specified for server \'{}\''.format(server))
            isValid = False
        elif rcOptions['protocol'] not in ['imap', 'pop3', 'smtp']:
            globs.log.write(globs.SEV_NOTICE, function='EmailManager', action='validateServerOptions', msg='Invalid protocol \'{}\' specified for email server \'{}\''.format(rcOptions['protocol'], server))
            isValid = False

        if not isValid:
            return isValid, None

        # Looking good. Now loop through required options to see if any are missing
        for option in serverRcParts[rcOptions['protocol']]:
            if option not in rcOptions:
                globs.log.write(globs.SEV_NOTICE, function='EmailManager', action='validateServerOptions', msg='Required option \'{}\' not found in defintion of email server \'{}\''.format(option, server))
                isValid = False
            else:
                if option in ['port']: # Int conversion
                    options[option] = int(rcOptions[option])
                elif option in ['keepalive', 'unreadonly', 'markread']: # Bool conversion
                    options[option] = rcOptions[option].lower() in ('true')
                else: # String value
                    options[option] = rcOptions[option]

        return isValid, options

class EmailServer:
    def __init__(self, serverName, optionList):
        globs.log.write(globs.SEV_DEBUG, function='EmailServer', action='init', msg='Initializing email server \'{}\''.format(serverName))

        self.options = optionList
        self.name = serverName
        self.serverconnect = None
        self.newEmails = 0      # List[] of new emails on server. Activated by connect()
        self.numEmails = 0      # Number of emails in list
        self.nextEmail = 0      # index into list of next email to be retrieved
        self.available = False  # Set to True if able to make a connection
        globs.log.write(globs.SEV_DEBUG, function='EmailServer', action='init', msg='Email server \'{}\' initialized'.format(serverName))
        return None

    def connect(self):
        globs.log.write(globs.SEV_NOTICE, function='EmailServer', action='connect', msg='Connecting to email server \'{}\''.format(self.options['server']))
        globs.log.write(globs.SEV_DEBUG, function='EmailServer', action='connect', msg='serverconnect=[{}] keepalive=[{}]'.format(self.serverconnect, self.options['keepalive']))

        # See if a server connection is already established (self.serverconnect != None)
        # This is the most common case, so check this first
        if self.serverconnect != None:
            if not self.options['keepalive']: # Do we care about keepalives?
                return None

            globs.log.write(globs.SEV_DEBUG, function='EmailServer', action='connect:KeepAlive', msg='Checking existing server connection using {}'.format(self.options['protocol']))
            if self.options['protocol'] == 'imap':
                try:
                    status = self.serverconnect.noop()[0]
                except:
                    e = sys.exc_info()[0]
                    globs.log.write(globs.SEV_ERROR, function='EmailServer', action='connect:Imap', msg='IMAP noop() Error: {}'.format(e))
                    status = 'NO'
                if status != 'OK':
                    globs.log.write(globs.SEV_DEBUG, function='EmailServer', action='connect:Imap', msg='Server {} timed out. Reconnecting.'.format(self.options['server']))
                    self.serverconnect = None
                    self.available = False
                    self.connect()
            elif self.options['protocol'] == 'pop3':
                try:
                    status = self.serverconnect.noop()
                except:
                    e = sys.exc_info()[0]
                    globs.log.write(globs.SEV_ERROR, function='EmailServer', action='connect:Pop3', msg='POP3 noop() Error: {}'.format(e))
                    status = '+NO'
                if status.decode() != '+OK':        # Stats from POP3 returned as byte string. Need to decode before compare (Issue #107)
                    globs.log.write(globs.SEV_NOTICE, function='EmailServer', action='connect:Pop3', msg='Server {} timed out. Reconnecting.'.format(self.options['server']))
                    self.serverconnect = None
                    self.available = False
                    self.connect()
            elif self.options['protocol'] == 'smtp':
                try:
                    status = self.serverconnect.noop()[0]
                except:  # smtplib.SMTPServerDisconnected
                    e = sys.exc_info()[0]
                    globs.log.write(globs.SEV_ERROR, function='EmailServer', action='connect:Smtp', msg='SMTP noop() Error: {}'.format(e))
                    status = -1
                if status != 250: # Disconnected. Need to reconnect to server
                    globs.log.write(globs.SEV_DEBUG, function='EmailServer', action='connect:Smtp', msg='Server {} timed out. Reconnecting.'.format(self.options['server']))
                    self.serverconnect = None
                    self.available = False
                    self.connect()
        else:     # self.serverconnect == None. Never connected, need to establish server connection
            globs.log.write(globs.SEV_DEBUG, function='EmailServer', action='connect:Init', msg='Initiating new server connection using {}'.format(self.options['protocol']))
            if self.options['protocol'] == 'imap':
                try:
                    if self.options['encryption'] != 'none':
                        self.serverconnect = imaplib.IMAP4_SSL(self.options['server'],self.options['port'])
                    else:
                        self.serverconnect = imaplib.IMAP4(self.options['server'],self.options['port'])
                    retVal, data = self.serverconnect.login(self.options['account'], self.options['password'])
                    globs.log.write(globs.SEV_DEBUG, function='EmailServer', action='connectInit', msg='IMAP Logged in. retVal=[{}] data=[{}]'.format(retVal, globs.maskData(data)))
                    retVal, data = self.serverconnect.select(self.options['folder'])
                    globs.log.write(globs.SEV_DEBUG,function='EmailServer', action='connect:Imap', msg='Setting IMAP folder. retVal=[{}] data=[{}]'.format(retVal, data))
                    self.available = True
                    return retVal
                except:
                    e = sys.exc_info()[0]
                    globs.log.write(globs.SEV_ERROR, function='EmailServer', action='connect:Imap', msg='IMAP connection Error: {}'.format(e))
                    self.available = False
                    return None
            elif self.options['protocol'] == 'pop3':
                try:
                    if self.options['encryption'] != 'none':
                        self.serverconnect = poplib.POP3_SSL(self.options['server'],self.options['port'])
                    else:
                        self.serverconnect = poplib.POP3(self.options['server'],self.options['port'])
                    retVal = self.serverconnect.user(self.options['account'])
                    globs.log.write(globs.SEV_DEBUG, function='EmailServer', action='connect:Pop3', msg='POP3 Logged in. retVal=[{}]'.format(retVal))
                    retVal = self.serverconnect.pass_(self.options['password'])
                    globs.log.write(globs.SEV_DEBUG, function='EmailServer', action='connect:Pop3', msg='Entered password. retVal={}'.format(retVal))
                    self.available = True
                    return retVal.decode()
                except:
                    e = sys.exc_info()[0]
                    globs.log.write(globs.SEV_ERROR, function='EmailServer', action='connect:Pop3', msg='POP3 connection Error: {}'.format(e))
                    self.available = False
                    return None
            elif self.options['protocol'] == 'smtp':
                try:
                    globs.log.write(globs.SEV_DEBUG, function='EmailServer', action='connect:Smtp', msg='Initializing SMPT Object for address=[{}] port=[{}]'.format(self.options['server'],self.options['port']))
                    self.serverconnect = smtplib.SMTP(self.options['server'],self.options['port'])
                    globs.log.write(globs.SEV_DEBUG, function='EmailServer', action='connect:Smtp', msg='SMPT serverconnect object=[{}]'.format(self.serverconnect))
                    if self.options['encryption'] != 'none':   # Do we need to use SSL/TLS?
                        globs.log.write(globs.SEV_DEBUG, function='EmailServer', action='connect:Smtp', msg='Starting TLS')
                        try:
                            tlsContext = ssl.create_default_context()
                            self.serverconnect.starttls(context=tlsContext)
                        except Exception as e:
                            globs.log.write(globs.SEV_NOTICE, function='EmailServer', action='connect:Smtp', msg='SMTP TLS Exception: [{}]'.format(e))
                    try:
                        globs.log.write(globs.SEV_DEBUG, function='EmailServer', action='connect:Smtp', msg='Logging into server.')
                        retVal, retMsg = self.serverconnect.login(self.options['account'], self.options['password'])
                        globs.log.write(globs.SEV_DEBUG, function='EmailServer', action='connect:Smtp', msg='Logged in. retVal=[{}] retMsg=[{}]'.format(retVal, retMsg))
                        self.available = True
                        return retMsg.decode()
                    except:
                        e = sys.exc_info()[0]
                        globs.log.write(globs.SEV_ERROR,  function='EmailServer', action='connect:Smtp', msg='SMTP login Error: {}'.format(e))
                        self.available = False
                except (smtplib.SMTPAuthenticationError, smtplib.SMTPConnectError, smtplib.SMTPSenderRefused):
                    e = sys.exc_info()[0]
                    globs.log.write(globs.SEV_ERROR,  function='EmailServer', action='connect:Smtp', msg='SMTP connection Error: {}'.format(e))
                    self.available = False
                    return None
            else:   # Bad protocol specification
                globs.log.write(globs.SEV_NOTICE, function='EmailServer', action='connect', msg='Invalid protocol specification: {}. Aborting program.'.format(self.options['protocol']))
                globs.closeEverythingAndExit(1)
                return None
        return None

    # Close email server connection
    def close(self):
        globs.log.write(globs.SEV_NOTICE, function='EmailServer', action='close', msg='Closing connection to {}.'.format(self.options['server']))
        # If self.serverconnect == None, nothing left to close
        if self.serverconnect != None:
            if self.options['protocol'] in ['pop3', 'smtp']:
                self.serverconnect.quit()
            else: #IMAP
                self.serverconnect.close()
        return None

    # Check if there are new messages waiting on the server
    # Return number of messages if there (or 0 if none)
    # Return None if empty
    def checkForMessages(self):
        globs.log.write(globs.SEV_NOTICE, function='EmailServer', action='checkForMessages', msg='Checking for messages on server {}. Protocol={}'.format(self.options['server'], self.options['protocol']))
        self.connect()
        if not self.available:
            globs.log.write(globs.SEV_NOTICE, function='EmailServer', action='checkForMessages', msg='Server {} marked as \'unavailable\''.format(self.options['server']))
            return 0

        if self.options['protocol'] == 'pop3':
            self.numEmails = len(self.serverconnect.list()[1])  # Get list of new emails
            if self.numEmails == 0:     # No new emails
                self.newEmails = None
                self.nextEmail = 0
                return 0
            self.newEmails = list(range(self.numEmails))
            self.nextEmail = -1     # processNextMessage() pre-increments message index. Initializing to -1 ensures the pre-increment start at 0
            return self.numEmails
        elif self.options['protocol'] == 'imap':
            # Issue #124 - only read unseen/unread messages. Speed up input processing.
            scope = '(UNSEEN)' if self.options['unreadonly'] == True else 'ALL'
            retVal, data = self.serverconnect.search(None, scope)
            globs.log.write(globs.SEV_DEBUG, function='EmailServer', action='checkForMessagesImap', msg='Searching folder. retVal=[{}] data=[{}]'.format(retVal, data))
            if retVal != 'OK':          # No new emails
                self.newEmails = None
                self.numEmails = 0
                self.nextEmail = 0
                return 0
            self.newEmails = list(data[0].split())   # Get list of new emails
            self.numEmails = len(self.newEmails)
            self.nextEmail = -1     # processNextMessage() pre-increments message index. Initializing to -1 ensures the pre-increment start at 0
            return self.numEmails
        else:  # Invalid protocol
            return 0

    # Extract a (parentheses) field or raw data from the result
    # Some fields (sizes, date, time) can be presented in text or numeric values (Starting with Canary builds in Jan 2018)
    # Examples: EndTime: 1/24/2018 10:01:45 PM (1516852905)
    #           SizeOfAddedFiles: 10.12 KB (10364)
    #           SizeOfExaminedFiles: 44.42 GB (47695243956)
    # This function will return the value in parentheses (if it exists) or the raw info (if it does not)
    # Inputs: val = value to parse, dt = date format string, tf = time format string
    def parenOrRaw(self, val, df = None, tf = None, tz = None):
        globs.log.write(globs.SEV_DEBUG, function='EmailServer', action='parenOrRaw', msg='Extracting actual value from {}'.format(val))
        retval = val    # Set default return as input value
        # Search for '(XXX)' in value
        # Modified in 3.0.7 by @ekutner
        pat = re.compile(r'\([^\)]*\)')
        match = re.search(pat, val)
        if match:  # value found in parentheses
            retval = val[match.regs[0][0]+1:match.regs[0][1]-1]
        else:  # No parens found
            if df != None:  # Looking for date/time
                retval = drdatetime.toTimestamp(val, dfmt=df, tfmt=tf, utcOffset=tz)

        globs.log.write(globs.SEV_DEBUG, function='EmailServer', action='parenOrRaw', msg='Retrieved [{}]'.format(retval))
        return retval

    # Issue 105
    # POP3 manages headers different than IMAP
    # Need to transform POP3 headers into IMAP style so the rest of the program
    # Can process them properly
    # Please, in the name of all that is holy, stop using POP3!!!
    def mergePop3Headers(self, hdrBody):
        globs.log.write(globs.SEV_DEBUG, function='EmailServer', action='mergePop3Headers', msg='Merging POP3 headers for [{}]'.format(hdrBody))
        hdrLine = ""
        for nxtHdr in hdrBody:
            hdrLine += nxtHdr.decode('utf-8') + "\r\n"
        globs.log.write(globs.SEV_DEBUG, function='EmailServer', action='mergePop3Headers', msg='POP3 headers merged: [{}]'.format(hdrLine))
        return hdrLine

    # Extract specific fields from an email header
    # Different email servers create email headers diffrently
    # Also, fields like Subject can be split across multiple lines
    # Our mission is to sort it all out
    # Return date, subject, message-id
    def extractHeaders(self, hdrs):
        globs.log.write(globs.SEV_NOTICE, function='EmailServer', action='extractHeaders', msg='Extracting headers from ({})'.format(hdrs))
        hdrFields={}                            # Dictionary to hold the header fields we found
        splitlines = hdrs.split("\r\n")         # Split header into separate lines
        for line in splitlines:
            if line == "":                      # Some lines are just \r\n
                continue
            sections = line.split(':',1)                # Look for the FIRST colon. Protects against the subject having a colon in it (Issue #104)
            if len(sections) == 1:                      # No header field. This is a continuation of the last header line
                hdrFields[lastHeader] += sections[0]    # Just concatenate this line to the next one
            else:
                hdrFields[sections[0].lower()] = sections[1].lstrip().rstrip()  # Add field to hdrFields dictionary
                lastHeader = sections[0].lower()                                # Remember this header, in case the next line is a continuation

        if 'content-transfer-encoding' not in hdrFields:
            globs.log.write(globs.SEV_DEBUG, function='EmailServer', action='extractHeaders', msg='No \'content-transfer-encoding\' header. Defaulting to \'\'.')
            hdrFields['content-transfer-encoding'] = ''

        globs.log.write(globs.SEV_NOTICE, function='EmailServer', action='extractHeaders', msg='Header fields extracted: [{}]'.format(hdrFields))
        return hdrFields['date'], hdrFields['subject'], hdrFields['message-id'], hdrFields['content-transfer-encoding']

    # Retrieve and process next message from server
    # Returns <Message-ID> or '<INVALID>' if there are more messages in queue, even if this message was unusable
    # Returns None if no more messages
    def processNextMessage(self):
        globs.log.write(globs.SEV_NOTICE, function='EmailServer', action='processNextMessage', msg='Processing next message on server {}. Protocol={}'.format(self.options['server'], self.options['protocol']))
        self.connect()

        # Increment message counter to the next message.
        # Skip for message #0 because we haven't read any messages yet
        self.nextEmail += 1

        emailParts = {
            'header': {},
            'body': {}
            }

        # Check no-more-mail conditions. Either no new emails to get or gone past the last email on list
        if (self.newEmails == None) or (self.nextEmail == self.numEmails):
            return None

        if self.options['protocol'] == 'pop3':
            # Get message header
            server_msg, body, octets = self.serverconnect.top((self.newEmails[self.nextEmail])+1,0)
            globs.log.write(globs.SEV_DEBUG, function='EmailServer', action='processNextMessage', msg='server_msg=[{}]  body=[{}]  octets=[{}]'.format(server_msg,body,octets))
            if server_msg[:3].decode() != '+OK':
                globs.log.write(globs.SEV_ERROR,  function='EmailServer', action='processNextMessage', msg='ERROR getting message {}'.format(self.nextEmail))
                return '<INVALID>'
            # Get date, subject, and message ID from headers
            hdrLine = self.mergePop3Headers(body)       # Convert to IMAP format
            emailParts['header']['date'], emailParts['header']['subject'], emailParts['header']['messageId'] = self.extractHeaders(hdrLine)
        elif self.options['protocol'] == 'imap':
            # Get message header
            retVal, data = self.serverconnect.fetch(self.newEmails[self.nextEmail],'(BODY.PEEK[HEADER.FIELDS (DATE SUBJECT MESSAGE-ID CONTENT-TRANSFER-ENCODING)])')
            if retVal != 'OK':
                globs.log.write(globs.SEV_ERROR, function='EmailServer', action='processNextMessage', msg='ERROR getting message {}'.format(self.nextEmail))
                return '<INVALID>'
            globs.log.write(globs.SEV_DEBUG, function='EmailServer', action='processNextMessage', msg='Server.fetch(): retVal=[{}] data=[{}]'.format(retVal,data))
            emailParts['header']['date'], emailParts['header']['subject'], emailParts['header']['messageId'], emailParts['header']['content-transfer-encoding'] = self.extractHeaders(data[0][1].decode('utf-8'))
        else:   # Invalid protocol spec
            globs.log.write(globs.SEV_NOTICE, function='EmailServer', action='processNextMessage', msg='Invalid protocol specification: {}.'.format(self.options['protocol']))
            return None

        # Log message basics
        globs.log.write(globs.SEV_DEBUG, function='EmailServer', action='processNextMessage', msg='Next Message: headers=[{}]'.format(emailParts['header']))

        # Check if any of the vital parts are missing
        if emailParts['header']['messageId'] is None or emailParts['header']['messageId'] == '':
            globs.log.write(globs.SEV_NOTICE, function='EmailServer', action='processNextMessage', msg='No message-Id. Abandoning message.')
            return '<INVALID>'
        if emailParts['header']['date'] is None or emailParts['header']['date'] == '':
            globs.log.write(globs.SEV_NOTICE, function='EmailServer', action='processNextMessage', msg='No Date. Abandoning message.')
            return emailParts['header']['messageId']
        if emailParts['header']['subject'] is None or emailParts['header']['subject'] == '':
            globs.log.write(globs.SEV_NOTICE, function='EmailServer', action='processNextMessage', msg='No Subject. Abandoning message.')
            return emailParts['header']['messageId']

        # See if it's a message of interest
        # Match subject field against 'subjectregex' parameter from RC file (Default: 'Duplicati Backup report for...')
        if re.search(globs.opts['subjectregex'], emailParts['header']['subject']) == None:
            globs.log.write(globs.SEV_NOTICE, function='EmailServer', action='processNextMessage', msg='Message [{}] is not a Message of Interest. Can\'t match subjectregex from .rc file. Skipping message.'.format(emailParts['header']['messageId']))
            return emailParts['header']['messageId']    # Not a message of Interest

        # Get source & desination computers from email subject
        # Modified in 3.0.7 by @ekutner - Optimized string parsing for source & destination systems - Issue #174
        globs.log.write(globs.SEV_DEBUG, function='EmailServer', action='processNextMessage', msg="subjectregex='[{}]' srcregex='[{}]' srcdestdelimiter='[{}]' destregex='[{}]'".format(globs.opts['subjectregex'],globs.opts['srcregex'],self._unwrap_quotes(globs.opts['srcdestdelimiter']), globs.opts['destregex']))
        regex = '{} ({}){}({})'.format(globs.opts['subjectregex'],globs.opts['srcregex'],self._unwrap_quotes(globs.opts['srcdestdelimiter']), globs.opts['destregex'])
        m = re.search(regex, emailParts['header']['subject'])

        if m is None or len(m.groups()) != 2:    # Correct subject but delimeter not found. Something is wrong.
            globs.log.write(globs.SEV_NOTICE,  function='EmailServer', action='processNextMessage', msg="Correct subject '{}' but regex doesn't match {} . Skipping message.".format(emailParts['header']['subject'], regex))
            return emailParts['header']['messageId']

        # Extract source & destination information
        emailParts['header']['sourceComp'] = m.group(1)
        emailParts['header']['destComp'] = m.group(2)
        globs.log.write(globs.SEV_DEBUG, function='EmailServer', action='processNextMessage', msg="Extract: source='[{}]' destination='[{}]'".format(emailParts['header']['sourceComp'],emailParts['header']['destComp']))

        # See if the record is already in the database, meaning we've seen it before
        if globs.db.searchForMessage(emailParts['header']['messageId']):    # Is message is already in database?
            # Mark the email as being seen in the database
            globs.db.execSqlStmt('UPDATE emails SET dbSeen = 1 WHERE messageId = \"{}\"'.format(emailParts['header']['messageId']))
            globs.db.dbCommit()
            return emailParts['header']['messageId']
        # Message not yet in database. Proceed.
        globs.log.write(globs.SEV_DEBUG, function='EmailServer', action='processNextMessage', msg='Message ID [{}] does not yet exist in DB.'.format(emailParts['header']['messageId']))

        # Extract date information from header
        dTup = email.utils.parsedate_tz(emailParts['header']['date'])
        if dTup:
            # See if there's timezone info in the email header data. May be 'None' if no TZ info in the date line
            # TZ info is represented by seconds offset from UTC
            # We don't need to adjust the email date for TimeZone info now, since date line in email already accounts for TZ.
            # All other calls to toTimestamp() should include timezone info
            emailParts['header']['timezone'] = dTup[9]

            # Set date into a parseable string
            # It doesn't matter what date/time format we pass in (as long as it's valid)
            # When it comes back out later, it'll be parsed into the user-defined format from the .rc file
            # For now, we'll use YYYY/MM/DD HH:MM:SS
            xDate = '{:04d}/{:02d}/{:02d} {:02d}:{:02d}:{:02d}'.format(dTup[0], dTup[1], dTup[2], dTup[3], dTup[4], dTup[5])
            dtTimStmp = drdatetime.toTimestamp(xDate, dfmt='YYYY/MM/DD', tfmt='HH:MM:SS')  # Convert the string into a timestamp
            emailParts['header']['emailTimestamp'] = dtTimStmp
            globs.log.write(globs.SEV_DEBUG, function='EmailServer', action='processNextMessage', msg='Email Date: Timestamp=[{}] Date=[{}]'.format(dtTimStmp, drdatetime.fromTimestamp(dtTimStmp)))


        globs.log.write(globs.SEV_DEBUG, function='EmailServer', action='processNextMessage', msg='emailParts[\'header\']={}'.format(emailParts['header']))

        # Search for source/destination pair in database. Add if not already there
        retVal = globs.db.searchSrcDestPair(emailParts['header']['sourceComp'], emailParts['header']['destComp'])

        # Extract the body (payload) from the email
        if self.options['protocol'] == 'pop3':
            # Retrieve the whole messsage. This is redundant with previous .top() call and results in extra data downloads
            # In cases where there is a mix of Duplicati and non-Duplicati emails to read, this actually saves time in the large scale.
            # In cases where all the emails on the server are Duplicati emails, this does, in fact, slow things down a bit
            # POP3 is a stupid protocol. Use IMAP if at all possible.
            server_msg, body, octets = self.serverconnect.retr((self.newEmails[self.nextEmail])+1)
            msgTmp=''
            for j in body:
                msgTmp += '{}\n'.format(j.decode("utf-8"))
            emailParts['body']['fullbody'] = email.message_from_string(msgTmp)._payload  # Get message body
        elif self.options['protocol'] == 'imap':
            # Retrieve just the body text of the message.
            retVal, data = self.serverconnect.fetch(self.newEmails[self.nextEmail],'(BODY.PEEK[TEXT])')

            # Fix issue #71
            # From https://stackoverflow.com/questions/2230037/how-to-fetch-an-email-body-using-imaplib-in-python
            # "...usually the data format is [(bytes, bytes), bytes] but when the message is marked as unseen manually,
            # the format is [bytes, (bytes, bytes), bytes] – Niklas R Sep 8 '15 at 23:29
            # Need to check if len(data)==2 (normally unread) or ==3 (manually set unread)
            globs.log.write(globs.SEV_DEBUG, function='EmailServer', action='processNextMessage', msg='IMAP message fetch(): retval={} dataLen={}'.format(retVal, len(data)))
            if len(data) == 2:
                emailParts['body']['fullbody'] = data[0][1].decode('utf-8')  # Get message body
            else:
                emailParts['body']['fullbody'] = data[1][1].decode('utf-8')  # Get message body

        globs.log.write(globs.SEV_DEBUG, function='EmailServer', action='processNextMessage', msg='Message Body=[{}]'.format(emailParts['body']['fullbody']))

        # See if content-transfer-encoding is in use
        if emailParts['header']['content-transfer-encoding'].lower() == 'quoted-printable':
            emailParts['body']['fullbody'] = quopri.decodestring(emailParts['body']['fullbody'].replace('=0D=0A','\n')).decode("utf-8")
            globs.log.write(globs.SEV_DEBUG, function='EmailServer', action='processNextMessage', msg='New (quopri) Message Body=[{}]'.format(emailParts['body']['fullbody']))

        # See if email is text or JSON. JSON messages begin with '{"Data":'
        isJson = True if emailParts['body']['fullbody'][:8] == '{\"Data\":' else False

        if isJson:
            globs.log.write(globs.SEV_DEBUG, function='EmailServer', action='processNextMessage', msg='Message is JSON formatted')

            jsonStatus = json.loads(emailParts['body']['fullbody'].replace("=\r\n","").replace("=\n",""), strict = False)    # Top-level JSON data
            jsonData = jsonStatus['Data']                                           # 'Data' branch under main data

            # Get message fields from JSON column in lineParts list
            for section,regex,flag,typ,jsonSection in lineParts:
                emailParts['body'][section] = self.searchMessagePartJson(jsonData, jsonSection, typ)
            # Get Up/Download data
            if 'BackendStatistics' in jsonData:
                emailParts['body']['bytesUploaded'] = jsonData['BackendStatistics']['BytesUploaded']
                emailParts['body']['bytesDownloaded'] = jsonData['BackendStatistics']['BytesDownloaded']
            else:
                emailParts['body']['bytesUploaded'] = 0
                emailParts['body']['bytesDownloaded'] = 0

            # See if there are log lines to display
            if len(jsonStatus['LogLines']) > 0:
                emailParts['body']['logdata'] = jsonStatus['LogLines'][0]
            else:
                emailParts['body']['logdata'] = ''

            if emailParts['body']['parsedResult'] != 'Success': # Error during backup
                # Set appropriate fail/message fields to relevant values
                # The JSON report has somewhat different fields than the "classic" report, so we have to fudge this a little bit
                #   so we can use common code to process both types later.
                emailParts['body']['failed'] = 'Failure'
                globs.report.resultList['Failure'] = True
                if emailParts['body']['parsedResult'] == '':
                    emailParts['body']['parsedResult'] = 'Failure'
                emailParts['body']['errors'] = jsonData['Message'] if 'Message' in jsonData else ''
        else: # Not JSON - standard Duplicati message format
            # Issue #174 - Some email systems generate HTML instead of text output. To prevent crashing, replace any HTML '<br>' breaks with newlines.
            emailParts['body']['fullbody'] = emailParts['body']['fullbody'].replace('<br/>','\n')

            globs.log.write(globs.SEV_DEBUG, function='EmailServer', action='processNextMessage', msg='Message is Duplicati formatted')
            # Go through each element in lineParts{}, get the value from the body, and assign it to the corresponding element in emailParts['body']{}
            for section,regex,flag,typ, jsonSection in lineParts:
                emailParts['body'][section] = self.searchMessagePart(emailParts['body']['fullbody'], regex, flag, typ) # Get the field parts
                # bytesUploaded & bytesDownloaded are only included in JSON message formats. Set to 0 if it's a non-JSON message
                if section == 'bytesUploaded':
                    emailParts['body']['bytesUploaded'] = 0
                if section == 'bytesDownloaded':
                    emailParts['body']['bytesDownloaded'] = 0

        # Adjust fields if not a clean run
        globs.log.write(globs.SEV_DEBUG, function='EmailServer', action='processNextMessage', msg="emailParts['body']['failed']=[{}]".format(emailParts['body']['failed']))
        if emailParts['body']['failed'] == '':  # Looks like a good run
            globs.log.write(globs.SEV_DEBUG, function='EmailServer', action='processNextMessage', msg='Email indicates a successful backup.')
            # Get the start and end times of the backup
            if  isJson:
                emailParts['body']['endTimestamp'] = drdatetime.toTimestampRfc3339(emailParts['body']['endTimeStr'], utcOffset = emailParts['header']['timezone'])
                emailParts['body']['beginTimestamp'] = drdatetime.toTimestampRfc3339(emailParts['body']['beginTimeStr'], utcOffset = emailParts['header']['timezone'])
            else:
                # Some fields in "classic" Duplicati report output are displayed in standard format or detailed format (in parentheses)
                # For example:
                #   SizeOfModifiedFiles: 23 KB (23556)
                #   SizeOfAddedFiles: 10.12 KB (10364)
                #   SizeOfExaminedFiles: 44.42 GB (47695243956)
                #   SizeOfOpenedFiles: 33.16 KB (33954)
                # JSON output format does not use parenthesized format (see https://forum.duplicati.com/t/difference-in-json-vs-text-output/7092 for more explanation)

                # Extract the parenthesized value (if present) or the raw value (if not)
                dt, tm = globs.optionManager.getRcSectionDateTimeFmt(emailParts['header']['sourceComp'], emailParts['header']['destComp'])
                emailParts['body']['endTimestamp'] = self.parenOrRaw(emailParts['body']['endTimeStr'], df = dt, tf = tm, tz = emailParts['header']['timezone'])
                emailParts['body']['beginTimestamp'] = self.parenOrRaw(emailParts['body']['beginTimeStr'], df = dt, tf = tm, tz = emailParts['header']['timezone'])
                emailParts['body']['sizeOfModifiedFiles'] = self.parenOrRaw(emailParts['body']['sizeOfModifiedFiles'])
                emailParts['body']['sizeOfAddedFiles'] = self.parenOrRaw(emailParts['body']['sizeOfAddedFiles'])
                emailParts['body']['sizeOfExaminedFiles'] = self.parenOrRaw(emailParts['body']['sizeOfExaminedFiles'])
                emailParts['body']['sizeOfOpenedFiles'] = self.parenOrRaw(emailParts['body']['sizeOfOpenedFiles'])

            # Issue #147 - 'Limited' W/E/M fields get moved to standard W/E/M fields
            # The 'Limited' fields were introduced in Beta 2.0.5.1 (2.0.5.1_beta_2020-01-18)
            if emailParts['body']['limitedErrors'] != '':
                emailParts['body']['errors'] = emailParts['body']['limitedErrors']
            if emailParts['body']['limitedWarnings'] != '':
                emailParts['body']['warnings'] = emailParts['body']['limitedWarnings']
            if emailParts['body']['limitedMessages'] != '':
                emailParts['body']['messages'] = emailParts['body']['limitedMessages']

        else:  # Something went wrong. Let's gather the details.
            globs.log.write(globs.SEV_DEBUG, function='EmailServer', action='processNextMessage', msg='Email indicates a failed backup.')
            if not isJson:
                emailParts['body']['errors'] = emailParts['body']['failed']
                emailParts['body']['parsedResult'] = 'Failure'
                globs.report.resultList['Failure'] = True
                emailParts['body']['warnings'] = emailParts['body']['details']

            globs.log.write(globs.SEV_DEBUG, function='EmailServer', action='processNextMessage', msg='Errors=[{}]'.format(emailParts['body']['errors']))
            globs.log.write(globs.SEV_DEBUG, function='EmailServer', action='processNextMessage', msg='Warnings=[{}]'.format(emailParts['body']['warnings']))
            globs.log.write(globs.SEV_DEBUG, function='EmailServer', action='processNextMessage', msg='Log Data=[{}]'.format(emailParts['body']['logdata']))

            # Since the backup job report never ran, we'll use the email date/time as the report date/time
            emailParts['body']['endTimestamp'] = emailParts['header']['emailTimestamp']
            emailParts['body']['beginTimestamp'] = emailParts['header']['emailTimestamp']
            globs.log.write(globs.SEV_DEBUG, function='EmailServer', action='processNextMessage', msg='Replacing date/time for failed backup with: end=[{}]  begin=[{}]'.format(emailParts['body']['endTimestamp'], emailParts['body']['beginTimestamp'])),

        # Replace commas (,) with newlines (\n) in message fields. SQLite really doesn't like commas in SQL statements!
        for part in ['messages', 'warnings', 'errors', 'logdata']:
            if emailParts['body'][part] != '':
                emailParts['body'][part] = emailParts['body'][part].replace(',','\n')

        # If we're just collecting and get a warning/error, we may need to send an email to the admin
        if (globs.opts['collect'] is True) and (globs.opts['warnoncollect'] is True) and ((emailParts['body']['warnings'] != '') or (emailParts['body']['errors'] != '')):
            errMsg = 'Duplicati error(s) on backup job\n'
            errMsg += 'Message ID {} on {}\n'.format(emailParts['header']['messageId'], emailParts['header']['date'])
            errMsg += 'Subject: {}\n\n'.format(emailParts['header']['subject'])
            if emailParts['body']['warnings'] != '':
                errMsg += 'Warnings:' + emailParts['body']['warnings'] + '\n\n'
            if emailParts['body']['errors'] != '':
                errMsg += 'Errors:' + emailParts['body']['errors'] + '\n\n'
            if emailParts['body']['logdata'] != '':
                errMsg += 'Log Data:' + emailParts['body']['logdata'] + '\n\n'

            globs.emailManager.sendEmail(msgText=errMsg, subject='Duplicati Job Status Error')

        globs.log.write(globs.SEV_DEBUG, function='EmailServer', action='processNextMessage', msg='Resulting timestamps: endTimeStamp=[{}] beginTimeStamp=[{}]'.format(drdatetime.fromTimestamp(emailParts['body']['endTimestamp']), drdatetime.fromTimestamp(emailParts['body']['beginTimestamp'])))

        globs.db.execEmailInsertSql(emailParts)
        return emailParts['header']['messageId']

    # Issue #174 support. Remove quotes from a string
    def _unwrap_quotes(self, src):
        QUOTE_SYMBOLS = ('"', "'")
        for quote in QUOTE_SYMBOLS:
            if src.startswith(quote) and src.endswith(quote):
                return src.strip(quote)
        return src

    # Issue #111 feature request
    # Provide ability to mark messages as read/seen if [main]markread is true in the .rc file.
    # This function is only works for IMAP. POP3 doesn't have this capability.
    def markMessagesRead(self):
        globs.log.write(globs.SEV_NOTICE, function='EmailServer', action='markMessagesRead', msg='Marking {} {} messages as \'read/seen\''.format(self.numEmails, self.options['protocol']))
        for msg in range(self.numEmails):
            self.serverconnect.store(self.newEmails[msg],'+FLAGS',r'\Seen')
        return

    # Search for field in message
    # msgField - text to search against
    # regex - regex to search for
    # multiLine - 0=single line, 1=multi-line
    # type - 0=int or 1=string
    def searchMessagePart(self, msgField, regex, multiLine, typ):
        globs.log.write(globs.SEV_DEBUG, function='EmailServer', action='searchMessagePart', msg='Searching for standard field: regex=[{}], multiline=[{}], typ=[{}]'.format(regex, multiLine, typ))

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

        globs.log.write(globs.SEV_DEBUG, function='EmailServer', action='searchMessagePart', msg='Search result: \'{}\''.format(retData))
        return retData

    # Search for field in JSON message
    def searchMessagePartJson(self, jsonParts, key, typ):
        globs.log.write(globs.SEV_DEBUG, function='EmailServer', action='searchMessagePart', msg='Searching for JSON field \'{}\', typ=[{}]'.format(key,typ))
        if key in jsonParts:
            return jsonParts[key];

        # Key wasn't found in list value. Return appropriate empty value
        if typ == 0: #integer
            return 0
        else:       # string
            return ''

    # Replace substrings in title field
    def subjectSubstitute(self, subject = None, category = None, results = {}, seeking = None, replacement = None):

        # See if we even  have this type of message
        if category not in results:
            newsubject = subject.replace(seeking,'')
        else:
            newsubject  = subject.replace(seeking, replacement)

        globs.log.write(globs.SEV_NOTICE, function='EmailServer', action='subjectSubstitute', msg='Replacing {} in subject line. Was \'{}\'. Now \'{}\''.format(seeking, subject, newsubject))
        return newsubject

    # Send final email result
    def sendEmail(self, msgHtml = None, msgText = None, subject = None, sender = None, receiver = None, fileattach = False):
        self.connect()

        # Build email message
        globs.log.write(globs.SEV_NOTICE, function='EmailServer', action='sendEmail', msg='Building email.')
        msg = MIMEMultipart('alternative')
        if subject is None:
            globs.log.write(globs.SEV_NOTICE, function='EmailServer', action='sendEmail', msg='No subject yet, using default subject of \'{}\'.'.format(globs.report.rStruct['defaults']['title']))

            subject = globs.report.rStruct['defaults']['title']

            # Check for title substitutions - Issue #172
            # It turns out that - for whatever reason - SMTP REALLY DOES NOT like using a '[' as the first character in a subject line,
            # and the resulting subject line can be unpredictable; not exactly what you want in a program.
            # So, the bounding character for the keyword replacement was changed to '|'. That seemed to work much better.
            # If someone knows why that is, please let me know, as I wasted far too many hours trying to figure it out.
            globs.log.write(globs.SEV_NOTICE, function='EmailServer', action='sendEmail', msg='subject={}  resultlist={}'.format(subject, globs.report.resultList))

            # Check for #ALL# keyword substitution
            substr = re.search("#ALL#", subject)
            if substr is not None:
                subject = subject.replace("#ALL#","#SUCCESS##WARNING##ERROR##FAILURE#")
                globs.log.write(globs.SEV_NOTICE, function='EmailServer', action='sendEmail', msg='#ALL# keyword detected, substituting. New subject={}'.format(subject))
            else:
                # Check for #ANYERROR# substitution
                substr = re.search("#ANYERROR#", subject)
                if substr is not None:
                    subject = subject.replace("#ANYERROR#","#WARNING##ERROR##FAILURE#")
                    globs.log.write(globs.SEV_NOTICE, function='EmailServer', action='sendEmail', msg='#ANYERROR# keyword detected, substituting. New subject={}'.format(subject))

            subject = self.subjectSubstitute(subject, 'Success', globs.report.resultList, '#SUCCESS#', '|Success|')
            subject = self.subjectSubstitute(subject, 'Warning', globs.report.resultList, '#WARNING#', '|Warning|')
            subject = self.subjectSubstitute(subject, 'Error', globs.report.resultList, '#ERROR#', '|Error|')
            subject = self.subjectSubstitute(subject, 'Failure', globs.report.resultList, '#FAILURE#', '|Failure|')
        else:
            globs.log.write(globs.SEV_NOTICE, function='EmailServer', action='sendEmail', msg='Subject already exists: \'{}.\''.format(subject))

        globs.log.write(globs.SEV_NOTICE, function='EmailServer', action='sendEmail', msg='Final subject line: \'{}\'.'.format(subject))
        msg['Subject'] = subject
        if sender is None:
            sender = self.options['sender']
        if self.options['sendername'] != '':
            sender = '{} <{}>'.format(self.options['sendername'], sender)
        msg['From'] = sender
        if receiver is None:
            receiver = self.options['receiver']
        msg['To'] = receiver

        # Add 'Date' header for RFC compliance - See issue #77
        msg['Date'] = email.utils.formatdate(time.time(), localtime=True)

        # Record the MIME types of both parts - text/plain and text/html.
        # Attach parts into message container.
        # According to RFC 2046, the last part of a multipart message is best and preferred.
        # So attach text first, then HTML
        if msgText != None:
            globs.log.write(globs.SEV_DEBUG, function='EmailServer', action='sendEmail', msg='Length=[{}] TextVersion=[{}]'.format(len(msgText),msgText))
            msgPart = MIMEText(msgText, 'plain')
            msg.attach(msgPart)

        if msgHtml != None:
            globs.log.write(globs.SEV_DEBUG, function='EmailServer', action='sendEmail', msg='Length=[{}] HTMLVersion=[{}]'.format(len(msgHtml),msgHtml))
            msgPart = MIMEText(msgHtml, 'html')
            msg.attach(msgPart)

        # See which files need to be emailed
        # ofileList consists of tuples of (<filespec>,<emailSpec>)
        # Filespec is "<filename,type>". <emailSpec> is True (attach file as email) or False (dont).
        if fileattach and globs.ofileList:
            for ofile in globs.ofileList:
                if ofile[1]: # True - need to email
                    fname = ofile[0].split(',')[0]
                    attachment = open(fname, 'rb')
                    file_name = os.path.basename(fname)
                    part = MIMEBase('application','octet-stream')
                    part.set_payload(attachment.read())
                    part.add_header('Content-Disposition', 'attachment', filename=file_name)
                    encoders.encode_base64(part)
                    globs.log.write(globs.SEV_NOTICE, function='EmailServer', action='sendEmail', msg='Attaching file {} to email.'.format(file_name))
                    msg.attach(part)

        # Send the message via SMTP server.
        globs.log.write(globs.SEV_NOTICE,function='EmailServer', action='sendEmail', msg='Sending email to [{}]. Total length=[{}] AsString Length=[{}]'.format(globs.maskData(receiver.split(',')), len(msg), len(msg.as_string())))

        # Issue #166. Received a "501 Syntax error - line too long" error when sending through GMX SMTP servers.
        # Needed to change from smtplib.sendmail() to smtplib.send_message().
        # Tested on Gmail, Yahoo, & GMX with no errors.
        # Keeping this around in comment as I don't think this is the last we'll hear of this problem.
        #       #self.serverconnect.sendmail(sender, receiver.split(','), msg.as_string().encode('utf-8'))
        #       #The encode('utf-8') was added to deal with non-english character sets in emails. See Issue #26 for details
        self.serverconnect.send_message(msg, sender, receiver.split(','))

        return None

