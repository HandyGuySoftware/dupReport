

## dupReport Command Line

Once all the options have been set in the .rc file, use the following commands to run dupReport normally:

| Operating System | Command Line                                                 |
| ---------------- | ------------------------------------------------------------ |
| Linux            | **user@system:~$** /path/to/dupReport/dupReport.py \<options> |
| Windows          | **C:\users\me>** python.exe \path\to\dupreport\dupReport.py \<options> |

Command line options alter the way dupReport operates. Many command line options have equivalent options in the dupReport.rc file. **If an option is specified on both the command line and in the .rc file, the command line option takes precedence.**

dupReport has the following command line options:

| Short Version               | Long Version                                | Function                                                     | Notes                                                        |
| --------------------------- | ------------------------------------------- | :----------------------------------------------------------- | ------------------------------------------------------------ |
| -a                          | --append                                    | Append new logs to existing log file.                        | Overrides [main] logappend= in dupReport.rc file.            |
| -b \<DateTimeSpec>          | --rollback \<DateTimeSpec>                  | Roll back database to a specified date and time, then continue processing emails. \<DateTimeSpec\> must be in the following format: “\<datespec> \<timespec>”, where \<datespec> and \<timespec> are in the same format specified by the “dateformat=” and “timeformat=” options specified in the [main] section of the dupReport.rc file. For example, if dateformat="MM/DD/YYYY" and timeformat="HH:MM:SS" \<DateTimeSpec> should be set to "12/17/2017 12:37:45". | See the discussion of the **dateformat**= and **timeformat=** options in ["dupReport.rc file configuration."](RcFileConfig.md) To roll back the database to the beginning of a day, use "00:00:00" for \<timespec>. |
| -B \<DateTimeSpec>          | --rollbackx \<DateTimeSpec>                 | Roll back database to a specified date and time.             | Same operation as -b, except program will exit after rolling back the database. |
| -c                          | --collect                                   | Collect new emails only and don't run summary report.        | **-c** and **-t** options can not be used together.          |
| -d \<dbpath\>               | --dbpath \<dbpath\>                         | Sets \<dbpath\> as the directory or full path specification where the dupReport.rc file is located. | Overrides the [main] dbpath= option in dupReport.rc file. You must have read and write access to the place where \<dbpath> points. |
| -f \<filespec\>,\<type\>    | --file \<filespec\>,\<type\>                | Send the report to a file in text, HTML, CSV, or JSON format. \<filespec\> can be one of the following: A full path specification for a file; 'stdout', to send to the standard output device; 'stderr', to send to the standard error device. \<type\> can be one of the following: “txt”, “html”, “csv”, or "json" | -f may be used multiple times to send the output to multiple files. **Do not** leave a space between the comma (,) and the \<type>  specification. |
| -F \<filespec\>,\<type\>    | --fileattach \<filespec\>,\<type\>          | Functions the same as the -f option, but also attaches the resulting output file to the report email. |                                                              |
| -h                          | --help                                      | Display command line options.                                |                                                              |
| -i                          | --initdb                                    | Erase all information from the database and resets all the tables. |                                                              |
| -k                          | --masksensitive                             | Force masking of sensitive data (such as user names, passwords, and file paths) with asterisks (*) in the log file. | Overrides the "masksensitive" option in the .rc file. The -k and -K options can not be used together. See description of "masksensitive" option for more details. |
| -K                          | --nomasksensitive                           | Force display of sensitive data (such as user names, passwords, and file paths) in the log file. | Overrides the "masksensitive" option in the .rc file. The -k and -K options can not be used together. See description of "masksensitive" option for more details. |
| -l \<logpath\>              | --logpath \<logpath\>                       | Sets \<logpath\> as the directory or full path specification where the dupReport.log file is located. | Overrides the [main] logpath= option in dupReport.rc file. You must have read and write access to the place where \<logpath> points. |
| -m \<source> \<destination> | --remove \<source> \<destination>           | Remove a source-destination pair from the database.          |                                                              |
| -o                          | --validatereport                            | Validate the report file for syntax and accuracy, then exit the program. | Useful for debugging new custom report specifications.       |
| -p                          | --purgedb                                   | Purge emails that are no longer on the server from the database. | Overrides [main] purgedb in .rc file.                        |
| -r \<rcpath\>               | --rcpath \<rcpath\>                         | Sets \<rcpath\> as the directory or full path specification where the dupReport.rc file is located. | You must have read and write access to the place where \<rcpath> points. |
| -s {‘none’, ‘mb’, ‘gb’}     | --size {‘none’, ‘mb’, ‘gb’}                 | Instructs the program to round file sizes to standard units: bytes ('none'), megabytes ('mb'), or gigabytes ('gb') |                                                              |
| -t                          | --report                                    | Run summary report only and don't collect emails.            | **-c** and **-t** options can not be used together.          |
| -v {0,1,2, 3}               | --verbose {0,1,2, 3}                        | Sets the verbosity of the information in the log file.       | 1=General program execution info. 2=Program flow and status information. 3=Full debugging output |
| -V                          | --Version                                   | Prints version information for dupReport and supporting components |                                                              |
| -w                          | --stopbackupwarn                            | Suppress sending of unseen backup warning emails. Overrides all "nobackupwarn" options in the .rc file. See description of nobackwarn= option in ["[report] Section"](ReportSection.md) and ["[source-destination] Sections"](SourceDestinationSection) . |                                                              |
| -x                          | --nomail                                    | Do not send the report through email. This is typically used in conjunction with the -f or to save the report to a file rather than send it through email. | **NOTE 1**: If you suppress the sending of emails using '-x' you do not need to enter valid outgoing email server information in the dupReport.rc file. The [outgoing] section still needs to be present in the .rc file, but it does not need valid server or account information. **NOTE 2**: If you suppress the sending of emails using the '-x' option but still want unseen backup warning messages sent (i.e., you *don't* use the '-w' option), you must enter valid email server and account information in the [outgoing] section of the dupReport.rc file. |
| -y                          | --layout \<rptname>[,\<rptname>,\<rptname>] | Run specified reports during the program run.                | The named reports must be specified in the .rc file or the program will exit with an error. Using this option overrides the *layout=* option in the [report] section of the .rc file. **DO NOT** leave any spaces between the report names or the commas. |



(Return to [Main Page](readme.md))