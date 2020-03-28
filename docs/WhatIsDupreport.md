

# What is dupReport?

dupReport is a program that will collect up status emails from Duplicati and combine them into a single email report that is sent to you. The following diagram helps explain how it works:

![dupReport Architecture](dR_Architecture.jpg)\

Some general points about dupReport

- The program is designed for those who run backups from multiple locations and are getting multiple     Duplicati emails per day. For example, we have 14 separate emails coming in per day from Duplicati backup jobs; way too many to keep track of manually. In these cases, dupReport will collect and collate all those emails and create a single report that summarizes all of them. If you only have a single instance of Duplicati running a single backup job, you may get some value from dupReport, but it may be overkill.
- dupReport doesn’t interface directly with Duplicati and doesn't read the Duplicati configuration files, log files, or or database. It connects to your email server, reads the backup report emails that Duplicati sends out, then parses them to create its report. It does not need to be run on the same system where Duplicati is running, it can be on a completely different system if that is more convenient for you. The only requirement is that the system where dupReport is running must be able to connect to your email server.

# Origin Story

The old CrashPlan Home backup system had a really nice feature whereby it would gather up the current backup status for all your systems and mail you a consolidated report on a periodic basis. It was a great way to make sure all your backups were current and to notify you if something was wrong. Duplicati has no such capability. You can configure it to send you email when backup jobs completed, but you get a separate email for each backup job that runs. In the configuration we have (9 systems backing up to 2 different storage services in various combinations) we get 14 different emails per day. Compare that with CrashPlan's single summary email per day and you can see how this was a problem. Others on the [Duplicati discussion forum](https://forum.duplicati.com/) noticed it, too. That started us thinking about developing a tool to provide summarized email notification for Duplicati users.  

dupReport was born.  



Return to [Main Page](readme.md)