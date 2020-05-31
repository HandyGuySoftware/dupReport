# How can I get started quickly?

There's a **lot** of information in this guide about how to install, configure, and run dupReport. But you probably don't want to read all that, you want to just start running the program! Here's the quick & dirty guide to get you started.

1. Make sure Python 3.x is available and running on your system. For information on downloading and installing Python see the [Python Software Foundation web site](https://www.python.org/). 
2. Make sure your Duplicati backup jobs are named properly. The best naming scheme (at least to get      you started) is:

```
<source>-<destination>
```

where \<source> is the name of the computer where the files are located and \<destination> is the place where they are going to. For example, if your computer is named "MediaServer" and you are backing up to a directory on the "NAS" computer, the backup name would be:

```
MediaServer-NAS
```

For more interesting information on naming backup jobs see the section on ["Source-Destination Pairs."](Config-SrcDestPairs.md) 

3. Configure a Duplicati job to send its output report to an email account. See the [Duplicati documentation for the "send-mail" advanced email options](https://duplicati.readthedocs.io/en/latest/06-advanced-options/#send-mail-to) to learn how to do this.
4. Run at least one backup with the newly-named backup job so that you have an email that dupReport can find on your email server. 
5. Download the dupReport code from the [GitHub page](https://github.com/HandyGuySoftware/dupReport) by clicking the "Clone or download" button on the dupReport GitHub page, then click "Download ZIP." This will put the ZIP file on your system. Unzip the file to the directory of your choice.
6. Run dupReport.py to install the default configuration files. The first time you run the program it will launch the Guided Setup that will lead you through configuring the most common options. The instructions for the Guided Setup can be found in the ["Installation" section.](Installation.md) Read that section, do what it says, then come back here.
7. Once the Guided Setup completes it will continue to run the program and collect backup emails. If there are any errors or things that need to be adjusted in the configuration you will receive a message on what those are. 
8. For subsequent runs, run the dupReport.py program using the appropriate command line as shown in the ["Basic Command LIne" section](CommandLine.md).
9. Let the program run to completion. When it is complete you should get an email with the output report.

That's the quick way to do it! Now that you've seen how it works, please read the rest of this guide for LOTS more information on how to configure dupReport to get the most out of the program.





(Return to [Main Page](readme.md))

