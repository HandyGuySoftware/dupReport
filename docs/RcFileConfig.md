# dupReport.rc Configuration

The dupReport.rc file contains configuration information for dupReport to run properly. Many options in the dupReport.rc file have equivalent command line options. If an option is specified on both the command line and the .rc file, the command line option takes precedence.

## [main] section

The [main] section contains the high-level program options for dupReport to run properly.

```
version=<major>.<minor>.<subminor>
```

The current version number of the program. Used to determine if the .rc file needs to be updated. **PLEASE DO NOT** alter the version= option

```
dbpath=<dbpath>
```

 Directory where the dupReport.db file is located. Can be overridden by the -d command line option.

```
logpath=<logpath> 
```

The directory where the dupReport.log file is located. Can be overridden by the -l command line option.

```
verbose=
```

- 0=No log output
- 1=(Default) General program execution info.
- 2=Program flow and status information
- 3=Full debugging output

Sets the level of detail the program will put in the log file. Can be overridden by the -v command line option.

```
logappend=false
```

Append new logs to the log file (true) or reset log file for each run (false). Can be overridden by the -a command line option.

```
subjectregex=^Duplicati Backup report for
```

A regular expression used to find backup message Emails Of Interest. This should somewhat match the text specified in the ‘send-mail-subject’ advanced option in Duplicati. 

**NOTE**: If you modify the subject line of your Duplicati emails by changing the ‘send-mail-subject’ option, make sure that the subject line you construct ***does not*** use the character you specify as the Source/Destination delimiter in the srcdestdelimiter= option in dupReport.rc (see below). If the subject line uses the same character as the Source/Destination delimiter, dupReport will get confused and not parse your emails properly.

```
srcregex=\w*
```

Regular expression used to find the “source” side of the source-destination pair in the subject line of the email.

```
destregex=\w*
```

Regular expression used to find the “destination” side of the source-destination pair in the subject line of the email.

```
srcdestdelimiter=-
```

Single character used to specify the delimiter between the ‘source’ and ‘destination’ parts of the source-destination pair.

```
dateformat=MM/DD/YYYY
```

Default format for dates found in emails. Acceptable formats are:

- MM/DD/YYYY
- DD/MM/YYYY
- MM-DD-YYYY
- DD-MM-YYYY
- MM.DD.YYYY
- DD.MM.YYYY
- YYYY/MM/DD
- YYYY/DD/MM
- YYYY-MM-DD
- YYYY-DD-MM
- YYYY.MM.DD
- YYYY.DD.MM

