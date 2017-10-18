#!/bin/bash

# DupDownloadEmails - Download new emails from the backups email account for processing

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

# Now, to the fun stuff...

# Local variables to define
SQLSTATEMENT="${PROGDIR}/sqlstatements.sql"	# File to store SQL update statements
AWKFILE="${PROGDIR}/dupParse.awk"

# Run getmail, download new email messages
${GETMAIL} -g${GETMAILDATA} -r getmailrc

# Clear out any residual SQL statements left from previous runs
rm -f ${SQLSTATEMENT}

# Loop through all new messages in message directory. Whatever is there is new.
for i in $( ls ${MSGSDIR} ); do
	echo $i
	# Parse each message using awk to create sqlite INSERT statements for each message. Send result to a temporary file
	cat ${MSGSDIR}/$i | ${AWKPATH} -f ${AWKFILE} > ${PROGDIR}/tmpfile
	# Get result of awk command.
	cmdResult=$?
	if [ ${cmdResult} -eq 0 ]; then
		# awk result = 0. It's a backup email message.
		# Add sqlite INSERT statement to SQL file for later processing
		cat ${PROGDIR}/tmpfile >> ${SQLSTATEMENT}
	else
		# Result != 0. Not a backup email message
		# Forward notification to a monitored email address for review
		# Date, time, subject are forwarded. Original email is left in backup email account
		# Change subject text to suit your own taste
		#cat ${PROGDIR}/tmpfile | mail -s "Non-Backup Email Message" ${FORWARDEMAIL}
		echo ""
	fi
done

# Check if any SQL was generated. File will not exist if 1) no new email messages were retrieved, or 2) all retrieved messages were non-backup messages
if [ -f ${SQLSTATEMENT} ]; then
	# Execute sqlite with email UPDATE statements
	${SQLITE3} ${DBPATH} < ${SQLSTATEMENT}
fi

# Remove all processed messages, leave a clean directory for the next run.
rm -f ${MSGSDIR}/*

# Exit gracefully
exit 0
