#####
#
# Module name:  drdatetime.py
# Purpose:      Miscellaneous date and time management functions for dupReport
# 
# Notes:
#
#####

# Import system modules
import re
import datetime

# Import dupReport modules
import globs

# dtFmtDefs - definitions for date field formats
# Tuples are defined as follows:
# Field     Purpose
# 0         separator character
# 1, 2, 3   Positions in format string for (year, month, day) or (hour, minute, seconds)
#
# Note: There's only one recognized time string format. But with all the 
#       problems I had with date string recoznition, this makes time strings
#       more flexible should the need arise in the future.
dtFmtDefs={
    # Format Str    [0]Delimiter    [1]Y/H Col  [2]M/Mn Col [3]D/S Col
    'YYYY/MM/DD':   ('/',           0,          1,          2),
    'YYYY/DD/MM':   ('/',           0,          2,          1),
    'MM/DD/YYYY':   ('/',           2,          0,          1),
    'DD/MM/YYYY':   ('/',           2,          1,          0),
    'YYYY-MM-DD':   ('-',           0,          1,          2),
    'YYYY-DD-MM':   ('-',           0,          2,          1),
    'MM-DD-YYYY':   ('-',           2,          0,          1),
    'DD-MM-YYYY':   ('-',           2,          1,          0),
    'YYYY.MM.DD':   ('.',           0,          1,          2),
    'YYYY.DD.MM':   ('.',           0,          2,          1),
    'MM.DD.YYYY':   ('.',           2,          0,          1),
    'DD.MM.YYYY':   ('.',           2,          1,          0),
    'HH:MM:SS'  :   (':',           0,          1,          2)
    }

# Issue #83. Changed regex for the date formats to allow any standard delimiter ('/', '-', or '.')
# The program (via toTimestamp()) will use this regex to extract the date from the parsed emails
# If the structure is correct (e.g., 'MM/DD/YYYY') but the delimiters are wrong (e.g., '04-30-2018') the program will still be able to parse it.
# As a result, all the rexex's for dtFmtDefs date fields are all the same now. (Change from previous versions)
dateParseRegex = '(\s)*(\d)+[/\-\.](\s)*(\d)+[/\-\.](\s)*(\d)+'     # i.e., <numbers>[/-.]<numbers>[/-.]<numbers>
timeParseRegex = '(\d)+[:](\d+)[:](\d+)'                            # i.e., <numbers>:<numbers>:<numbers>
validDateDelims = '[/\-\.]'                                         # Valid delimiters in a date string
validTimeDelims = ':'                                               # Valid delimiters in a time string

# Print error messages to the log and stderr if there is a date or time format problem.
# It happens more often than you'd think!
def timeStampCrash(msg):
    globs.log.write(1, msg)
    globs.log.write(1,'This is likely caused by an email using a different date or time format than expected,\nparticularly if you\'re collecting emails from multiple locations or time zones.')
    globs.log.write(1,'Please check the \'dateformat=\' and \'timeformat=\' value(s) in the [main] section\nand any [<source>-<destination>] sections of your .rc file for accuracy.')
    globs.log.err('Date/time format specification mismatch. See log file for details. Exiting program.')
    globs.closeEverythingAndExit(1)

