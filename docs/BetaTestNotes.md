# dupReport 3.0.0 - Notes for Beta Testers

------

Thank you for beta testing dupReport 3.0.0. There are a lot of changes planned for in this version, both in the options available to end users and in the code itself. Here's a high level look at what's changed (so far):

- The reporting engine has been completely re-built to allow for more control over reporting formats
	- Users can now create their own customized reports
	- You can now run multiple report formats in the same program run. These are specified in the *[report]layout=* option in the .rc file
	- Created separate "no activity" report instead of including that in the standard report output. This can now be added or left off the report run at will
	- Created separate "lastseen" report to display the last seen backup date & time for each backupset. Replaces the [report]lastseen= option in the .rc file
- The specification for the database, .rc file, and log files can now be either directory names or full path specifications
- You can now send output to a JSON file
- The documentation has been re-structured for better readability and made it easier to find specific settings.

Because there are so many changes planned for this version, the beta testing will be done in stages. The rest of this page will be a running list of the development process and the things that need testing. Testing began in early April, but if you're coming to this later than that please feel free to jump right in wherever you can.

**BEFORE YOU BEGIN:**

Because this is a beta program, the software may not always perform the way we'd like ("unstable" is right there in the branch name ;-)). Therefore, I highly suggest that you **do not use this as your production code**, at least not yet. Install this on a separate area of your computer and run it separately, at least until we're all more confident about the stability of the existing code. That being said, **I do** run this as my production system, just to make sure it is constantly being tested under real-world circumstances.

**Reporting Issues**

All issues, comments, and discussions about dupReport 3.0 beta should be done in the [dupReport 3.0.0 Beta Testing Thread (Issue #143)](https://github.com/HandyGuySoftware/dupReport/issues/143) on GitHub. Please do not post comments about the beta on the Duplicati Forum.

**Thank You!**

Thanks for helping to make this new version of dupReport as good as it can be. I appreciate any effort you can put in to help make this version as bug free as possible when it is released to the general public.

------

**4 April 2020 - Beta 1**

The first three things to test are the new documentation, the file conversion routines, and the new reporting engine. 

**Documentation**

The dupReport documentation has been re-arranged to make finding information about the program much easier. Please review the docs and let me know if you have any corrections or if something is not explained clearly or properly. In particular for this beta, read through the documentation on reporting to understand how the new reporting engine works.

**File Conversion**

The program will automatically update your .db and .rc file to new formats. The program will also automatically make a date-stamped backup of each of these files, but I suggest you make your own backup copies just in case.

I anticipate that there will be some more .db and .rc file changes coming down the road, and each time we will assume that you are starting from 2.x version files. Basically, be prepared to restore your .db and .rc files back to pre-3.0 versions a few times during the testing.

**Reporting Engine**

The reporting engine has been completely rewritten. A few highlights:

- Reports are now much more customizable.
- You can run multiple reports during the same run
- The reports to run can be specified in the .rc file or the command line
- You can select what order you'd like the reports to appear

You can read all about the reporting engine on the [[report] Section](Reporting-ReportSection.md) and [Custom Reporting](Reporting-CustomReportSpec.md) pages.

