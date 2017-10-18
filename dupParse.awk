BEGIN {
	FS=": "		# File Separator for fields
	a["Jan"]=1	# Convert Months to numbers
	a["Feb"]=2
        a["Mar"]=3
        a["Apr"]=4
        a["May"]=5
        a["Jun"]=6
        a["Jul"]=7
        a["Feb"]=8
        a["Sep"]=9
        a["Oct"]=10
        a["Nov"]=11
        a["Dec"]=12

	#sourceComp=destcomp=emailDate=emailTime="";
	#deletedFiles=deletedFolders=modifiedFiles=examinedFiles=openedFiles=addedFiles=sizeOfModifiedFiles=sizeOfAddedFiles=0;
	#sizeOfExaminedFiles=sizeOfOpenedFiles=notProcessedFiles=addedFolders=tooLargeFiles=filesWithError=modifiedFolders=modifiedSymlinks=0;
	#addedSymlinks=deletedSymlinks=0
	#partialBackup=mainOperation=parsedResult=verboseOutput=verboseErrors=endDate=endTime=beginDate=beginTime=duration=messages=warnings=errors=""; 
	parsedResult="";
}

/^Subject:/ {
	if (match($2,"Duplicati Backup report for") == 0)
		{
		print "Subject: Not a result email" > "/dev/stderr";
		print "Non-Backup Email Message to somewhere else";
		print "Subject: "$2;
		print "Date: "emailDate"  Time: "emailTime;
		validEmail=0;
		exit 1;
		}
	else
		{
		print "Subject: result email" > "/dev/stderr"
		split($2, subjArr, " ");
		split(subjArr[5], subjArr2, "[-:]");
		sourceComp=subjArr2[1];
		destComp=subjArr2[2];
		print "Source=" subjArr2[1] > "/dev/stderr";
                print "Destination=" subjArr2[2] > "/dev/stderr";
		validEmail=1;
		}
	}

/^Date:/ {
        split($2, dtArr , " ");
        exeDay=dtArr[2]; exeMonth=a[dtArr[3]]; exeYear=dtArr[4];
        emailDate = exeYear"-"exeMonth"-"exeDay;
	emailTime = dtArr[5];
	print emailDate " " emailTime > "/dev/stderr";
        }

/^DeletedFiles:/ {
	deletedFiles=$2;
	print "Deleted Files:" deletedFiles > "/dev/stderr";
	}

/^DeletedFolders:/ {
        deletedFolders=$2;
        print "Deleted Folders:" deletedFolders > "/dev/stderr";
        }

/^ModifiedFiles:/ {
        modifiedFiles=$2;
        print "Modified Files:" modifiedFiles > "/dev/stderr";
        }

/^ExaminedFiles:/ {
        examinedFiles=$2;
        print "Examined Files:" examinedFiles > "/dev/stderr";
        }

/^OpenedFiles:/ {
        openedFiles=$2;
        print "Opened Files:" openedFiles > "/dev/stderr";
        }

/^AddedFiles:/ {
        addedFiles=$2;
        print "Added Files:" addedFiles > "/dev/stderr";
        }

/^SizeOfModifiedFiles:/ {
        sizeOfModifiedFiles=$2;
        print "Size of Modified Files:" sizeOfModifiedFiles > "/dev/stderr";
        }

/^SizeOfAddedFiles:/ {
        sizeOfAddedFiles=$2;
        print "Size of Added Files:" sizeOfAddedFiles > "/dev/stderr";
        }

/^SizeOfExaminedFiles:/ {
        sizeOfExaminedFiles=$2;
        print "Size of ExaminedFiles:" sizeOfExaminedFiles > "/dev/stderr";
        }

/^SizeOfOpenedFiles:/ {
        sizeOfOpenedFiles=$2;
        print "Size of Opened Files:" sizeOfOpenedFiles > "/dev/stderr";
        }

/^NotProcessedFiles:/ {
        notProcessedFiles=$2;
        print "Not Processed Files:" notProcessedFiles > "/dev/stderr";
        }

/^AddedFolders:/ {
        addedFolders=$2;
        print "Added Folders:" addedFolders > "/dev/stderr";
        }

/^TooLargeFiles:/ {
        tooLargeFiles=$2;
        print "Too Large Files:" tooLargeFiles > "/dev/stderr";
        }

/^FilesWithError:/ {
        filesWithError=$2;
        print "Files With Error:" filesWithError > "/dev/stderr";
        }

/^ModifiedFolders:/ {
        modifiedFolders=$2;
        print "Modified Folders:" modifiedFolders > "/dev/stderr";
        }

/^ModifiedSymlinks:/ {
        modifiedSymlinks=$2;
        print "Modified Symlinks:" modifiedSymlinks > "/dev/stderr";
        }

/^AddedSymlinks:/ {
        addedSymlinks=$2;
        print "Added Symlinks:" addedSymlinks > "/dev/stderr";
        }

/^DeletedSymlinks:/ {
        deletedSymlinks=$2;
        print "Deleted Symlinks:" deletedSymlinks > "/dev/stderr";
        }

