

# WELCOME TO dupReport

dupReport is a Python-based email collection and reporting system for Duplicati. It will gather all your Duplicati backup status emails and produce a summary report on what Duplicati backup jobs were run and their success or failure.

Here is a list of some of dupReport's most important features:

- Collects all your Duplicati result emails and produces easy-to-understand status reports
- Runs on multiple operating systems. dupReport has been tested on Linux (Debian 8 & 9) and Windows 10, but users have reported it working on a wide variety of operating systems
- A Guided Setup for new users. If there is no configuration (.rc) file when the program runs, the Guided Setup will take the user through the most common configurable options.
- Support for IMAP and POP3 email services (IMAP is recommended for better results)
- Support for using multiple inbound (IMAP/POP3) and outbound (SMTP) email servers.
- Supports both text and JSON formatted status emails from Duplicati
- Supports SSL/TLS support for incoming/outgoing email transmissions.
- Output report in HTML, Text, CSV, and JSON formats
- Send results to email or local files (or both)
- User-defined reporting formats with configurable column and organization options
- Syslog-style logging format for easier searching and organization.

- Ability to send log output to an external syslog server or log aggregator.
- Support for the Apprise push notification service (<https://github.com/caronc/apprise>)

Please see the (new, updated, and reorganized) documentation on these and all the dupReport features.

------

# Available Code Branches

Beginning with release 2.1, the branch structure of the dupReport repository has changed. We have moved to a more organized structure based on [this article by Vincent Driessen](http://nvie.com/posts/a-successful-git-branching-model/) (with some modifications). (Thanks to @DocFraggle for suggesting this structure.)

There are usually only two branches in the dupReport repository:

| Branch Name  | Current Version | Purpose                                                      |
| ------------ | --------------- | ------------------------------------------------------------ |
| **master**   | 3.0.9           | This is the Release branch, which should contain <u>completely stable</u> code. If you want the latest and greatest release version, get it here. If you are looking for an earlier release, tags in this branch with the name "Release_x.x.x" will point you there. |
| **pre_prod** | \<None\>        | The Pre-Production branch. This is a late-stage beta branch where code should be mostly-stable, but no guarantees. Once final testing of code in this branch is complete it will be moved to master and released to the world. If you want to get a peek at what's coming up in the next release, get the code from here. **If you don't see a pre_prod branch in the repository, that means there isn't any beta code available for testing.** |

If you see any additional branches in the repository, they are there for early-stage development or bug fix testing purposes. Code in such branches should be considered **<u>highly unstable</u>**. Swim here at your own risk. Void where prohibited. Batteries not included. Freshest if eaten before date on carton. For official use only. Use only in a well-ventilated area. Keep away from fire or flames. May contain peanuts. Keep away from pets and small children.

Bug reports and feature requests can be made on GitHub in the [dupReport Issues Section](https://github.com/HandyGuySoftware/dupReport/issuesdupReport). <u>Please do not issue pull requests</u> before discussing any problems or suggestions as an Issue. 

The discussion group for dupReport is on the Duplicati Forum in [this thread](https://forum.duplicati.com/t/announcing-dupreport-a-duplicati-email-report-summary-generator/1116).

The program is released under an MIT license. Please see the LICENSE file for more details.

Enjoy!



------

# Documentation

[What is dupReport?](WhatIsDupreport.md)

[System Requirements](SystemRequirements.md)

[Getting Started (Quickly)](QuickStart.md)

[Understanding Source-Destination Pairs and Identifying Emails of Interest](Config-SrcDestPairs.md) 

Running dupReport

- [Installation](Installation.md)

- [Command Line Options](CommandLine.md)

[dupReport.rc File Configuration](RcFileConfig.md)

- Program Management: The [[main] Section](RcFileConfig-Main.md)
- Handling Specific Backup Jobs: The [[\<source-destination>] Sections](RcFileConfig-SourceDestination.md)
- [Email Management](RcFileConfig-EmailManagement.md)
- Push Notifications Using Apprise: The [[apprise] Section](RcFileConfig-Apprise.md)

Reporting

- [The [report] Section](Reporting-ReportSection.md)
- [Custom Report Formats](Reporting-CustomReportSpec.md)