# Convert a date/time string to a timestamp
# Input string = YYYY/MM/DD HH:MM:SS AM/PM (epochDate)."
# May also be variants of the above. Must check for all cases
# dtStr = date/time string
# dfmt is date format - defaults to user-defined date format in .rc file
# tfmt is time format - - defaults to user-defined time format in .rc file
# utcOffset is UTC offset info as extracted from the incoming email message header
def toTimestamp(dtStr, dfmt = None, tfmt = None, utcOffset = None):
    globs.log.write(1,'drDateTime.toTimestamp({}, {}, {}, {})'.format(dtStr, dfmt, tfmt, utcOffset))

    # Set default formats
    if (dfmt is None):
        dfmt = globs.opts['dateformat']
    if (tfmt is None):
        tfmt = globs.opts['timeformat']

    # Find proper date spec
    # Get column positions
    yrCol = dtFmtDefs[dfmt][1] # Which field holds the year?
    moCol = dtFmtDefs[dfmt][2] # Which field holds the month?
    dyCol = dtFmtDefs[dfmt][3] # Which field holds the day?
    
    # Extract the date
    dtPat = re.compile(dateParseRegex)      # Compile regex for date/time pattern
    dateMatch = re.match(dtPat,dtStr)       # Match regex against date/time
    if dateMatch:
        dateStr = dtStr[dateMatch.regs[0][0]:dateMatch.regs[0][1]]   # Extract the date string
    else:
        timeStampCrash('Can\'t find a match for date pattern {} in date/time string {}.'.format(dfmt, dtStr))   # Write error message, close program
    
    datePart = re.split(validDateDelims, dateStr)     # Split date string based on any valid delimeter
    year = int(datePart[yrCol])
    month = int(datePart[moCol])
    day = int(datePart[dyCol])
    
    # Get column positions
    hrCol = dtFmtDefs[tfmt][1] # Which field holds the Hour?
    mnCol = dtFmtDefs[tfmt][2] # Which field holds the minute?
    seCol = dtFmtDefs[tfmt][3] # Which field holds the seconds?
 
    # Extract the time
    tmPat = re.compile(timeParseRegex)
    timeMatch = re.search(tmPat,dtStr)
    if timeMatch:
        timeStr = dtStr[timeMatch.regs[0][0]:timeMatch.regs[0][1]]
    else:
        timeStampCrash('Can\'t find a match for time pattern {} in date/time string {}.'.format(tfmt, dtStr))   # Write error message, close program
    timePart = re.split(validTimeDelims, timeStr)
    hour = int(timePart[hrCol])
    minute = int(timePart[mnCol])
    second = int(timePart[seCol])
    
    # See if we need AM/PM adjustment
    pmPat = re.compile('AM|PM')
    pmMatch = re.search(pmPat,dtStr)
    if pmMatch:
        dayPart = dtStr[pmMatch.regs[0][0]:pmMatch.regs[0][1]]
        if ((hour == 12) and (dayPart == 'AM')):
            hour = 0
        elif ((hour != 12) and (dayPart == 'PM')):
            hour += 12

    # Convert to datetime object, then get timestamp
    try:
        ts = datetime.datetime(year, month, day, hour, minute, second).timestamp()
    except ValueError:
        timeStampCrash('Error creating timestamp: DateString={} DateFormat={} year={} month={} day={} hour={} minute={} second={}'.format(dtStr, dfmt, year, month, day, hour, minute, second))   # Write error message, close program
 
    # Apply email's UTC offset to date/time
    # Need to separate the two 'if' statements because the init routines crash otherwise
    # (Referencing globs.opts[] before they're set)
    if utcOffset is not None:
        if globs.opts['applyutcoffset']:
            ts += float(utcOffset)

    globs.log.write(1,'Date/Time converted to [{}]'.format(ts))
    return ts

# Convert an RFC 3339 format datetime string to an epoch-style timestamp
# Needed because the JSON output format uses this style for datetime notation
# Basically, decode the RFC3339 string elements into separate date & time strings, then send to toTimeStamp() as a normal date/time string.
def toTimestampRfc3339(tsString, utcOffset = None):
    globs.log.write(1,'drDateTime.toTimestampRfc3339({})'.format(tsString))

    # Strip trailing 'Z' and last digit from milliseconds, the float number is too big to convert
    tsStringNew = tsString[:-2] 

    # Convert to datetime object
    dt = datetime.datetime.strptime(tsStringNew, '%Y-%m-%dT%H:%M:%S.%f')

    # Now, use existing methods to convert to a timestamp
    ts = toTimestamp("{}/{}/{} {}:{}:{}".format(dt.month, dt.day, dt.year, dt.hour, dt.minute, dt.second), "MM/DD/YYYY", "HH:MM:SS", utcOffset)

    return ts

