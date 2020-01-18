

# WELCOME TO dupReport!!!

dupReport is an email-based reporting system for Duplicati. It will gather all your Duplicati backup status emails and produce a summary report on what Duplicati backup jobs were run and their success or failure.

Here is a list of some of dupReport's most important features:

- Collects all your Duplicati result emails and produces easy-to-understand status reports
- Runs on multiple operating systems. dupReport has been tested on Linux (Debian 8 & 9) and Windows 10, but users have reported it working on a wide variety of operating systems
- Support for IMAP and POP3 email services (we recommend IMAP for better results)
- SSL/TLS support for incoming/outgoing email transmissions.
- Output report supports HTML, text, and CSV formats
- Supports both text and JSON status emails from Duplicati
- Multiple reporting formats with configurable column options
- No limit to  the number of different backup jobs it can track
- Support for Apprise push notification service (<https://github.com/caronc/apprise>)

# How can I get started quickly?

There's a **lot** of information below about how to install, configure, and run dupReport. But you probably don't want to read all that, you want to just start running the program! Here's the quick & dirty guide to get you started.

1. Make sure Python 3.x is available and running on your system. For information on downloading and installing Python see the [Python Software Foundation web site](https://www.python.org/). 
2. Make sure your Duplicati backup jobs are named properly. The best naming scheme (at least to get      you started) is:

```
<source>-<destination>
```

where \<source> is the name of the computer where the files are located and \<destination> is the place where they are going to. For example, if your computer is named "shenjhou" and you are backing up to a directory on the "discovery" computer, the backup name would be:

```
shenjhou-discovery
```

For more interesting information on naming backup jobs see the section below on "Source-Destination Pairs." 

3. Configure a Duplicati job to send its output report to an email account. See the [Duplicati documentation for the "send-mail" advanced email options](https://duplicati.readthedocs.io/en/latest/06-advanced-options/#send-mail-to) to learn how to do this.
4. Run at least one backup with the newly-named backup job so that you have an email that dupReport can find on your email server. 
5. Download the dupReport code from the [GitHub page](https://github.com/HandyGuySoftware/dupReport) by clicking the "Clone or download" button on the dupReport GitHub page, then click "Download ZIP." This will put the ZIP file on your system. Unzip the file to the directory of your choice.
6. Run dupReport.py to install the default configuration files. The instructions for doing this can be      found below in "First-time Installation." Read that section, do what it says, then come back here.
7. After the initial run, locate the "dupreport.rc" file in the dupReport directory. Open the file with a text editor (notepad, notepad++, nano, vi, whatever. Again, no judgements.) Update the following sections as noted:

```
[incoming]
intransport = imap    				# Select imap or POP3
inserver = localhost				# DNS name of email server with Duplicati emails
inport = 993						# IP port for transport. 993 for IMAP, 995 for POP3
inencryption = tls					# "tls" or "none"
inaccount = someacct@hostmail.com	# Account ID on email server
inpassword = ********				# Password for email server
infolder = INBOX					# Folder to find emails (IMAP only)

[outgoing]
outserver = localhost				# DNS name of outgoing SMTP server
outencryption = tls					# "tls" or "none"
outaccount = someacct@hostmail.com	# Account ID on SMTP server
outpassword = ********				# Password for SMTP server
outsender = sender@hostmail.com		# ID to send emails from
outreceiver = receiver@hostmail.com # Email address to send report to
```

There are lots of other options you can configure in the .rc file to customize how dupReport runs, but these are the bare minimum you need to get started.

8. Run the dupReport.py program using the appropriate command line as shown in the "Running the Program After Installation" section below.
9. Let the program run to completion. When it is complete you should get an email with the output      report.

That's the quick way to do it! Now that you've seen how it works, please read the rest of this guide for LOTS more information on how to configure dupReport to get the most out of the program.

# Available Code Branches

Beginning with release 2.1, the branch structure of the dupReport repository has changed. We have moved to a more organized structure based on [this article by Vincent Driessen](http://nvie.com/posts/a-successful-git-branching-model/) (with some modifications). (Thanks to @DocFraggle for suggesting this structure.)

There are usually only two branches in the dupReport repository:

| Branch Name  | Current Version | Purpose                                                      |
| ------------ | --------------- | ------------------------------------------------------------ |
| **master**   | 2.2.9           | This is the Release branch, which should contain <u>completely stable</u> code. If you want the latest and greatest release version, get it here. If you are looking for an earlier release, tags in this branch with the name "Release_x.x.x" will point you there. |
| **pre_prod** | \<None>         | The Pre-Production branch. This is a late-stage beta branch where code should be mostly-stable, but no guarantees. Once final testing of code in this branch is complete it will be moved to master and released to the world. If you want to get a peek at what's coming up in the next release, get the code from here. **If you don't see a pre_prod branch in the repository, that means there isn't any beta code available for testing.** |

If you see any additional branches in the repository, they are there for early-stage development or bug fix testing purposes. Code in such branches should be considered **<u>highly unstable</u>**. Swim here at your own risk. Void where prohibited. Batteries not included. Freshest if eaten before date on carton. For official use only. Use only in a well-ventilated area. Keep away from fire or flames. May contain peanuts. Keep away from pets and small children. (You get the idea.)

Bug reports and feature requests can be made on GitHub in the [Issues Section](https://github.com/HandyGuySoftware/dupReport/issuesdupReport). <u>Please do not issue pull requests</u> before discussing any problems or suggestions as an Issue. 

The discussion group for dupReport is on the Duplicati Forum in [this thread](https://forum.duplicati.com/t/announcing-dupreport-a-duplicati-email-report-summary-generator/1116).

The program is released under an MIT license. Please see the LICENSE file for more details.

Please follow dupReport on Twitter [@dupReport](https://twitter.com/DupReport)

Enjoy!

# What is it?

dupReport is a program that will collect up status emails from Duplicati and combine them into a single email report that is sent to you. The following diagram helps explain how it works:

![dupReport Architecture](dR_Architecture.jpg)\

Some general points about dupReport

- The program is designed for those who run backups from multiple locations and are getting multiple     Duplicati emails per day. For example, we have 14 separate emails coming in per day from Duplicati backup jobs; way too many to keep track of manually. In these cases, dupReport will collect and collate all those emails and create a single report that summarizes all of them. If you only have a single instance of Duplicati running a single backup job, you may get some value from dupReport, but it may be overkill.
- dupReport doesn’t interface directly with Duplicati and doesn't read the Duplicati configuration files, log files, or or database. It connects to your email server, reads the backup report emails that Duplicati sends out, then parses them to create its report. It does not need to be run on the same system where Duplicati is running, it can be on a completely different system if that is more convenient for you. The only requirement is that the system where dupReport is running must be able to connect to your email server.

# Origin Story

The old CrashPlan Home backup system had a really nice feature whereby it would gather up the current backup status for all your systems and mail you a consolidated report on a periodic basis. It was a great way to make sure all your backups were current and to notify you if something was wrong. Duplicati has no such capability. You can configure it to send you email when backup jobs completed, but you get a separate email for each backup job that runs. In the configuration we have (9 systems backing up to 2 different storage services in various combinations) we get 14 different emails per day. Compare that with CrashPlan's single summary email per day and you can see how this was a problem. Others on the [Duplicati discussion forum](https://forum.duplicati.com/) noticed it, too. That started us thinking about developing a tool to provide summarized email notification for Duplicati users.  

dupReport was born.  

# Source-Destination Pairs

dupReport identifies backup jobs as a series of "Source-Destination" pairs. dupReport uses Source-Destination Pairs to identify the source and destination systems for each backup job. The default dupReport configuration requires that jobs be named in a way that indicates what is being backed up and where it is going. For instance, a job named: “Fred_Home_Desktop-Homers_Minio would show up in the dupReport as:

> **Source:** Fred_Home_Desktop   **Destination:** Homers_Minio

Note that spaces in job names are not supported, at least by the default pattern matching.

Source-Destination pairs are specified in dupReport in the following format: 

```
<Source><delimiter><Destination>
```


Where:

- \<Source\> is a series of alphanumeric characters
- \<delimiter\> is a single character (typically one of the "special" characters) and **CAN NOT** be a character you use in any of your Source-Destination pairs 
- \<Destination\> is a series of alphanumeric characters
- **There can be NO SPACES** in or between the \<Source>, \<delimiter>, and \<Destination> specifications

dupReport allows you to define the format specification of the Source, Destination, and Delimiter in the [main] section of the dupReport.rc file. Each specification is the regular expression definition of that element. The defaults are: 

```
[main]
srcregex=\w\*
destregex=\w\*
srcdestdelimiter=-
```

Together the full source-destination regex is:

```
<srcregex><srcdestdelimiter><destregex> 
```

You can modify the specification of these elements by replacing each with a regular expression defining how dupReport can find that element in a email's subject line. 

***WARNING!*** *dupReport relies on the Source-Destination pair format for all of its operations. If you do not properly specify your Source-Destination pair formats in both the program (through the dupReport.rc file) and in Duplicati (through proper job naming) none of this will work for you. In particular (and repeating what's already been stated) make sure that you **DO NOT INCLUDE ANY SPACES** in or between the \<Source>, \<delimiter>, and \<Destination> specifications in your Duplicati job names.*

# Identifying Emails of Interest

dupReport scans the identified mailbox looking for backup job emails. However, there may be hundreds (or thousands) of emails in the inbox, only a few of which contain information about Duplicati backup jobs. dupReport identifies "Emails of Interest" by matching the email's subject line against a pattern defined in the dupReport.rc file. If the pattern matches, the email is analyzed. If the pattern does not match, the email is ignored. 

The default pattern it looks for is the phrase "Duplicati backup report for" which is the default used  for Duplicati's “send-mail-subject” advanced option. You can change the text that dupReport tries to match by adjusting the subjectregex= option in the [main] section of the dupReport.rc file. subjectregex is  the regular expression definition for the desired phrase. The default for this option is: 

```
[main]
subjectregex=^Duplicati Backup report for 
```

If you change the subjectregex option, be sure that it will match the text specified in the Duplicati send-mail-subject advanced option or you will not be able to properly match incoming emails.

Several users on the Duplicati Forum have found different ways to modify subjectregex= to get more control over finding Emails of Interest. [This idea from dcurrey](https://forum.duplicati.com/t/announcing-dupreport-a-duplicati-email-report-summary-generator/1116/15) shows one way to specify what types of report emails you are looking for.  [This post from Marc_Aronson](https://forum.duplicati.com/t/how-to-configure-automatic-email-notifications-via-gmail-for-every-backup-job/869) shows another approach.

# System Requirements

dupReport has been formally tested on Linux (Debian 8 and 9) and Windows 10 and is officially supported on those platforms. However, users posting on the [dupReport announcement page on the Duplicati Forum](https://forum.duplicati.com/t/announcing-dupreport-a-duplicati-email-report-summary-generator/1116)   have stated they’ve installed and run the program on a wide variety of operating systems. The python code uses standard Python libraries, so it *should* run on any platform where Python can be run.

In addition to the dupReport program files, the only other software dupReport needs is Python3. Installation instructions for Python are beyond our scope here, but instructions are widely available on the Internet.

# Installing dupReport

dupReport installation is easy and quick. To begin, download the dupReport files from the GitHub repository and place them in the directory of your choice. Then, make sure Python 3 is installed on your system and operating correctly.

## First-time Installation

Installing dupReport is easy. To use all the default values, execute the following command:

```
Linux systems: user@system:~$ /path/to/dupReport/dupReport.py
```

```
Windows Systems: C:\users\me> python.exe \path\to\dupreport\dupReport.py
```

dupReport is self-initializing, and running the program for the first time creates the database, initializes the .rc file with a bunch of default values, then exits. By default, the database and .rc files will be created in the same directory where the dupReport.py script is located. If you want them created in another location use the following program options:

```
dupReport.py -r <RC_Directory> -d <Database_Directory>
```

dupReport will create the .rc and database files in their respective paths. Both directories must already exist and you must have read and write access permissions to those locations. Use of the default values for these file paths is recommended, but the option is there if you want it.

The only thing dupReport can't set defaults for is the technical specifics about your incoming and outgoing mail servers (for example, the name/IP address, user ID, password, transport, encryption, etc.). These are specified in the [incoming] and [outgoing] sections of the .rc file. Once you edit those entries in the .rc file everything should work like magic. Probably.

More information on the .rc file configuration can be found below under “RC File Configuration.”

## Upgrading From a Previous Version

If you have been running an earlier version of dupReport, the program will automatically update the dupReport.rc file and the dupReport.db database to the latest versions. Depending on the extent of the changes, the program may indicate that you need to edit the dupReport.rc file to set any new options correctly. 

As a precaution, **it is highly recommended that you backup your .rc and .db files to a safe place** before proceeding with the upgrade until you're sure everything is working properly.

## Running the Program After Installation

Once all the options have been set in the .rc file, use the following commands to run dupReport normally:

```
Linux systems: user@system:~$ /path/to/dupReport/dupReport.py <options>
```

```
Windows Systems: C:\users\me> python.exe \path\to\dupreport\dupReport.py <options>
```

# Command Line Options

Command line options alter the way dupReport operates. Many command line options have equivalent options in the dupReport.rc file. If an option is specified on both the command line and in the .rc file, the command line option takes precedence.

dupReport has the following command line options:

| Short Version               | Long Version                       | Description                                                  |
| --------------------------- | ---------------------------------- | ------------------------------------------------------------ |
| -h                          | --help                             | Display command line options.                                |
| -r \<rcpath\>               | --rcpath \<rcpath\>                | Sets \<rcpath\> as the directory where the dupReport.rc file is located. \<rcpath\> should point to the directory only, not a full file path specification. |
| -d \<dbpath\>               | --dbpath \<dbpath\>                | Sets \<dbpath\> as the directory where the dupReport.rc file is located. Overrides the [main] dbpath= option in dupReport.rc file. \<dbpath\> should point to the directory only, not a full file path specification. |
| -l \<logpath\>              | --logpath \<logpath\>              | Sets \<logpath\> as the directory where the dupReport.log file is located. Overrides the [main] logpath= option in dupReport.rc file. \<logpath\> should point to the directory only, not a full file path specification. |
| -v {0,1,2, 3}               | --verbose {0,1,2, 3}               | Sets the verbosity of the information in the log file. 1=General program execution info. 2=Program flow and status information. 3=Full debugging output |
| -a                          | --append                           | Append new logs to existing log file. Overrides [main] logappend= in dupReport.rc file. |
| -s {‘byte’, ‘mega’, ‘giga’} | --size {‘byte’, ‘mega’, ‘giga’}    | Display file sizes in bytes, megabytes, or gigabytes         |
| -i                          | --initdb                           | Erase all information from the database and resets the tables. |
| -c                          | --collect                          | Collect new emails only and don't run summary report. -c and -t options can not be used together. |
| -t                          | --report                           | Run summary report only and don't collect emails. -c and -t options can not be used together. |
| -b \<DateTimeSpec>          | --rollback \<DateTimeSpec>         | Roll back database to a specified date and time, then continue processing emails. \<DateTimeSpec\> must be in the following format: “\<datespec> \<timespec>”, where \<datespec> and \<timespec> are in the same format specified by the “dateformat=” and “timeformat=” options specified in the [main] section of the dupReport.rc file. For example, if dateformat="MM/DD/YYYY" and timeformat="HH:MM:SS" \<DateTimeSpec> should be set to "12/17/2017 12:37:45". See the discussion of the dateformat= and timeformat= options below. To roll back the database to the beginning of a day, use "00:00:00" for \<timespec>. |
| -B \<DateTimeSpec>          | --rollbackx \<DateTimeSpec>        | Roll back database to a specified date and time. Same operation as -b, except program will exit after rolling back the database. |
| -f \<filespec\>,\<type\>    | --file \<filespec\>,\<type\>       | Send the report to a file in text, HTML, or CSV format. -f may be used multiple times to send the output to multiple files. \<filespec\> can be one of the following: A full path specification for a file; 'stdout', to send to the standard output device; 'stderr', to send to the standard error device. \<type\> can be one of the following: “Txt”, “Html”, or “csv” |
| -F \<filespec\>,\<type\>    | --fileattach \<filespec\>,\<type\> | Functions the same as the -f option, but also attaches the resulting output file to the report email. |
| -x                          | --nomail                           | Do not send the report through email. This is typically used in conjunction with the -f option to save the report to a file rather than send it through email. **NOTE**: If you suppress the sending of emails using '-x' you do not need to enter valid outgoing email server information in the dupReport.rc file. The [outgoing] section still needs to be present in the .rc file, but it does not need valid server or account information. |
| -m \<source> \<destination> | --remove \<source> \<destination>  | Remove a source-destination pair from the database.          |
| -p                          | --purgedb                          | Purge emails that are no longer on the server from the database. Overrides [main] purgedb in .rc file. |
| -w                          | --stopbackupwarn                   | Suppress sending of unseen backup warning emails. Overrides all "nobackupwarn" options in the .rc file. See description of nobackwarn= option in "[report]" and "[source-destination]" sections below. **NOTE**: If you suppress emails using the '-x' option (above) but still want unseen backup warning messages sent (i.e., you *don't* use the '-w' option), you must enter valid email server and account information in the [outgoing] section of the dupReport.rc file. |
| -k                          | --masksensitive                    | Force masking of sensitive data (such as user names, passwords, and file paths) with asterisks (*) in the log file. Overrides the "masksensitive" option in the .rc file. The -k and -K options can not be used together. See description of "masksensitive" option below for more details. |
| -K                          | --nomasksensitive                  | Force display of sensitive data (such as user names, passwords, and file paths) in the log file. Overrides the "masksensitive" option in the .rc file. The -k and -K options can not be used together. See description of "masksensitive" option below for more details. |



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

## [report] section

The [report] section contains settings for the final report created by dupReport.

```
style=srcdest
```

Specifies the type of report for dupReport to create. Allowable report styles are:

- **srcdest**: Backup jobs grouped by source-destination pairs
- **bydest**: Backup jobs grouped by destination systems
- **bysource**: Backup jobs grouped by source systems
- **bydate**: backup jobs grouped by run date

See “Report Formats” below for more information on reporting formats and options.

```
sortby=source
```

Specify how to sort the data within the report specified by the style= parameter

Allowable sorting options are:

- **srcdest**: 'source' or 'destination'
- **bydest**: 'source' or 'date'
- **bysource**: 'destination' or 'date'
- **bydate**: 'source', 'destination', or 'time'

```
reporttitle=Duplicati Backup Summary Report
```

Main report tile used for the report.

```
subheading=Report Subheading
```

Text to use as the subheading of the report. Because the subheading is different for each report there is no default for this option and <u>you will need to manually add it to the .rc file to enable it</u>. If a subheading is not specified in the .rc file, dupReport will supply the following default subheading:

| Report   | Default Subheading                       |
| -------- | ---------------------------------------- |
| srcdest  | Source: \<source>  Destination: \<destination> |
| bydest   | Destination: \<destination>              |
| bysource | Source: \<source>                        |
| bydate   | Date: \<date>                            |

**Keyword Substitution**: You can supply keywords within the subheading= option to customize the way it looks. Available keywords are:

- \#SOURCE#: Inserts the appropriate source name in the subheading
- \#DESTINATION#: Inserts the appropriate destination name in the subheading
- \#DATE#: Inserts the appropriate date in the subheading

For example, in the srcdest report an appropriate subheading might be:

```
subheading = Source System: #SOURCE# Destination System: #DESTINATION#
```

For the bydest report an appropriate subheading might be:

```
subheading = Target Destination: #DESTINATION#
```

Not all keywords are appropriate for all reports. The following table shows what keywords are available to use in the subheading field for each report:

| Report   | Allowable Keywords        |
| -------- | ------------------------- |
| srcdest  | \#SOURCE#  \#DESTINATION# |
| bydest   | \#DESTINATION#            |
| bysource | \#SOURCE#                 |
| bydate   | \#DATE#                   |

```
border=1
```

Size in pixels of the borders in the report table. (HTML only)

```
padding=5
```

Size of cell padding in the report table. (HTML only)

```
displaymessages=false
```

Display any informational messages contained in the Duplicati email. Default is false

```
displaywarnings=true
```

Display any warning messages contained in the Duplicati email. Default is true

```
displayerrors=true
```

Display any error messages in the Duplicati email. Default is 'true'

```
sizedisplay=byte
```

Display file sizes in bytes, megabytes, or gigabytes. Can be overridden by the -s option on the command  line. Default is 'byte'

```
showsizedisplay=true
```

Determine whether to show the size indicator ('MB' or 'GB') in the size columns.

```
repeatheaders=true
```

Indicates whether to repeat the column headers for each report section (true) or only at the beginning of the report (false). Default is 'false'

```
titlebg=#FFFFFF
```

Background color for report title. (HTML only)

```
subheadbg=#D3D3D3
```

Background color for report subheadings. (HTML only)

```
noactivitybg=#FF0000
```

**DEPRECATED as of version 2.2.0.**  This option is no longer referenced in the code and will be removed from the .RC file if found. It has been replaced by the [report] lastseen* set of options. See that description for information on how those options work. 

```
jobmessagebg=#FFFFFF
```

Background color for job messages. (HTML only)

```
jobwarningbgDefault=#FFFF00
```

background color for job warning messages. (HTML only)

```
joberrorbg=#FF0000
```

HTML background color for job error messages. (HTML only)

```
nobackupwarn=5
```

Sets the threshold of the number of days to go without a backup from a source-destination pair before sending a separate email warning. If nobackupwarn is set to 0 no email notices will be sent. The warning email will be sent to the email address specified by the "outreceiver" option in the [outgoing] section unless overridden by a "receiver=" option in a [source-destination] section. 

```
truncatemessage = 0
truncatewarning = 0
truncateerror = 0
```

These settings truncate the message, warning, and error fields generated during backup job execution. Duplicati job messages can be quite lengthy and take up a lot of room in the report. These options allow you to truncate those messages to a reasonable length. A length of 0 (zero) indicates that the message should not be truncated. If the length of the message/warning/error is less than the size indicated, the entire message/warning/error will be displayed. To view the original (full) message string, refer to the email generated for that backup job.

```
nbwsubject = Backup Warning: #SOURCE##DELIMITER##DESTINATION# Backup Not Seen for #DAYS# Days
```

If the threshold defined by nobackupwarn is reached, the string specified by nbwsubject will be used as the subject of the warning email. This can be overridden on a per backupset basis by adding a nbwsubject= option in a [source-destination] section. 

**Keyword Substitution**: You can supply keywords within the nbwsubject option to customize the way it looks. Available keywords are: 

- \#SOURCE# - The source in a source-destination pair
- \#DESTINATION# - The destination in a source-destination pair
- \#DELIMITER# - The delimiter used in a source-destination pair (specified in [main] srcdestdelimiter)
- \#DAYS# - The number of days since the last backup
- \#DATE# - The date of the last backup
- \#TIME# - The time of the last backup

```
lastseenlow= 5
lastseenmed = 10
lastseenlowcolor = #FFFF00
lastseenmedcolor = #FF4500
lastseenhighcolor = #FF0000
```

These options set parameters for displaying "Last Seen" lines in the email report and the optional "Last Seen" Summary table (discussed below). If a known backup set was not seen during the program's run the following line will be added to the result email:

![Last Seen report line](last_seen_line.jpg)

lastseenlow= and lastseenmed= set thresholds for displaying the number of days since a backup has been seen. The lastseen*color= options set background colors for the display. The following chart shows how the thresholds and colors work:

| Comparison                                   | Background Color Display (HTML only)   |
| :------------------------------------------- | :------------------------------------- |
| \# days <= 'lastseenlow'                     | lastseenlowcolor (Defaut: yellow)      |
| \# days > 'lastseenlow' and <= 'lastseenmed' | lastseenmedcolor (Default: orange-red) |
| \# days > 'lastseenmed'                      | lastseenhighcolor (Default: red)       |

```
lastseensummary = none
lastseensummarytitle = Backup Sets Last Seen
```

Add a summary table of all the backup sets and the date they were last seen by dupReport to the final report. An example of the table looks like this:

![last_date_table](last_date_table.jpg)

The default option is 'none' to skip this table. 'top' puts the table at the top of the summary report, 'bottom' places it at the bottom of the summary report. The lastseensummarytitle= option sets a custom title for the table.

```
durationzeroes = true
```

This modifies the display of the backup job "Duration" column in the report. If set to 'true' (the default), job duration will be displayed as "0d 13h 0m 32s." If set to "false", any unit that equals zero (0) will not be displayed, so the previous example will be displayed as "13h 32s."

### **Report color selection:** 

All color specifications in the [report] section follow standard HTML color codes. For a sample list of colors and their HTML codes, please refer to [https://www.w3schools.com/colors/colors_names.asp](https://www.w3schools.com/colors/colors_names.asp)

## [headings] section

The [headings] section contains the default column titles for the fields used in all the dupReport reports. You can alter the headings to suit your tastes. For example, to change the heading for the “size” column from “Size” to “How Big?”, change this:

```
size = Size
```


to this:

```
size = How Big?
```


Once this change is made, any report that displays the “size” column will display the text “How Big?” as the column header.

To prevent a field from displaying on a report, leave the heading specification blank for that field. For example, to prevent the “added” field from displaying on a report, change its line in the [headings] section to:

```
added =
```

| Heading Field    | Notes                                                        |
| ---------------- | ------------------------------------------------------------ |
| source           | The source system for the backup                             |
| destination      | The destination system for the backup                        |
| date             | The date of the backup                                       |
| time             | The time of the backup                                       |
| duration         | The duration of the backup job (days/hours/minutes/seconds). This column can be modified to remove units that equal zero (0) by setting durationzeroes=false in the [report] section. |
| files            | Number of files examined by the backup job                   |
| filesplusminus   | The increase (+) or decrease (-) in the number of files examined since the previous backup |
| jobsize          | The total size of the files examined by the backup           |
| jobsizeplusminus | The increase (+) or decrease (-) in the total size of files examined since the previous backup job |
| added            | Number of blocks added to the backup                         |
| deleted          | Number of blocks deleted from the backup                     |
| modified         | Number of blocks modified by the backup                      |
| errors           | Number of errors encountered during the backup               |
| result           | The final result of the backup job (e.g., Success, Failure, etc) |
| jobmessages      | Messages generated by the backup job during its run. This column can also be suppressed by setting displaymessages=false in the [report] section. |
| jobwarnings      | Warning messages generated by the backup job during its run. This column can also be suppressed by setting displaywarnings=false in the [report] section |
| joberrors        | Error messages generated by the backup job during its run. This column can also be suppressed by setting displayerrors=false in the [report] section |

## [source-destination] sections

Specific options can also be set for each Source-Destination pair in the system. For example, to specify parameters specifically for a backup job named “Client-Server”, there should be a section in the .rc file with the following name:

```
[Client-Server]
```

Note that the section name must match the Source-Destination pair name ***exactly***, including capitalization and delimiter characters. If there is any difference between the Source-Destination job name and the [source-destination] section name, the program will not be able to match the proper parameters to the correct backup job.

Because [source-destination] sections are optional, they must be manually added to the .rc file if they are needed. 

The options currently recognized in the [source-destination] section are:

```
dateformat=
timeformat=
```

The allowable values for these options are the same as the dateformat= and timeformat= options in the [main] section. Specifying date and time formats on a per-job basis allows the program to properly parse and sort date and time results from backups that may be running in different locales and using different date/time display formats. If any of these options are not specified in a [source-destination] section the following fallback options will be used:

| Option      | Fallback Option    |
| ----------- | ------------------ |
| dateformat= | [main] dateformat= |
| timeformat= | [main] timeformat= |

**NOTE:** dateformat= and timeformat= in a [source-destination] section are only applied to the parsing of *incoming* emails. Dates and times produced in the final report are always formatted according to the default dateformat= and timeformat= options in the [main] section.

```
nobackupwarn = 3
nbwsubject = BACKUP WARNING: #SOURCE##DELIMITER##DESTINATION# not being backed up!
receiver = person@mailserver.com
```

These options specify the parameters for warning emails if a backup has not been seen for a period of time. See the descriptions for the [report] section above for allowable values for these options. If any of these options are not specified in a [source-destination] section the following fallback options will be used:

| Option      | Fallback Option         |
| ----------- | ----------------------- |
| nobackwarn= | [report] nobackupwarn=  |
| nbwsubject= | [report] nbwsubject=    |
| receiver=   | [outgoing] outreceiver= |

```
offline = True
```

This suppresses mention of the source-destination pair in the output report. Useful when you know a system is going to be offline for a while and you don't want to see the "not seen in X days" warning message in the report.

```
backupinterval = 1
```

This option can be used if a backup set is run at some interval other than once a day. If a backup from a source/destination pair is not seen while scanning the emails but the number of days since the last backup is less than the backupinterval= value, the program will simply print a notification message rather than the standard warning message. For example (from the 'bydest' report):

![interval_example](interval_example.jpg)

The first line represents a backup that missed its daily execution. The second line represents a backup that only runs every 5 days. If no backupinterval= value is specified in a [source-destination] section, the default is 0.

## [apprise] Section - Apprise Push Notifications 

Beginning with version 2.2.3, dupReport supports the Apprise push notification package from [@caronc](https://github.com/caronc). From the [Apprise GitHub page](https://github.com/caronc/apprise):

> "Apprise allows you to take advantage of just about every notification service available to us today. Send a notification to almost all of the most popular services out there today (such as Telegram, Slack, Twitter, etc). The ones that don't exist can be adapted and supported too!"

Once Apprise is enabled in dupReport, you can send configurable push notifications of backup job status to any service that Apprise supports. Apprise is not required to run dupReport. If you don't want to use Apprise notifications, you can still use all the other features of dupReport without worry.

See the [Apprise GitHub page](https://github.com/caronc/apprise) for instructions on installing Apprise on your system. The installation page also includes instructions for running Apprise directly from the command line. Properly configuring the Apprise URLs for notification can be a tricky business and may involve a lot of trial-and-error before you get it right. Therefore, **<u>we strongly suggest</u>** you test out your Apprise URLs using the command line tool to make sure they work properly **<u>before</u>** trying to use them through dupReport. 

**<u>Notification timing</u>**: Because dupReport runs as a "batch" process and does not receive Duplicati backup job notifications in real time, Apprise notifications will only be sent at the time dupReport is run. For example, if the backup job completes at 1:00 AM but dupReport does not run until 6:00 PM, the Apprise notification will not be sent until 6:00 PM once dupReport has completed its processing.

 Apprise is enabled in dupReport by adding an [apprise] section to the dupReport.rc file. If dupReport sees an [apprise] section in the .rc file it will load the Apprise libraries and configure the proper notifications. If dupReport does not see an [apprise] section in the .rc file it will simply carry on without loading any Apprise support. The [apprise] section contains the following options:

```
services = <service 1>[, <service 2>, <service 3>, …]
```

The services option contains the URL(s) that Apprise will use for its notifications. These are the same URLs that you used when testing Apprise from the command line. For example, if the Apprise command line is: 

```
apprise -t 'my title' -b 'my notification body' '<mailto://myemail:mypass@gmail.com>' 
```

 The services option would be: 

```
services = mailto://myemail:mypass@gmail.com
```

(Note that the "services=" option does not use quotes ('))

If you want to use multiple notification services, separate the URLs for each service with a comma, for example: 

```
services = <mailto://myemail:mypass@gmail.com>, \
pbul://o.gn5kj6nfhv736I7jC3cj3QLRiyhgl98b
```

 

```
title = <title text>
```

This is the text that will be used for the title of the Apprise message. The default title text is: 

*Apprise Notification for #SRCDEST# Backup*

(See the "Keyword Substitution" section below for more information on title text.)

```
body = <body text>
```

This is the text that will be used for the body of the Apprise message. The default body text is:

*Completed at #COMPLETETIME#: #RESULT# - #ERRMSG#*

(See the "Keyword Substitution" section below for more information on body text.)

**Keyword Substitution**: You can supply keywords within the title= and body= options to customize the way it looks. Available keywords are:

- \#SOURCE#: Inserts the backup job's  source      name
- \#DESTINATION#: Inserts the backup job's destination name
- \#SRCDEST#: Inserts the backup job's full \<source>-\<destination> name
- \#RESULT#: Insert's the backup job's result status
- \#MESSAGE#: Inserts the 'Message" field from the status email
- \#WARNMSG#: Inserts the "Warning" message field from the status email
- \#ERRMSG#: Inserts the "Error" message field from the status email
- \#COMPLETETIME#: Inserts the backup job completion time

```
titletruncate = 0
```

Truncates the length of the title field. May be useful for notification services that limit available space in the title field. The default is 0 (no truncation).

```
bodytruncate = 0
```

Truncates the length of the body field. May be useful for notification services that limit available space in the body field. The default is 0 (no truncation).

```
msglevel = failure
```

Indicates the types of messages that dupReport will send to Apprise. This is based on the Parsed Result field from the Duplicati status emails. The following table shows the possible values and their meaning.

| Value   | Types of Messages   Sent      |
| ------- | ----------------------------- |
| success | success, warning, and failure |
| warning | warning and failure           |
| failure | Failure only                  |

**Apprise and Email interaction**: If you want to use email notifications through Apprise instead of direct email from dupReport for notifications, use the '-x' option on the command line to suppress sending of dupReport emails.

**<u>Important Support Note</u>**: dupReport has included Apprise notifications because we feel it would be a useful feature for our users. While we can support and address issues with dupReport's use of Apprise, we cannot provide support for Apprise issues or feature requests. Please contact the Apprise developer directly on the [Apprise GitHub page](https://github.com/caronc/apprise).



# Report Formats

dupReport has several formats for reporting that are specified in the “style” parameter in the [report] section of the dupReport.rc file. Each report can be sorted in various ways. Sorting options are configured using the “sortby” option in the [report] section.

------

**The ‘srcdest’ report**, also known as the “classic” report, displays backup jobs in groups of Source-Destination pairs. Here is an example of the ‘srcdest’ report:

![report_srcdest](report_srcdest.jpg)



------

**The 'bydest' report** displays backup jobs grouped by destination. Here is an example of the ‘bydest’ report:

![report_bydest](report_bydest.jpg)



------

**The ‘bysource’ report** displays backup jobs grouped by source. Here is an example of the ‘bysource’ report:

![report_bysource](report_bysource.jpg)



------

**The ‘bydate’ report** displays backup jobs grouped by the date the jobs were run. Here is an example of the ‘bydate’ report:

![report_bydate](report_bydate.jpg)



