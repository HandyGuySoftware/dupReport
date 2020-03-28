# Installing dupReport

dupReport installation is easy and quick. To begin, download the dupReport files from the GitHub repository and place them in the directory of your choice. Then, make sure Python 3 is installed on your system and operating correctly.

## First-time Installation

Installing dupReport is easy. To use all the default values, execute the following command:

```
Linux systems: user@system:~$ /path/to/dupReport/dupReport.py
```

```
Windows Systems: C:\users\me> python.exe \path\to\dupreport\dupReport.py
```

dupReport is self-initializing, and running the program for the first time creates the database, initializes the .rc file with a bunch of default values, then exits. By default, the database and .rc files will be created in the same directory where the dupReport.py script is located. If you want them created in another location use the following program options:

```
dupReport.py -r <RC_Directory> -d <Database_Directory>
```

dupReport will create the .rc and database files in their respective paths. Both directories must already exist and you must have read and write access permissions to those locations. Use of the default values for these file paths is recommended, but the option is there if you want it.

The only thing dupReport can't set defaults for is the technical specifics about your incoming and outgoing mail servers (for example, the name/IP address, user ID, password, transport, encryption, etc.). These are specified in the [incoming] and [outgoing] sections of the .rc file. Once you edit those entries in the .rc file everything should work like magic. Probably.

More information on the .rc file configuration can be found below under “RC File Configuration.”

## Upgrading From a Previous Version

If you have been running an earlier version of dupReport, the program will automatically update the dupReport.rc file and the dupReport.db database to the latest versions. Depending on the extent of the changes, the program may indicate that you need to edit the dupReport.rc file to set any new options correctly. 

As a precaution, **it is highly recommended that you backup your .rc and .db files to a safe place** before proceeding with the upgrade until you're sure everything is working properly.



Return to [Main Page](readme.md)