# Convert from timestamp to resulting time and date formats
def fromTimestamp(ts, dfmt = None, tfmt = None):
    
    # 'x' holds the array for yr/mo/day or hh/m/ss
    # Placement in the array is determined by the position values (columns 2, 3, & 4) in the dtFmtDefs[] list
    x = [0, 0, 0]

    # If date & time formats are not specified, use the global defaults as defined in the .rc file
    if (dfmt is None):
        dfmt = globs.opts['dateformat']
    if (tfmt is None):
        tfmt = globs.opts['timeformat']
    globs.log.write(1, 'drdatetime.fromTimestamp({}, {}, {})'.format(ts, dfmt, tfmt))
    if ts is None:
        timeStampCrash('Timestamp conversion error.')   # Write error message, close program

    # Get datetime object from incoming timestamp
    dt = datetime.datetime.fromtimestamp(float(ts))

    # Get date column positions
    delim = dtFmtDefs[dfmt][0] # Get the Date delimeter
    yrCol = dtFmtDefs[dfmt][1] # Which field holds the year?
    moCol = dtFmtDefs[dfmt][2] # Which field holds the month?
    dyCol = dtFmtDefs[dfmt][3] # Which field holds the day?

    # Place strftime() format specs in appropriate year/month/day columns
    x[yrCol] = '%Y'
    x[moCol] = '%m'
    x[dyCol] = '%d'
    retDate = dt.strftime('{}{}{}{}{}'.format(x[0],delim,x[1],delim,x[2]))

    # Get time column positions
    delim = dtFmtDefs[tfmt][0] # Get the time delimeter
    hrCol = dtFmtDefs[tfmt][1] # Which field holds the Hour?
    mnCol = dtFmtDefs[tfmt][2] # Which field holds the minute?
    seCol = dtFmtDefs[tfmt][3] # Which field holds the seconds?

    if not globs.opts['show24hourtime']:
        x[hrCol] = '%I'
        if dt.hour < 12:
            ampm = ' AM'
        else:
            ampm = ' PM'
    else:
        x[hrCol] = '%H'
        ampm = ''

    x[mnCol] = '%M'
    x[seCol] = '%S'
    retTime = dt.strftime('{}{}{}{}{}{}'.format(x[0],delim,x[1],delim,x[2], ampm))
    globs.log.write(3, 'Converted [{}] to [{} {}]'.format(ts, retDate, retTime))

    
    return retDate, retTime

# Calculate # of days since some arbitrary date
def daysSince(tsIn):
    # Get the current time (timestamp)
    nowTimestamp = datetime.datetime.now().timestamp()
    now = datetime.datetime.fromtimestamp(nowTimestamp)
    then = datetime.datetime.fromtimestamp(tsIn)
    diff = (now-then).days
    globs.log.write(3, 'daysSince() now=[{}]-[{}] then=[{}]-[{}] diff=[{}]'.format(nowTimestamp,fromTimestamp(nowTimestamp), tsIn, fromTimestamp(tsIn), diff))

    return diff

# Calculate time difference between two dates
def timeDiff(td):

    # Cast td as a timedelta object
    tDelt = datetime.timedelta(seconds = td)

    # Calculate unit values
    days = tDelt.days
    hours, remainder = divmod(tDelt.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    #seconds += tDelt.microseconds / 1e6

    # Set return string value based on opts['durationzeroes'] setting
    if globs.report.reportOpts['durationzeroes'] is True:
        return "{}d {}h {}m {}s".format(days, hours, minutes, seconds)
    else: # Leave out parts that == 0
        retVal = ""
        if days != 0:
            retVal += "{}d ".format(days)
        if hours != 0:
            retVal += "{}h ".format(hours)
        if minutes != 0:
            retVal += "{}m ".format(minutes)
        if seconds != 0:
            retVal += "{}s ".format(seconds)
        return retVal

