# dupReport Reporting

dupReport contains an advanced reporting engine that allows the user to define the data included in reports, arrange the layout of report sections. This is all handled by managing configuration of .rc file options. No programming is required.

Several sections of the .rc file specify how reports will look and how they are organized:

| Section                                                  | Purpose                                                      |
| -------------------------------------------------------- | ------------------------------------------------------------ |
| [[report]](Reporting-ReportSection.md)                   | Specifies main report operation and default options for report sections |
| [noactivity]                                             | Specifies layout and format options for reporting on which backup jobs were not seen during the run of the program. |
| [lastseen]                                               | Specifies layout and format options for reporting on when all backup jobs were last seen by dupreport. |
| [[\<custom_report_name>]](Reporting-CustomReportSpec.md) | Users can define their own report formats. For each user-defined report there must be a separate section in the .rc file defining the options for that report. |

Click on a section name above to find out more about each section.