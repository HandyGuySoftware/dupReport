## dupReport.rc File - [apprise] Section  & Push Notifications 

Beginning with version 2.2.3, dupReport supports the Apprise push notification package from [@caronc](https://github.com/caronc). From the [Apprise GitHub page](https://github.com/caronc/apprise):

> "Apprise allows you to take advantage of just about every notification service available to us today. Send a notification to almost all of the most popular services out there today (such as Telegram, Slack, Twitter, etc). The ones that don't exist can be adapted and supported too!"

Once Apprise is enabled in dupReport, you can send configurable push notifications of backup job status to any service that Apprise supports. Apprise is not required to run dupReport. If you don't want to use Apprise notifications, you can still use all the other features of dupReport without worry.

See the [Apprise GitHub page](https://github.com/caronc/apprise) for instructions on installing Apprise on your system. The installation page also includes instructions for running Apprise directly from the command line. Properly configuring the Apprise URLs for notification can be a tricky business and may involve a lot of trial-and-error before you get it right. Therefore, **<u>we strongly suggest</u>** you test out your Apprise URLs using the command line tool to make sure they work properly **<u>before</u>** trying to use them through dupReport. 

**<u>Notification timing</u>**: Because dupReport runs as a "batch" process and does not receive Duplicati backup job notifications in real time, Apprise notifications will only be sent at the time dupReport is run. For example, if the backup job completes at 1:00 AM but dupReport does not run until 6:00 PM, the Apprise notification will not be sent until 6:00 PM once dupReport has completed its processing.

Apprise is enabled in dupReport by adding an [apprise] section to the dupReport.rc file. If dupReport sees an [apprise] section in the .rc file it will load the Apprise libraries and configure the proper notifications. If dupReport does not see an [apprise] section in the .rc file it will simply carry on without loading any Apprise support. 

**<u>Important Support Note</u>**: dupReport includes Apprise notifications because we feel it is a useful feature for our users. While we can support and address issues with dupReport's use of Apprise, we cannot provide support for Apprise issues or feature requests. Please contact the Apprise developer directly on the [Apprise GitHub page](https://github.com/caronc/apprise).

------

**Defining Notification Services**

```
services = <service 1>[, <service 2>, <service 3>, …]
```

The services option contains the URL(s) that Apprise will use for its notifications. These are the same URLs that you used when testing Apprise from the command line. For example, if the Apprise command line is: 

> apprise -t 'my title' -b 'my notification body' '<mailto://myemail:mypass@gmail.com>' 

 The services option in the dupReport.rc file would be: 

```
services = mailto://myemail:mypass@gmail.com
```

(Note that the "services=" option in the .rc file does not use quotes ('))

If you want to use multiple notification services, separate the URLs for each service with a comma, for example: 

```
services = <mailto://myemail:mypass@gmail.com>, pbul://o.gn5kj6nfhv736I7jC3cj3QLRiyhgl98b
```

------

**Adding a Message Title**

```
title = <title text>
```

This is the text that will be used for the title of the Apprise message. The default title text is: 

*Apprise Notification for #SRCDEST# Backup*

(See the "Keyword Substitution" section below for more information on title text.)

------

**Specifying the Message Body**

```
body = <body text>
```

This is the text that will be used for the body of the Apprise message. The default body text is:

*Completed at #COMPLETETIME#: #RESULT# - #ERRMSG#*

(See the "Keyword Substitution" section below for more information on body text.)

------

**Keyword Substitution**

You can supply keywords within the title= and body= options to customize the way it looks. Available keywords are:

- \#SOURCE#: Inserts the backup job's source name
- \#DESTINATION#: Inserts the backup job's destination name
- \#SRCDEST#: Inserts the backup job's full \<source>-\<destination> name
- \#RESULT#: Insert's the backup job's result status
- \#MESSAGE#: Inserts the 'Message" field from the status email
- \#WARNMSG#: Inserts the "Warning" message field from the status email
- \#ERRMSG#: Inserts the "Error" message field from the status email
- \#COMPLETETIME#: Inserts the backup job completion time

------

**Truncating Long Titles and Messages**

```
titletruncate = 0
```

Truncates the length of the title field. May be useful for notification services that limit available space in the title field. The default is 0 (no truncation).

```
bodytruncate = 0
```

Truncates the length of the body field. May be useful for notification services that limit available space in the body field. The default is 0 (no truncation).

------

**Specifying the Types of Messages to Send**

```
msglevel = failure
```

Indicates the types of messages that dupReport will send to Apprise. This is based on the Parsed Result field from the Duplicati status emails. The following table shows the possible values and their meaning.

| Value              | Types of Messages   Sent      |
| ------------------ | ----------------------------- |
| msglevel = success | success, warning, and failure |
| msglevel = warning | warning and failure           |
| msglevel = failure | Failure only                  |

------

**Using Apprise for Email Notification**

If you want to use email notifications through Apprise instead of direct email from dupReport for notifications, use the '-x' option on the command line to suppress sending of dupReport emails.





(Return to [Main Page](readme.md))