#!/bin/bash

# dupReport.sh - Create periodic reports on Duplicati activity and send to email

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

EMAILRESULTFILE=${PROGDIR}/emailresult.dat

# Find all backup sources
SOURCES=$(${SQLITE3} ${DBPATH} "select distinct source from backupsets")
#echo "Sources=["${SOURCES}"]"

# Remove any result file left over from a previous run
if [ -f ${EMAILRESULTFILE} ]; then
	rm -f ${EMAILRESULTFILE}
fi

# Print HTML headers and initial table structure to email
echo "<html><Title>Duplicati Activity Report</title><body>" > ${EMAILRESULTFILE}
echo "<table border=1><tr><td><b>Date</b></td><td><b>Examined</b></td><td><b>Size</b></td><td><b>Added</b></td><td><b>Deleted</b></td><td><b>Modified</b></td>">> ${EMAILRESULTFILE}
echo "<td><b>Errors</b></td><td><b>Result</b></td></tr>" >> ${EMAILRESULTFILE}

for i in ${SOURCES}
do
	echo "Source:$i"

	# Find all destinations where that souce is backed up to
	DESTINATIONS=$(${SQLITE3} ${DBPATH} "select distinct destComp from emails where sourceComp= '${i}'")
	#echo "Destinations=[${DESTINATIONS}]"

	for j in ${DESTINATIONS}
	do

		# Start new table row for <source>-<destination> pair
		echo "<tr><td colspan=8><center><b>${i} to ${j}</b></center></td></tr>" >> ${EMAILRESULTFILE}

                # Find out when the last update was run"
                LASTDT=$(${SQLITE3} ${DBPATH} "select lastDate,lastTime from backupsets where source='${i}' and destination = '${j}'")
                LASTDATE=$(echo ${LASTDT} | cut -f1 -d\|)
                LASTTIME=$(echo ${LASTDT} | cut -f2 -d\|)
                echo "Source=[$i]  Destination=[$j]   LASTDATE=[${LASTDATE}]   LASTTIME=[${LASTTIME}]"

		# Next, get all the emails since the last update date
		QUERYSTRING="select endDate, endtime, examinedFiles, sizeOfExaminedFiles, addedFiles, deletedFiles, modifiedFiles, filesWithError, parsedResult, warnings, errors \
			from emails \
			where sourceComp='${i}' and destComp = '${j}' and ((endDate > '${LASTDATE}') or ((endDate == '${LASTDATE}') and (endtime > '${LASTTIME}'))) order by endDate, endTime"
		echo "Query=[${QUERYSTRING}]"

		# Loop through each of those emails
		${SQLITE3} ${DBPATH} "${QUERYSTRING}" | while read queryResult; do

			# Get latest stats from backupsets table
			LASTDT=$(${SQLITE3} ${DBPATH} "select lastDate,lastTime,lastFileCount,lastFileSize from backupsets where source='${i}' and destination = '${j}'")
			LASTDATE=$(echo ${LASTDT} | cut -f1 -d\|) 	# Last date for recorded email
			LASTTIME=$(echo ${LASTDT} | cut -f2 -d\|)	# Last time for recorded email
			LASTFC=$(echo ${LASTDT} | cut -f3 -d\|)		# Last file count recorded
			LASTFS=$(echo ${LASTDT} | cut -f4 -d\|)		# Last file size recorded
			echo "LASTDATE=[${LASTDATE}]   LASTTIME=[${LASTTIME}]  LASTFC=[${LASTFC}]  LASTFS=[${LASTFS}]"

			# Parse various table columns from query result, these are the info foelds from the downloaded emails
			echo "Query Result=[${queryResult}]"
			endDate=$(echo ${queryResult} | cut -f1 -d\|)
			endTime=$(echo ${queryResult} | cut -f2 -d\|)
			examinedFiles=$(echo ${queryResult} | cut -f3 -d\|)
				examinedFilesDisp=$(printf "%'d" ${examinedFiles})
			sizeOfExaminedFiles=$(echo ${queryResult} | cut -f4 -d\|)
				sizeOfExaminedFilesDisp=$(printf "%'d" ${sizeOfExaminedFiles})
			addedFiles=$(echo ${queryResult} | cut -f5 -d\|)
				addedFilesDisp=$(printf "%'d" ${addedFiles})
			deletedFiles=$(echo ${queryResult} | cut -f6 -d\|)
				deletedFilesDisp=$(printf "%'d" ${deletedFiles})
			modifiedFiles=$(echo ${queryResult} | cut -f7 -d\|)
				modifiedFilesDisp=$(printf "%'d" ${modifiedFiles})
			filesWithError=$(echo ${queryResult} | cut -f8 -d\|)
				filesWithErrorDisp=$(printf "%'d" ${filesWithError})
			parsedResult=$(echo ${queryResult} | cut -f9 -d\|)
			warnings=$(echo ${queryResult} | cut -f10 -d\|)
			errors=$(echo ${queryResult} | cut -f11 -d\|)
			echo "${examinedFilesDisp}|${sizeOfExaminedFilesDisp}|${addedFilesDisp}|${deletedFilesDisp}|${modifiedFilesDisp}|${filesWithErrorDisp}|${parsedResult}|${warnings}|${errors}"

			# Determine file count & size diffeence from last run
			examinedFilesDelta=$(expr ${examinedFiles} - ${LASTFC})
			fileSizeDelta=$(expr ${sizeOfExaminedFiles} - ${LASTFS})

			# Determine sign (+/-) of deltas
			if [ ${examinedFilesDelta} -ge 0 ]; then FDS='+'; else FDS='-'; fi
			if [ ${fileSizeDelta} -ge 0 ]; then SDS='+'; else SDS='-'; fi

			efdDisp=$(printf "%'d" ${examinedFilesDelta})
			fsdDisp=$(printf "%'d" ${fileSizeDelta})

			# Print report for this email to email file
			echo "<tr>" >> ${EMAILRESULTFILE}
			echo "<td>${endDate} ${endTime}</td><td>${examinedFilesDisp}(${FDS}${efdDisp})</td><td>${sizeOfExaminedFilesDisp}(${SDS}${fsdDisp})</td>" >> ${EMAILRESULTFILE}
			echo "<td>${addedFilesDisp}</td><td>${deletedFilesDisp}</td><td>${modifiedFilesDisp}</td><td>${filesWithErrorDisp}</td><td>${parsedResult}</td></tr>" >> ${EMAILRESULTFILE}
			if [ "${warnings}" != "" ]; then
				echo "<tr><td colspan=8>Warnings: ${warnings}</td></tr>"  >> ${EMAILRESULTFILE}
			fi
                        if [ "${errors}" != "" ]; then
                                echo "<tr><td colspan=8>Errors: ${errors}</td></tr>" >> ${EMAILRESULTFILE}
                        fi

			# Update database with most recent count & sizes
			UPDATESTRING="update backupsets set lastFileCount = ${examinedFiles}, lastFileSize = ${sizeOfExaminedFiles}, \
				lastDate = '${endDate}', lastTime = '${endTime}' where source = '${i}' and destination = '${j}'"
			echo "UPDATESTRING:[${UPDATESTRING}]"
			${SQLITE3} ${DBPATH} "${UPDATESTRING}"
		done
	done
done

echo "</table></body></html>"  >> ${EMAILRESULTFILE}

cat ${EMAILRESULTFILE} | mail -s "$(echo -e "Backup Report\nContent-Type: text/html")"  -r ${BACKUPEMAIL} ${REPORTEMAIL}