/^PartialBackup:/ {
        partialBackup=$2;
        print "Partial Backup:" partialBackup > "/dev/stderr";
        }

/^Dryrun:/ {
        dryRun=$2;
        print "Dry Run:" dryRun > "/dev/stderr";
        }

/^MainOperation:/ {
        mainOperation=$2;
        print "Main Operation:" mainOperation > "/dev/stderr";
        }

/^ParsedResult:/ {
        parsedResult=$2;
        print "Parsed Result:" parsedResult > "/dev/stderr";
        }

/^VerboseOutput:/ {
        verboseOutput=$2;
        print "VerboseOutput:" verboseOutput > "/dev/stderr";
        }

/^VerboseErrors:/ {
        verboseErrors=$2;
        print "Verbose Errors:" verboseErrors > "/dev/stderr";
        }

/^EndTime:/ {
        split($2, dtArr , " ");
	split(dtArr[1], dtDate, "/");
	endDate = sprintf("%04d-%02d-%02d",dtDate[3], dtDate[1], dtDate[2]);

        split(dtArr[2], dtDate, ":");
	if (dtArr[3] == "PM")
		dtDate[1] = dtDate[1] + 12;
	endTime = sprintf("%02d:%02d:%02d",dtDate[1], dtDate[2], dtDate[3]);

        print "End Date:",endDate,"  End Time:",endTime > "/dev/stderr";
        }

/^BeginTime:/ {
        split($2, dtArr , " ");
        split(dtArr[1], dtDate, "/");
        beginDate = sprintf("%04d-%02d-%02d",dtDate[3], dtDate[1], dtDate[2]);

        split(dtArr[2], dtDate, ":");
        if (dtArr[3] == "PM")
                dtDate[1] = dtDate[1] + 12;
        beginTime = sprintf("%02d:%02d:%02d",dtDate[1], dtDate[2], dtDate[3]);
	}

/^Duration:/ {
        duration=$2;
        print "Duration: ", duration > "/dev/stderr";
        }

/^Messages:/ {
	if ($2 ~ "\\[\\]")
		messages=""
	else
		{
		eom=0;
		messages="";
		while (eom == 0)
			{
			getline tmp;
			if (tmp ~ /^\]/)
				{
				print ("End of message") > "/dev/stderr";
				eom = 1;
				}
			else
				{
				messages = messages tmp;
				}
			}
		}
	print "Messages: " messages > "/dev/stderr";
	}

/^Warnings:/ {
        if ($2 ~ "\\[\\]")
                warnings=""
        else
                {
                eom=0;
                warnings="";
                while (eom == 0)
                        {
                        getline tmp;
                        if (tmp ~ /^\]/)
                                {
                                print ("End of warmings") > "/dev/stderr";
                                eom = 1;
                                }
                        else
                                {
                                warnings = warnings tmp;
                                }
                        }
                }
        print "Warnings: " warnings > "/dev/stderr";
        }

/^Errors:/ {
        if ($2 ~ "\\[\\]")
                errors=""
        else
                {
                eom=0;
                errors="";
                while (eom == 0)
                        {
                        getline tmp;
                        if (tmp ~ /^\]/)
                                {
                                print ("End of errors") > "/dev/stderr";
                                eom = 1;
                                }
                        else
                                {
                                errors = errors tmp;
                                }
                        }
                }
        print "Errors: " errors > "/dev/stderr";
        }


END {

if ((validEmail == 1) && (parsedResult != ""))
	{
	sqlstatement = "insert into emails (sourceComp, destcomp, emailDate, emailTime, deletedFiles, deletedFolders, modifiedFiles, \
	examinedFiles, openedFiles, addedFiles, sizeOfModifiedFiles, sizeOfAddedFiles, \
	sizeOfExaminedFiles, sizeOfOpenedFiles, notProcessedFiles, addedFolders, tooLargeFiles,\
	filesWithError, modifiedFolders, modifiedSymlinks, addedSymlinks, deletedSymlinks,\
	partialBackup, dryRun, mainOperation, parsedResult, verboseOutput, verboseErrors, endDate,\
	endTime, beginDate, beginTime, duration, messages, warnings, errors) \
	values (";

	sqlstatement = sqlstatement "'"sourceComp"','"destComp"','" emailDate "','" emailTime "'," deletedFiles ","  deletedFolders ","  modifiedFiles ","  \
	examinedFiles ","  openedFiles ","  addedFiles ","  sizeOfModifiedFiles ","  sizeOfAddedFiles "," \
	sizeOfExaminedFiles "," sizeOfOpenedFiles ","  notProcessedFiles ","  addedFolders ","  tooLargeFiles "," \
	filesWithError ","  modifiedFolders ","  modifiedSymlinks ","  addedSymlinks ","  deletedSymlinks ",'" \
	partialBackup "','"  dryRun "','"  mainOperation "','"  parsedResult "','"  verboseOutput "','"  verboseErrors "','"  endDate "','" \
	endTime "','"  beginDate "','"  beginTime "','"  duration "',\""  messages "\",\""  warnings "\",\""  errors "\");";

	print sqlstatement > "/dev/stdout";
	}
}

