

# WELCOME TO dupReport

dupReport is an email-based reporting system for Duplicati. It will gather all your Duplicati backup status emails and produce a summary report on what Duplicati backup jobs were run and their success or failure.

Here is a list of some of dupReport's most important features:

- Collects all your Duplicati result emails and produces easy-to-understand status reports
- Runs on multiple operating systems. dupReport has been tested on Linux (Debian 8 & 9) and Windows 10, but users have reported it working on a wide variety of operating systems
- Support for IMAP and POP3 email services (we recommend IMAP for better results)
- Supports both text and JSON status emails from Duplicati
- SSL/TLS support for incoming/outgoing email transmissions.
- Output report supports HTML, Text, CSV, and JSON formats
- User-defined reporting formats with configurable column options
- No limit to  the number of different backup jobs it can track
- Support for Apprise push notification service (<https://github.com/caronc/apprise>)

------

# Available Code Branches

Beginning with release 2.1, the branch structure of the dupReport repository has changed. We have moved to a more organized structure based on [this article by Vincent Driessen](http://nvie.com/posts/a-successful-git-branching-model/) (with some modifications). (Thanks to @DocFraggle for suggesting this structure.)

There are usually only two branches in the dupReport repository:

| Branch Name  | Current Version | Purpose                                                      |
| ------------ | --------------- | ------------------------------------------------------------ |
| **master**   | 3.0.2           | This is the Release branch, which should contain <u>completely stable</u> code. If you want the latest and greatest release version, get it here. If you are looking for an earlier release, tags in this branch with the name "Release_x.x.x" will point you there. |
| **pre_prod** | \<None\>        | The Pre-Production branch. This is a late-stage beta branch where code should be mostly-stable, but no guarantees. Once final testing of code in this branch is complete it will be moved to master and released to the world. If you want to get a peek at what's coming up in the next release, get the code from here. **If you don't see a pre_prod branch in the repository, that means there isn't any beta code available for testing.** |

If you see any additional branches in the repository, they are there for early-stage development or bug fix testing purposes. Code in such branches should be considered **<u>highly unstable</u>**. Swim here at your own risk. Void where prohibited. Batteries not included. Freshest if eaten before date on carton. For official use only. Use only in a well-ventilated area. Keep away from fire or flames. May contain peanuts. Keep away from pets and small children.

Bug reports and feature requests can be made on GitHub in the [Issues Section](https://github.com/HandyGuySoftware/dupReport/issuesdupReport). <u>Please do not issue pull requests</u> before discussing any problems or suggestions as an Issue. 

The discussion group for dupReport is on the Duplicati Forum in [this thread](https://forum.duplicati.com/t/announcing-dupreport-a-duplicati-email-report-summary-generator/1116).

The program is released under an MIT license. Please see the LICENSE file for more details.

Please follow dupReport on Twitter [@dupReport](https://twitter.com/DupReport)

Enjoy!

------

# What's New in Version 3.0

dupReport Version 3.0 includes some new and advanced features for analyzing and reporting on Duplicati emails:

- The reporting engine has been re-built to allow for user-created reporting formats (see the new reporting documentation for more details).
- Added a Guided Setup for new users. If there is no .rc file when the program runs the guided Setup will take the user through the most common configurable options.
- Added the ability to specify multiple inbound (IMAP/POP3) and outbound (SMTP) email servers.
- Standardized log format for easier searching and organization.
- Added ability to send output to syslog server or log aggregator.
- Can now send output to a JSON file.
- Added ability to rollback (-b and -B) to a relative time (e.g., 1w,3h) instead of an absolute date time (i.e., "04/11/2020 8:00:00").
- Re-structured the documentation for better readibility and made it easier to find specific settings.

Please see the (new, updated, and reorganized) documentation on these and all the dupReport features.

------

# Documentation

[What is dupReport?](WhatIsDupreport.md)

[System Requirements](SystemRequirements.md)

[Getting Started (Quickly)](QuickStart.md)

Understanding dupReport

- [Source-Destination Pairs](Config-SrcDestPairs.md)
- [Identifying Emails of Interest](Config-EmailsofInterest.md)

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



