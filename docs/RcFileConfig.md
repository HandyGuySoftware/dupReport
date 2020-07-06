# dupReport.rc Configuration

The dupReport.rc file (hereafter, the ".rc file") contains configuration information for dupReport to run properly. Many options in the dupReport.rc file have equivalent command line options. **If an option is specified on both the command line and the .rc file, the command line option takes precedence.**

The .rc file contains several "sections", and each section has the form:

```
[section]
option1 = value1
option2 = value2
option3 = value3
```

"[section]" is the name of the section and  the "option" lines below the section name sets various options for that section. For a complete description of how .rc files are formatted, please see this [Wikipedia Article](https://en.wikipedia.org/wiki/INI_file). The important sections in the dupReport.rc file are:

| Section                                                      | Purpose                                                      |
| ------------------------------------------------------------ | ------------------------------------------------------------ |
| [[main]](RcFileConfig-Main.md)                               | Sets the main program configuration                          |
| \[\<Email Server>]                                           | Sets the configuration for the POP3, IMAP, and SMTP servers. See the section on [Email Management](RcFileConfig-EmailManagement.md) for more information on the configuration of these sections. |
| [[\<source-destination>]](RcFileConfig-SourceDestination.md) | Sets specific operating configuration options for the backup job named "\<source-destination>" |
| [[apprise]](RcFileConfig-Apprise.md)                         | Set configuration options for the Apprise notification service |
| [[report]](Reporting-ReportSection.md)                       | Sets the default configuration for the reporting system      |
| [[\<report_name>]](Reporting-CustomReportSpec.md)            | Sets specific configuration options for user-defined custom reports |

Click the section name in the table above to see more information on how to configure that section.





(Return to [Main Page](readme.md))