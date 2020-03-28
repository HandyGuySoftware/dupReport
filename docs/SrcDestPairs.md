

# Source-Destination Pairs

dupReport uses "Source-Destination Pairs" to identify the source and destination systems for each backup job. The default dupReport configuration requires that jobs be named in a way that indicates what is being backed up and where it is going. For instance, a job named: “Fred_Home_Desktop-Homers_Minio would show up in the dupReport as:

> **Source:** Fred_Home_Desktop   **Destination:** Homers_Minio

Note that spaces in job names are not supported, at least by the default pattern matching.

Source-Destination pairs are specified in dupReport in the following format: 

```
<Source><delimiter><Destination>
```


Where:

- \<Source\> is a series of alphanumeric characters
- \<delimiter\> is a single character (typically one of the "special" characters) and **CAN NOT** be a character you use in any of your Source-Destination pairs 
- \<Destination\> is a series of alphanumeric characters
- **There can be NO SPACES** in or between the \<Source>, \<delimiter>, and \<Destination> specifications

dupReport allows you to define the format specification of the Source, Destination, and Delimiter in the [main] section of the dupReport.rc file. Each specification is the regular expression definition of that element. The defaults are: 

```
[main]
srcregex=\w\*
destregex=\w\*
srcdestdelimiter=-
```

Together the full source-destination regex is:

```
<srcregex><srcdestdelimiter><destregex> 
```

You can modify the specification of these elements by replacing each with a regular expression defining how dupReport can find that element in a email's subject line. 

***WARNING!*** *dupReport relies on the Source-Destination pair format for all of its operations. If you do not properly specify your Source-Destination pair formats in both the program (through the dupReport.rc file) and in Duplicati (through proper job naming) none of this will work for you. In particular (and repeating what's already been stated) make sure that you **DO NOT INCLUDE ANY SPACES** in or between the \<Source>, \<delimiter>, and \<Destination> specifications in your Duplicati job names.*





Return to [Main Page](readme.md)