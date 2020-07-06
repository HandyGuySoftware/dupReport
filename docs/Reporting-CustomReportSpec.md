# **Defining Custom Report Formats**

dupreport allows you to specify your own custom report formats by creating special [report] sections in the .rc file. Custom report sections have the following general structure:

```
[rptname]
type = report
title = Title for the report
groupby = <column1>:ascending
groupheading = This is the Next Group
columns = <column2>:Column 2, <column3>:Column 3
columnsort = <column2>:ascending
```

------

**Custom Report Options**

```
type = report
```

The *type =* option tells dupReport how to parse the information in the report specification. All custom reports in dupReport have the type "report". If you are defining a custom report, **make sure the type field is set to "report"**. dupReport has other report types that it uses for its own reports (e.g., 'noactivity' and 'lastseen'). 

```
title = Title for the Report
```

This is the title that will be included at the top of the report. The above example will produce the following report:

![](D:\Users\parents\Documents\Development\dupReport\docs\images\TitleExample.jpg)

```
groupby = <column1>:<sortorder>
```

This tells dupReport how to group the data in the report. Reports can be grouped by any of the standard columns (See ["Specifying Report Columns"](Reporting-reportSection.md) for more information)

\<sortorder> tells dupReport how to sort the groups. The only allowable values are:

- **ascending** - sort in alphabetical order (A-Z)
- **descending** - sore in reverse alphabetical order (Z-A)

The example above use the specification: *groupby = destination:ascending*

If you do not want to use groupings in your report you can omit the *groupby=* option in your custom report specification.

```
groupheading = This is the Next Group
```

This specifies the title that will be used for each group. The above example used the specification: *groupheading = Destination: #DESTINATION#*

**Keyword Substitution**: You can supply keywords within the *groupheading =* option to customize the way it looks. Available keywords are:

| Keyword        | Meaning                                                    |
| -------------- | ---------------------------------------------------------- |
| \#SOURCE#      | Inserts the appropriate source name in the subheading      |
| \#DESTINATION# | Inserts the appropriate destination name in the subheading |
| \#DATE#        | Inserts the appropriate date in the subheading             |

If you do not specify a *groupby=* option in your specification you do not need to specify a *groupheading=* option.

```
columns = column2:Column 2, column3:Column 3
```

This specifies the columns used in the report. Reports can use any of the standard columns (See ["Specifying Report Columns"](Reporting-reportSection.md) for more information)

```
columnsort = column2:ascending
```

This specifies the way information in the report is sorted. The format and options are similar to the *groupby =* option above. Multiple sorting columns can be specified, each separated by a comma (',')

------

**Overriding Standard Report Options**

Any custom report specification can change the default option in the [report] section simply by including that option in the custom report section. For example, the [report] section defaults the background color of the title line to white:

```
[report]
titlebg = #FFFFFF
```

If you want the title background to be green, you can specify that for just your custom report:

```
[myreport]
titlebg = #00CC00
```

Most of the options found in the [report] section can be changed by including them as an option in the custom report section.



(Return to [Main Page](readme.md))