If there are problems in your report dates (especially if your locale doesn't use U.S.-style dates), or if you are getting program crashes around the date/time routines, you might try checking and/or changing this value.

The default format can be overridden for specific backup jobs by specifying a dateformat= line in a job-specific section of the .rc file. See “[source-destination] Sections” below.

```
timeformat=HH:MM:SS
```

Default format for times found in emails. The only time format currently acceptable is ‘HH:MM:SS’. The default format can be overridden for specific backup jobs by specifying a timeformat= line in a job-specific section of the .rc file. See “[source-destination] Sections” below.

```
warnoncollect=false
```

If true, send an email if there are warning or error messages in incoming email. Only works if the -c option is specified so the user will get error messages even if they are not producing an email report.

```
applyutcoffset=true
```

Duplicati version 2 does not apply local time zone information when reporting start and end times for backup jobs. If set to 'true', this option takes the UTC time zone offset from the email header and applies it to the backup job start and end times. If the backup times in your report do not look right, try adjusting this value.

```
show24hourtime=false
```

 If true, times will be displayed in 24-hour notation. Otherwise, dupReport will use 12-hour, AM/PM notation.

```
purgedb=true
```

If true, emails in the database that are no longer found on the incoming email server will be purged from the database and the database will be compacted. **NOTE:** Any source-destination pairs referenced in purged emails will remain in the database in case emails for those pairs are seen in the future. To remove obsolete source-destination pairs from the database, use the -m option.

```
showprogress=0
```

If this option is greater than zero, dupReport will display a dot ('.') on stdout for every 'n' emails that are processed from the incoming server. For example, if showprogress=5, there will be one '.' for every 5 emails that are read.

```
masksensitive = true
```

Masks sensitive data in the log file. If set to "true" (the default), fields such as user name, password, server name, and file paths will be masked with asterisks in the log file. This is useful for maintaining privacy if the log file needs to be stored or transmitted somewhere else for debugging or analysis purposes. **NOTE**: this setting **<u>will not</u>** mask any information found in the actual emails pulled from your email server, such as sending and receiving email address, server names, etc. It only affects the data that dupReport generates as part of its operation.

```
markread = false
```

When set to "true" dupReport will instruct the email server to mark all emails as read/seen once they have been processed by the program. The default is "false" allowing the program to leave the email inbox in the same state as it found it. **NOTE:** this option is only available when using the IMAP protocol. POP3 does not have this capability.

## [incoming] section

The [incoming] section contains settings for incoming email that dupReport reads to create the report. If you are not sure what these settings should be for your email provider, try Googling "\<*email provider*> IMAP settings" or "\<*email provider*> POP3 settings."

```
transport=imap
```

Specify the transport mechanism used to gather emails from the email server. Can be 'imap' or 'pop3'. **IMAP is highly recommended**. POP3 has some severe limitations when it comes to handling email. If you must use POP3 for whatever reason, make sure the "Leave messages on server" option is enabled in all your POP3 clients and/or your POP3 server. The default behavior for POP3 is to remove messages from the email server as soon as they are read, so using multiple email clients on the same server will interfere with each's ability to read email. Setting this option tells the system it to leave the messages on the server for other clients to use. Different systems configure this option differently, so check the documentation for your email system to see where this is set.

```
inserver=localhost
```

DNS name or IP address of email server where Duplicati result emails are stored.

```
inport=995
```

IMAP or POP3 port for incoming email server.

```
inencryption=tls
```

Specify encryption used by incoming email server. Can be 'none', 'tls' (default), or 'ssl'

```
inaccount=<account_name>
```

User ID on incoming email system.

***NOTE:*** If you are using Gmail as your email server *and* using POP3 as your transport, put the prefix "recent:" in front of your email address, as in 

> inaccount=recent:user@gmail.com

The Gmail default is to retrieve email starting from the oldest, with a maximum of 250 emails. If you have a large inbox this will cause you to lose the most recent emails. The "recent:" prefix tells Gmail to retrieve the most recent 30 days of email. 

```
inpassword=<password>
```

Password for incoming email system

```
infolder=INBOX
```

Email account folder where incoming Duplicati email is stored. This parameter is used for IMAP systems and ignored for POP3 systems.

```
inkeepalive=false
```

Large inboxes may take a long time to scan and parse, and on some systems this can lead to a server connection timeout before processing has completed. This is more likely to happen on the outgoing connection (where there may be long periods of inactivity) than on the incoming connection. However, if you are experiencing timeout errors on your incoming server connection set this value to 'true'.

```
unreadonly = false
```

This option instructs the program to only read and parse messages marked as "unread" or "unseen" on the email server. This has the effect of dramatically reducing the time it takes to read your emails, as it only reads messages it hasn't seen yet. There are several things to consider when using this option:

- This option is only effective on IMAP email servers. It has no effect on POP3 servers.
- If any other process or user marks any of the messages on the server as read/seen this will impact dupReport's ability to properly parse all the emails. You should only use this option if dupReport is the only process accessing the IMAP email folder where the Duplicati emails are stored.
- This option should be used in conjunction with the **[main] markread** option set to "true" so messages will be marked as read once they are processed by dupReport.
- The seen/unseen flag can be flaky and exhibit different behaviors on different IMAP servers. You should test its usage thoroughly before using it in dupReport.

## [outgoing] section

The [outgoing] section contains settings for the email server that dupReport will use to send the final summary report email. If you are not sure what these settings should be for your email provider, try Googling "\<*email provider*> SMTP settings."

```
outtransport=smtp
```

Specify the transport protocol used to send emails to the outgoing server. Only SMTP is supported for outgoing email.

```
outserver=localhost
```

DNS name or IP address of outgoing email server. 

```
outport=587
```

SMTP port for outgoing email server. 

```
outencryption=tls
```

Specify the encryption used by outgoing email server. Can be 'tls' or 'none'

```
outaccount=<account name>
```

User ID on outgoing email system.

```
outpassword=<password>
```

Password for outgoing email system.

```
outsender=sender@somemail.com
```

Email address of report sender. To add a "friendly name" to the sender's email address, use the form:

	 `outsender=Arthur Dent <adent@galaxy.org>`

```
outreceiver=receiver@somemail.com
```

Email address of report recipient. To add a "friendly name" to the receiver's email address, use the form:

	`outreceiver=Arthur Dent <adent@galaxy.org>`

To send to multiple recipients, separate the recipients with a comma:

	`outreceiver=adent@galaxy.org, Zaphod B <zbeeblebrox@galaxy.org>`

```
outkeepalive=false
```

Large inboxes may take a long time to scan and parse, and on some systems this can lead to a server connection timeout before processing has completed. This is more likely to happen on the outgoing connection (where there may be long periods of inactivity) than on the incoming connection. If you are experiencing timeout errors on your outgoing server connection set this value to 'true'.



Return to [Main Page](readme.md)