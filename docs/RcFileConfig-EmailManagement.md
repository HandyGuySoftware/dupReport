## dupReport.rc File - Email Management

dupReport needs to know where your email servers are located to properly access and parse Duplicati log emails. Email servers can be one of two types:

- **Incoming**: servers that host Duplicati status emails that are read into the program. dupReport can access these systems using either IMAP or POP3 protocols. dupReport will pull mail from as many incoming email servers as you specify, but you must specify at least one incoming email server.
- **Outgoing**: server(s) that you use to send out dupReport results. These servers must be running the SMTP protocol. You can specify more than one outgoing server, but you must specify at least one . dupReport will attempt to connect to the servers - in the order they are specified - until it is able to successfully connect to one. It will then use that outgoing server to send email for the remainder of the program. 

------

**Specifying Email Servers**

The email servers to use are specified in the [main] section of the .rc file:

```
[main]
emailservers = server1, server2, server3
```

You can specify the servers in any order you like. By default, dupReport will create 2 servers, named "incoming" and "outgoing":

```
[main]
emailservers = incoming, outgoing
```

You can also specify the servers you want to use on the command line using the -e option:

```
$ dupReport.py -e incoming,outgoing
```

**NOTE:** If you use the command line option there can not be any spaces between the server names and the commas (,). 

------

**Email Server Specification Sections**

Each email server specified in the *[main]emailservers=* option (or using the -e command line option) must have an associated specification section in the .rc file. For example, your .rc file should look something like this:

```
[main]
emailservers = gmail-imap, yahoo-pop3, gmail-smtp, yahoo-smtp
.
.
.
[gmail-imap]
protocol = imap
.
.
.
[yahoo-pop3]
protocol = pop3
.
.
.
[gmail-smtp]
protocol = smtp
.
.
.
[yahoo-smtp]
protocol = smtp
.
.
.
```

You can name your servers whatever you like, but the names used in the *emailservers=* option **<u>must exactly match</u>** the names used for each of the server specification sections.

------

**Email Server Options**

Each server section uses similar options to describe the server's options. Each option described below will note whether it is needed for IMAP, POP3, and/or SMTP servers

```
protocol=<name>
```

Specify the transport protocol used to connect to the email server. Valid '\<name>' options for incoming servers are 'imap' and 'pop3'. Outgoing servers may only use 'smtp' as the '\<name>' option. dupReport will use this option to determine if this is an "incoming" or "outgoing" server. **(IMAP, POP3, SMTP)** 

**IMAP is highly recommended** for incoming servers. POP3 has some severe limitations when it comes to handling email. If you must use POP3 for whatever reason, make sure the "Leave messages on server" option is enabled in all your POP3 clients and/or your POP3 server. The default behavior for POP3 is to remove messages from the email server as soon as they are read, so using multiple email clients on the same server will interfere with each's ability to read email. Setting this option in your email server tells the server it to leave the messages on the server for other clients to use. Different systems configure this option differently, so check the documentation for your email system to see where this is set.

```
server=localhost
```

DNS name or IP address of email server. **(IMAP, POP3, SMTP)**

```
port=995
```

IMAP, POP3, or SMTP port for incoming email server. Typical values for these ports are:

| Protocol | Port           |
| -------- | -------------- |
| IMAP     | 993            |
| POP3     | 995            |
| SMTP     | 587 (with TLS) |

Your server may use different port numbers. Please contact (or Google) your email provider to see what the values for their systems should be. **(IMAP, POP3, SMTP)**

```
encryption=tls
```

Specify encryption used by incoming email server. Can be set to 'none', 'tls' (the default), or 'ssl' **(IMAP, POP3, SMTP)**

```
account=<account_name>
```

User ID on the email system. **(IMAP, POP3, SMTP)**

***NOTE:*** If you are using Gmail as your incoming email server *and* using POP3 as your transport, put the prefix "recent:" in front of your email address, as in 

> inaccount=recent:user@gmail.com

The Gmail default is to retrieve email starting from the oldest, with a maximum of 250 emails. If you have a large inbox this will cause you to lose the most recent emails. The "recent:" prefix tells Gmail to retrieve the most recent 30 days of email. 

```
password=<password>
```

Password for incoming email system. **(IMAP, POP3, SMTP)**

```
authentication=basic
```

Specifies the type of authentication to be used with the server. Available options are 'basic' and 'oauth'. If you are using Oauth please check with your service provider to identify how to obtain the proper authentication keys. **(IMAP, POP3, SMTP)**

```
folder=INBOX
```

IMAP folder on the incoming email server where Duplicati email is stored. **(IMAP)**

```
keepalive=false
```

Large inboxes may take a long time to scan and parse, and on some systems this can lead to a server connection timeout before processing has completed. This is more likely to happen on the outgoing connection (where there may be long periods of inactivity) than on the incoming connection. However, if you are experiencing timeout errors on your incoming or outgoing server connection, set this value to 'true'. **(IMAP, POP3, SMTP)**

```
unreadonly = false
```

This option instructs the program to only read and parse messages marked as "unread" or "unseen" on the incoming email server. Setting this option to "true" This has the effect of dramatically reducing the time it takes to read your emails, as it only reads messages it hasn't seen yet. **(IMAP)**

There are several things to consider when using this option:

- This option is only effective on IMAP email servers. It has no effect on POP3 servers.
- If any other process or user marks any of the messages on the server as read/seen this will impact dupReport's ability to properly parse all the emails. You should only use this option if dupReport is the only process accessing the IMAP server & folder where the Duplicati emails are stored.
- This option should be used in conjunction with the *markread=* option set to "true" so messages will be marked as read once they are processed by dupReport.
- The seen/unseen flag can be flaky and exhibit different behaviors on different IMAP servers. You should test its usage thoroughly before using it in dupReport.

```
markread = false
```

When set to "true" dupReport will instruct the email server to mark all emails as read/seen once they have been processed by the program. Allowing dupReport to mark all messages as read/seen ("true") will speed up the program by only parsing through emails it has not already seen. 

The default is "false," instructing dupReport to leave the mailbox in the same state as it found it. Setting this option to "false" will slow down processing because dupReport must read all messages in the mailbox looking for messages of interest. However, if you have other programs that use the mailbox or you want to control the read/seen status of your email messages manually, set this option to "false".  **(IMAP)**





(Return to [Main Page](readme.md))