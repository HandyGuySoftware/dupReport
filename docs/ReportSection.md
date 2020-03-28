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

| Report   | Default Subheading                             |
| -------- | ---------------------------------------------- |
| srcdest  | Source: \<source>  Destination: \<destination> |
| bydest   | Destination: \<destination>                    |
| bysource | Source: \<source>                              |
| bydate   | Date: \<date>                                  |

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

![Last Seen report line](D:/Users/parents/Documents/Development/dupReport/docs/last_seen_line.jpg)

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

![last_date_table](D:/Users/parents/Documents/Development/dupReport/docs/last_date_table.jpg)

The default option is 'none' to skip this table. 'top' puts the table at the top of the summary report, 'bottom' places it at the bottom of the summary report. The lastseensummarytitle= option sets a custom title for the table.

```
durationzeroes = true
```

This modifies the display of the backup job "Duration" column in the report. If set to 'true' (the default), job duration will be displayed as "0d 13h 0m 32s." If set to "false", any unit that equals zero (0) will not be displayed, so the previous example will be displayed as "13h 32s."

### **Report color selection:** 

All color specifications in the [report] section follow standard HTML color codes. For a sample list of colors and their HTML codes, please refer to [https://www.w3schools.com/colors/colors_names.asp](https://www.w3schools.com/colors/colors_names.asp)





Return to [Main Page](readme.md)