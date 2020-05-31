# Installing dupReport

dupReport installation is easy and quick. To begin, download the dupReport files from the GitHub repository and place them in the directory of your choice. Then, make sure Python 3 is installed on your system and operating correctly.

## First-time Installation - Guided Setup

Installing dupReport is easy. To use all the default values, execute the following command:

| Operating System | Command Line                                                |
| ---------------- | ----------------------------------------------------------- |
| Linux            | **user@system:~$** /path/to/dupReport/dupReport.py          |
| Windows          | **C:\users\me>** python.exe \path\to\dupreport\dupReport.py |

dupReport is self-initializing, so the first time you run the program the program will automatically create a database, initialize the .rc configuration file with a bunch of default values, then exit. By default, the database and .rc files will be created in the same directory where the dupReport.py script is located. If you want them created in another location use the following program options:

```
dupReport.py -r <RC_Path> -d <Database_Path>
```

You can specify either a directory or a full path name for the \<RC_Path> and \<Database_Path> options. dupReport will create the .rc and database files in their respective paths. If the directories do not already exist or you do not have read and write access permission to those locations the program will exit with an error message. Use of the default values for these file paths is recommended, but the option is there if you want it.

The first time the program is run it will launch the Guided Setup to assist you in filling in some of the basic configuration options. The Guided Setup will ask a series of questions about how you want the program to operate, where your email servers are, and how to log into them.  Defaults for each question ate provided in brackets ([]). If you hit 'Enter' without responding to a question it will take the default response as your answer.

Here is an explanation for each question in the Guided Setup:

```
Welcome to the dupReport guided setup.
Here we'll collect some basic information from you to help configure the program.
Let's get started...

Valid date formats in dupReport are:
        YYYY/MM/DD
        DD/MM/YYYY
        YYYY/DD/MM
        YYYY.MM.DD
        YYYY-DD-MM
        MM.DD.YYYY
        DD-MM-YYYY
        MM/DD/YYYY
        YYYY-MM-DD
        MM-DD-YYYY
        YYYY.DD.MM
        DD.MM.YYYY
Please enter the date format for your locale [MM/DD/YYYY]: DD/MM/YYYY
```

Since most of what dupReport does involves interpreting date & time strings it's important that it knows what date format you use in your locale. There are a limited number of format options, so select the one that use use for most of your systems. If you work with multiple systems that use different date formats you can specify this on a per-system basis in the .rc file later on.

```
Do you use a syslog server or log aggregator where you want the dupReport logs sent [n]: y
Enter the server name/ip and port of your syslog server [localhost:514]:syslog.localnet.com: 516
```

If you want to forward dupReport's log output to a syslog server or log aggregator you can specify the system (IP address or FQDN) and port number here.

```
Do you want file sizes displayed in bytes, megabytes, or gigabytes (enter 'byte', 'mb', or 'gb') [byte]: gb
```

Self-explanatory, hopefully. Since backup sizes can get quite large, this helps compact the report a bit by rounding the file & backup sizes to megabytes or gigabytes.

```
Now we'll need information about your 'incoming' email server.
This is the email server where your Duplicati job results are sent. dupReport will collect emails from this server and analyze them.
You can use more than one incoming server with dupReport, but for now we'll collect information for just one.
Does the 'incoming' server use IMAP or POP3 [imap]: imap

```

```
Please provide an IP address or DNS name for the 'incoming' server [localhost]: imap.gmail.com
Please provide a port number for the 'incoming' server [993]: 
Does the 'incoming' server use SSL/TLS encryption [Y]: 
```

These questions et the backs server & port options for the incoming server & indicates if TLS/SSL is required.

```
Please enter the user ID used to log into the 'incoming' server [youremail@emailservice.com]: sampleid@gmail.com
Please enter the password used to log into the 'incoming' server [secretpassword]:
```

This is the user ID and password you use to log into the incoming server. dupReport needs these to log in and retrieve Duplicati emails from your account. Your password will not be displayed on the console.

```
Please enter the IMAP folder name to where Duplicati emails are stored on the 'incoming' server [INBOX]: INBOX
```

If your server uses IMAP you need to specify the folder where the  email is stored. (Note: Gmail uses the term 'tags'). This option is only needed for IMAP systems. If you told dupReport you are using POP3 yo will not see this question.

```
Now we'll need information about your 'outgoing' email server.
This is the email server that dupReport will use to send the results of its analysis.
You can use more than one outgoing server with dupReport, but for now we'll collect information for just one.
Please provide an IP address or DNS name for the 'outgoing' server [localhost]: smtp.gmail.com
Please provide a port number for the 'outgoing' server [587]: 
Does the 'outgoing' server use SSL/TLS encryption [Y]: 
Please enter the user ID used to log into the 'outgoing' server [youremail@emailservice.com]: sampleid@gmail.com
Please enter the password used to log into the 'outgoing' server [secretpassword]: 

```

These options mean the same thing as they did for the 'incoming' server questions. Most likely you will use the same system for both incoming and outgoing emails, in which case your answers here will be the same as they were for the 'incoming' section.

```
What email address should be used for the sender [youremail@emailservice.com]: myid@gmail.com
What is the 'friendly name' of the outgoing email sender [Your Name]: dupReport Summary
```

This tells dupReport what to put in for the "sent from" fields in the outgoing email report.  

```
Who should the outgoing emails be sent to [receiver@emailservice.com]:myid@gmail.com
```

This tells dupReport where the resulting report email goes.

```
OK, all set. We've recorded your responses and (hopefully) the program will work perfectly now
If it doesn't, you can change the configuration in the .rc file located at /home/user/dupReport/dupReport.rc
```

More information on the .rc file configuration can be found in the [“dupReport .rc File Configuration” section](RcFileConfig.md).

## Upgrading From a Previous Version

If you have been running an earlier version of dupReport, the program will automatically update the dupReport.rc file and the dupReport.db database to the latest versions. Depending on the extent of the changes, the program may indicate that you need to edit the dupReport.rc file to set any new options correctly. 

Beginning with Version 3.0.0, dupReport will automatically make a backup of your database (.db) and configuration (.rc) file before the upgrade in case something goes wrong during the process. However, as a precaution **it is always recommended that you backup your .rc and .db files yourself and keep them in a safe place** before proceeding with the upgrade until you're sure everything is working properly.





(Return to [Main Page](readme.md))