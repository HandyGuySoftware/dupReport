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

![interval_example](D:/Users/parents/Documents/Development/dupReport/docs/interval_example.jpg)

The first line represents a backup that missed its daily execution. The second line represents a backup that only runs every 5 days. If no backupinterval= value is specified in a [source-destination] section, the default is 0.





Return to [Main Page](readme.md)