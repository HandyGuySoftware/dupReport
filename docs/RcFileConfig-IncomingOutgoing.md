## dupReport.rc File - Email Management

------

## [incoming] section

The [incoming] section contains settings for incoming email that dupReport reads to create the report. If you are not sure what these settings should be for your email provider, try Googling "\<*email provider*> IMAP settings" or "\<*email provider*> POP3 settings."

```
intransport=imap
```

Specify the transport mechanism used to gather emails from the email server. Valid options are 'imap' or 'pop3'. 

**IMAP is highly recommended**. POP3 has some severe limitations when it comes to handling email. If you must use POP3 for whatever reason, make sure the "Leave messages on server" option is enabled in all your POP3 clients and/or your POP3 server. The default behavior for POP3 is to remove messages from the email server as soon as they are read, so using multiple email clients on the same server will interfere with each's ability to read email. Setting this option in your email server tells the server it to leave the messages on the server for other clients to use. Different systems configure this option differently, so check the documentation for your email system to see where this is set.

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

Specify encryption used by incoming email server. Can be set to 'none', 'tls' (default), or 'ssl'

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

IMAP folder on the email server where incoming Duplicati email is stored. This parameter is ignored for POP3 systems.

```
inkeepalive=false
```

Large inboxes may take a long time to scan and parse, and on some systems this can lead to a server connection timeout before processing has completed. This is more likely to happen on the outgoing connection (where there may be long periods of inactivity) than on the incoming connection. However, if you are experiencing timeout errors on your incoming server connection set this value to 'true'.

```
unreadonly = false
```

This option instructs the program to only read and parse messages marked as "unread" or "unseen" on the email server. This has the effect of dramatically reducing the time it takes to read your emails, as it only reads messages it hasn't seen yet. There are several things to consider when using this option:

- This option is only effective on IMAP email servers. It has no effect on POP3 servers.
- If any other process or user marks any of the messages on the server as read/seen this will impact dupReport's ability to properly parse all the emails. You should only use this option if dupReport is the only process accessing the IMAP server & folder where the Duplicati emails are stored.
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

Specify the encryption used by outgoing email server. Can be set to 'tls' or 'none'

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

>  outsender=Arthur Dent \<adent@galaxy.org>

```
outreceiver=receiver@somemail.com
```

Email address of report recipient. To add a "friendly name" to the receiver's email address, use the form:

> outreceiver=Arthur Dent \<adent@galaxy.org>

To send to multiple recipients, separate the recipients with a comma:

> outreceiver=adent@galaxy.org, Zaphod B \<zbeeblebrox@galaxy.org>

```
outkeepalive=false
```

Large inboxes may take a long time to scan and parse, and on some systems this can lead to a server connection timeout before processing has completed. This is more likely to happen on the outgoing connection (where there may be long periods of inactivity) than on the incoming connection. If you are experiencing timeout errors on your outgoing server connection set this value to 'true'.



(Return to [Main Page](readme.md))