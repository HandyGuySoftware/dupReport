## dupReport.rc File - [source-destination] sections

Specific options can also be set for each Source-Destination pair in the system. For example, to specify parameters specifically for a backup job named “Shenjhou-Discovery”, there should be a section in the .rc file with the following name:

```
[Shenjhou-Discovery]
```

**IMPORTANT:** The section name must match the Source-Destination pair name ***exactly***, including capitalization and delimiter characters. If there is any difference between the Source-Destination job name and the [source-destination] section name, the program will not be able to match the proper parameters to the correct backup job.

Because [source-destination] sections are optional, they are not automatically added to the .rc file by the program. You must manually add them to the .rc file if they are needed. 

------

**Date and Time Format Processing**

```
dateformat=
timeformat=
```

These values override any *dateformat=* and *timeformat=* values specified in the [main] section. Specifying date and time formats on a per-job basis allows the program to properly parse and sort date and time results from backups that may be running in different locales and using different date/time display formats. 

The allowable values for these options are the same as the *dateformat=* and *timeformat=* options in the [[main] section](RcFileConfig-Main.md). If either of these options are not specified in a [source-destination] section the equivalent option from the [main] section will be used. 

**NOTE:** *dateformat=* and *timeformat=* in a [source-destination] section are only applied to the parsing of *incoming* emails. Dates and times produced in the final report are always formatted according to the default *dateformat=* and *timeformat=* options in the [main] section.

------

**Warnings for Missing Backups**

```
nobackupwarn = 3
nbwsubject = BACKUP WARNING: #SOURCE##DELIMITER##DESTINATION# not being backed up!
receiver = person@mailserver.com
```

These options specify the parameters for sending out warning emails if a particular backup job has not been seen for a period of time. See the descriptions for these options in the [[report] section](RcFileConfig-ReportSection.md) for allowable values for these options. If any of these options are not specified in a [source-destination] section the following fallback options will be used:

| Option                           | If not found, will use  |
| -------------------------------- | ----------------------- |
| [source-destination] nobackwarn= | [report] nobackupwarn=  |
| [source-destination] nbwsubject= | [report] nbwsubject=    |
| [source-destination] receiver=   | [outgoing] outreceiver= |

------

**Ignore Offline Systems**

```
offline = True
```

This suppresses mention of the source-destination pair in the output report. This is useful when you know a system is offline for a while and you don't want to see the "not seen in X days" warning messages in the report. The source-destination pair will be noted in the "Offline Backup Sets" report.

```
ignore = True
```

This completely ignores any mention of that source-destination pair in either the output reports or warning emails. This is a companion option to the --remove option on the command line. --remove completely removes all traces of that source-destination pair from the database, while the ignore= option leaves it in the database but prevents it from showing up on any reports.

------

**Defining Backup Intervals**

```
backupinterval = 1
```

This option can be used if a back up is scheduled to run less often than dupReport is run. For example, if your "Shenjhou-Discovery" backup runs every seven days but dupReport runs daily, for 6 days in the week you will get a warning notice that "Shenjhou-Discovery" wasn't seen. Setting this option to the number of days between backups for this particular job tells dupReport that it's OK if it doesn't see a backup from that job within that time period. 

If a backup from a source/destination pair is not seen while scanning the emails but the number of days since the last backup is less than the *backupinterval*= value, the program will simply print a notification message rather than the standard warning message. For example:

![](images\interval_example.jpg)

The first line represents a backup that missed its daily execution. The second line represents a backup that only runs every 10 days. If no *backupinterval=* value is specified in a [source-destination] section, the default is 0.





(Return to [Main Page](readme.md))