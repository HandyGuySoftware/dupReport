

# Source-Destination Pairs

The heart of dupReport's functionality is the use of "Source-Destination Pairs" to identify the source and destination systems for each backup job. The default dupReport configuration requires that Duplicati backup jobs be named in a way that indicates what is being backed up and where it is going. For instance, a Duplicati backup job named: “MediaServer-NAS" would show up in dupReport as:

> **Source:** MediaServer   **Destination:** NAS

Source-Destination pairs are used in dupReport in the following format: 

```
<Source><Delimiter><Destination>
```


Where:

- \<Source\> is a series of alphanumeric characters
- \<Delimiter\> is a single character (typically one of the "special" characters like !,@,#,$,-,*, etc.) and **CAN NOT** be a character you use in any of your Source or Destination names 
- \<Destination\> is a series of alphanumeric characters

Spaces are allowed in the \<Source>, \<Delimiter>, and \<Destination> if you define these specifications carefully, *though they are not recommended*, at least when you are just starting out.

**<u>Regular Expressions</u>**

dupReport uses *Regular Expressions* (also known as "regex") to define the source, destination, and delimiter specifications. Regular expressions allow you to specify patterns of characters in a shorthand way so you can match those patterns against a variety of text. If you are not familiar with regular expressions, you have two options:

1. **Accept the defaults**. In the default dupReport configuration the Source and Destination each consist of a single string of characters without spaces and the delimiter is the '-' character (for example, "MediaServer-NAS".) If you name all your backup jobs this way your Duplicati emails should be processed properly. No additional regular expression knowledge is needed on your part.
2. **Learn about regular expressions**. Building your skill set is always a good thing. You can start at [RegexOne](https://regexone.com/) (not an endorsement, just a good site), though there are lots of good regular expressions tutorials on the Internet. dupReport is written in Python, if you are looking for a language-specific tutorial.

<u>**Specifying Source, Destination, and Delimiter**</u>

The full source-destination regex specification is:

```
<Source Regex><Delimiter Regex><Destination Regex> 
```

dupReport allows you to define the Source, Destination, and Delimiter regular expressions in the [main] section of the dupReport.rc file. The defaults are: 

```
[main]
srcregex=\w+
destregex=\w+
srcdestdelimiter=-
```

| Option           | Defintion | Meaning                                                      |
| ---------------- | --------- | ------------------------------------------------------------ |
| srcregex         | \w+       | a single string of one or more alphanumeric characters (i.e., A-Z, a-z, 0-9, and the underscore character'_') |
| destregex        | \w+       | a single string of one or more alphanumeric characters (i.e., A-Z, a-z, 0-9, and the underscore character'_') |
| srcdestdelimiter | -         | The '-' character                                            |

Note that whitespace characters (space, tab, newlines, etc.) are **not** allowed in Source or Destination names using this default definition. If the Source or Destination systems in your Duplicati backup job names contain white space characters they will not match the expression.

Using these definitions, the full Backup name dupReport will look for (\<Source Regex>\<Delimiter Regex>\<Destination Regex>) is:

(\w+)-(\w+)

With this specification, the following list explains what will match and not match:

**Will Match**

- MediaServer-NAS
- WebServer-GDrive
- Development-B2

**Will Not Match**

- Media Server-NAS (space in Source name)
- WebServer-G Drive (space in Destination name)
- Development - B2 (space surrounding the delimiter character)
- System Backup (no delimiter character to define the Destination system)



If you want to get a bit more creative and allow space characters in your Source or Destination systems you can change the Source or destination to the following:

```
[main]
srcregex=[^-]+
destregex=.+
srcdestdelimiter=-
```

| Option           | Defintion | Meaning                                                      |
| ---------------- | --------- | ------------------------------------------------------------ |
| srcregex         | [^-]+     | One or more characters up to (but not including) the '-' character |
| destregex        | .+        | All characters up to the end of the line                     |
| srcdestdelimiter | -         | The '-' character                                            |

Using these definitions, the full Backup name dupReport will look for (\<Source Regex>\<Delimiter Regex>\<Destination Regex>) is:

(\[^-]\+)-(.+)

With this specification, the following list explains what will match and not match:

**Match**

- Media Server-NAS
- WebServer-G Drive
- Computer Under This Desk-Computer Under Other Desk

**Will Not Match**

- Media Server - NAS (OK, this will *technically* work, but your Source name will have an extra space at the end and your Destination system will have an extra space at the beginning. This has the potential to confuse things down the road.)



If you want to allow spaces anywhere in the Source-Destination specification, you can try something like the following:

```
[main]
srcregex=[^-]+
destregex=.+
srcdestdelimiter= \s*-\s*
```

| Option           | Defintion | Meaning                                                      |
| ---------------- | --------- | ------------------------------------------------------------ |
| srcregex         | [^-]*     | One or more characters up to (but not including) the '-' character |
| destregex        | .+        | One or more characters up to the end of the line             |
| srcdestdelimiter | \s\*-\s\* | An arbitrary number of spaces, followed by the '-' character, followed by an arbitrary number of spaces |



**<u>A WORD OF CAUTION</u>**

Using advanced regex patterns to match your Duplicati backup job names can get extremely tricky and the results can be unexpected. The best advice is to keep your naming convention as simple as possible (i.e., "Source-Destination") and things will work much better. dupReport relies on the Source-Destination pair format for all of its operations. If you do not properly specify your Source-Destination pair formats in both the program (through the dupReport.rc file) and in Duplicati (through proper job naming) none of this will work for you.

If you want to proceed with using advanced regular expressions in dupReport, you should use a good regular expression testing program to thoroughly test your regexes and understand how they work before using them in the program. [Regex101](https://regex101.com/) is a good site to use, though there are many others available on the Internet.



# Identifying Emails of Interest

dupReport scans the incoming mailbox looking for backup job emails. However, there may be hundreds (or thousands) of emails in the inbox, only a few of which contain information about Duplicati backup jobs. dupReport identifies "Emails of Interest" by matching the email's subject line against a pattern defined in the dupReport.rc file. If the pattern matches, the email is analyzed. If the pattern does not match, the email is ignored. 

You can specify the text that dupReport tries to match by adjusting the subjectregex= option in the [main] section of the dupReport.rc file. subjectregex is the regular expression definition for the desired phrase. 

The default for this option is: 

```
[main]
subjectregex=^Duplicati Backup report for 
```

This instructs dupReport to look for emails whose subject line start with the phrase, "Duplicati backup report for", which is the default used in Duplicati's “send-mail-subject” advanced option. 

If you change the subjectregex option in the dupReport.rc file, or change the "send-mail-subject" advanced option in Duplicati, be sure that the two patterns match or you will not be able to properly match incoming emails.

For example, Duplicati allows you to change the "send-mail-subject" to:

```
Duplicati %PARSEDRESULT%, %OPERATIONNAME% report for %backup-name%
```

This can result in an email with the subject line:

```
Duplicati Warning, Backup report for FileServer-B2
```

In this case, you would change the subjectregex option in the dupReport.rc file to:

```
subjectregex=^Duplicati ([\w ]*, |)Backup report for
```



(Return to [Main Page](readme.md))