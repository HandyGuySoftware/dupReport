#!/bin/bash

#dupCreateDb - Create and initialize database for dupReport.sh

# Get working directory for program
SOURCE="${BASH_SOURCE[0]}"
while [ -h "$SOURCE" ]; do # resolve $SOURCE until the file is no longer a symlink
        TARGET="$(readlink "$SOURCE")"
        if [[ $TARGET == /* ]]; then
                #echo "SOURCE '$SOURCE' is an absolute symlink to '$TARGET'"
                SOURCE="$TARGET"
        else
                DIR="$( dirname "$SOURCE" )"
                #echo "SOURCE '$SOURCE' is a relative symlink to '$TARGET' (relative to '$DIR')"
                SOURCE="$DIR/$TARGET" # if $SOURCE was a relative symlink, we need to resolve it relative to the path where the symlink file was located
        fi
done
RDIR="$( dirname "$SOURCE" )"
DIR="$( cd -P "$( dirname "$SOURCE" )" && pwd )"

# Read program variables from RC file (dupReport.rc)
if [ -f ${DIR}/dupReport.rc ]; then
        source ${DIR}/dupReport.rc
else
        echo "Error: dupreport.rc file not found in ${DIR}"
        exit 1
fi

# Remove any existing db file
if [ -f ${DBPATH} ]; then
	rm -f ${DBPATH}
fi

# Create database and initialize tables
${SQLITE3} ${DBPATH} <<!
create table emails (sourceComp varchar(50), destComp varchar(50), emailDate varchar(50), emailTime varchar(50), deletedFiles int,
        deletedFolders int, modifiedFiles int, examinedFiles int, openedFiles int, addedFiles int, sizeOfModifiedFiles int,
        sizeOfAddedFiles int, sizeOfExaminedFiles int,
        sizeOfOpenedFiles int, notProcessedFiles int, addedFolders int, tooLargeFiles int,
        filesWithError int, modifiedFolders int, modifiedSymlinks int, addedSymlinks int, deletedSymlinks int,
        partialBackup varchar(30), dryRun varchar(30), mainOperation varchar(30), parsedResult varchar(30), verboseOutput varchar(30), verboseErrors varchar(30), endDate varchar(30),
        endTime varchar(30), beginDate varchar(30), beginTime varchar(30), duration varchar(30), messages varchar(255), warnings varchar(255), errors varchar(255));

create table backupsets (source varchar(20), destination varchar(20), email varchar(50), lastFileCount integer, lastFileSize integer,
        lastDate varchar(50), lastTime varchar(50));
!

# Read Source-Destination-Email tuples from RC files. Add line in backupsets for each tuple
COUNT=1
VNAME="TUPLE${COUNT}"
echo "VNAME=[${VNAME}]"
eval VNAME2=\$$VNAME
echo "VANME2=[${VNAME2}]"

while [ "${VNAME2}" != "" ]; do
	# Split info into fields
	SCOMP=$(echo ${VNAME2} | cut -f1 -d-)
	DCOMP=$(echo ${VNAME2} | cut -f2 -d-)
	EMA=$(echo ${VNAME2} | cut -f3 -d-)
	echo "SCOMP=[${SCOMP}]  DCOMP=[${DCOMP}]  EMA=[${EMA}]"

	# Add entry in backupsets table
	${SQLITE3} ${DBPATH} <<!
	insert into backupsets (source, destination, email, lastFileCount, lastFileSize, lastDate, lastTime) values ("${SCOMP}", "${DCOMP}","${EMA}", 0, 0, "2000-01-01","00:00:00");
!
	((COUNT++))
        echo "${VNAME2}=[${VNAME2}]"
        VNAME="TUPLE${COUNT}"
        eval VNAME2=\$$VNAME
done

rm -f ${GETMAILDATA}/oldmail*
