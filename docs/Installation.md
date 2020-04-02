# Installing dupReport

dupReport installation is easy and quick. To begin, download the dupReport files from the GitHub repository and place them in the directory of your choice. Then, make sure Python 3 is installed on your system and operating correctly.

## First-time Installation

Installing dupReport is easy. To use all the default values, execute the following command:

| Operating System | Command Line                                                |
| ---------------- | ----------------------------------------------------------- |
| Linux            | **user@system:~$** /path/to/dupReport/dupReport.py          |
| Windows          | **C:\users\me>** python.exe \path\to\dupreport\dupReport.py |

dupReport is self-initializing, so the first time you run the program the program will automatically create a database, initialize the .rc configuration file with a bunch of default values, then exit. By default, the database and .rc files will be created in the same directory where the dupReport.py script is located. If you want them created in another location use the following program options:

```
dupReport.py -r <RC_Path> -d <Database_Path>
```

You can specify either a directory or a full path name for the \<RC_Path> and \<Database_Path> options. dupReport will create the .rc and database files in their respective paths. If the directories do not already exist or you do not have read and write access permission to those locations the program will exit with an error message. Use of the default values for these file paths is recommended, but the option is there if you want it.

The only thing dupReport can't set defaults for is the technical specifics about your incoming and outgoing mail servers (for example, the name/IP address, user ID, password, transport, encryption, etc.). These are specified in the [incoming] and [outgoing] sections of the .rc file. Once you edit those entries in the .rc file everything should work like magic. Probably.

More information on the .rc file configuration can be found in the [“dupReport .rc File Configuration” section](RcFileConfig.md).

## Upgrading From a Previous Version

If you have been running an earlier version of dupReport, the program will automatically update the dupReport.rc file and the dupReport.db database to the latest versions. Depending on the extent of the changes, the program may indicate that you need to edit the dupReport.rc file to set any new options correctly. 

Beginning with Version 3.0.0, dupReport will automatically make a backup of your database (.db) and configuration (.rc) file before the upgrade in case something goes wrong during the process. However, as a precaution **it is always recommended that you backup your .rc and .db files yourself and keep them in a safe place** before proceeding with the upgrade until you're sure everything is working properly.





(Return to [Main Page](readme.md))