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
import time

# Import dupReport modules
import globs

# dtFmtDefs - definitions for date field formats
# Tuples are defined as follows:
# Field     Purpose
# 0         separator character
# 1, 2, 3   Positions in format string for (year, month, day) or (hour, minute, seconds)
# 4         regex to parse date/time string
#
# Note: There's only one recognized time string format. But with all the 
#       problems I had with date string recoznition, this makes time strings
#       more flexible should the need arise in the future.
dtFmtDefs={
    # Format Str    [0]Delimiter    [1]Y/H Col  [2]M/Mn Col [3]D/S Col  [4]Regex
    'YYYY/MM/DD':   ('/',           0,          1,          2,          '(\s)*(\d)+[/](\s)*(\d)+[/](\s)*(\d)+'),
    'YYYY/DD/MM':   ('/',           0,          2,          1,          '(\s)*(\d)+[/](\s)*(\d)+[/](\s)*(\d)+'),
    'MM/DD/YYYY':   ('/',           2,          0,          1,          '(\s)*(\d)+[/](\s)*(\d)+[/](\s)*(\d)+'),
    'DD/MM/YYYY':   ('/',           2,          1,          0,          '(\s)*(\d)+[/](\s)*(\d)+[/](\s)*(\d)+'),
    'YYYY-MM-DD':   ('-',           0,          1,          2,          '(\s)*(\d)+[-](\s)*(\d)+[-](\s)*(\d)+'),
    'YYYY-DD-MM':   ('-',           0,          2,          1,          '(\s)*(\d)+[-](\s)*(\d)+[-](\s)*(\d)+'),
    'MM-DD-YYYY':   ('-',           2,          0,          1,          '(\s)*(\d)+[-](\s)*(\d)+[-](\s)*(\d)+'),
    'DD-MM-YYYY':   ('-',           2,          1,          0,          '(\s)*(\d)+[-](\s)*(\d)+[-](\s)*(\d)+'),
    'YYYY.MM.DD':   ('.',           0,          1,          2,          '(\s)*(\d)+[\.](\s)*(\d)+[\.](\s)*(\d)+'),
    'YYYY.DD.MM':   ('.',           0,          2,          1,          '(\s)*(\d)+[\.](\s)*(\d)+[\.](\s)*(\d)+'),
    'MM.DD.YYYY':   ('.',           2,          0,          1,          '(\s)*(\d)+[\.](\s)*(\d)+[\.](\s)*(\d)+'),
    'DD.MM.YYYY':   ('.',           2,          1,          0,          '(\s)*(\d)+[\.](\s)*(\d)+[\.](\s)*(\d)+'),
    'HH:MM:SS'  :   (':',           0,          1,          2,          '(\d)+[:](\d+)[:](\d+)')
    }

# Convert a date/time string to a timestamp
# Input string = YYYY/MM/DD HH:MM:SS AM/PM (epochDate)."
# May also be variants of the above. Must check for all cases
# dtStr = date/time string
# dfmt is date format - defaults to user-defined date format in .rc file
# tfmt is time format - - defaults to user-defined time format in .rc file
# utcOffset is UTC offset info as extracted from the incoming email message.
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
    dtPat = re.compile(dtFmtDefs[dfmt][4])  # Compile regex for date/time pattern
    dateMatch = re.match(dtPat,dtStr)        # Match regex against date/time
    if dateMatch:
        dateStr = dtStr[dateMatch.regs[0][0]:dateMatch.regs[0][1]]   # Extract the date string
    else:
        return None
    datePart = re.split(re.escape(dtFmtDefs[dfmt][0]), dateStr)     # Split date string based on the delimeter
    year = int(datePart[yrCol])
    month = int(datePart[moCol])
    day = int(datePart[dyCol])
    
    # Get column positions
    hrCol = dtFmtDefs[tfmt][1] # Which field holds the Hour?
    mnCol = dtFmtDefs[tfmt][2] # Which field holds the minute?
    seCol = dtFmtDefs[tfmt][3] # Which field holds the seconds?
 
    # Extract the time
    tmPat = re.compile(dtFmtDefs[tfmt][4])
    timeMatch = re.search(tmPat,dtStr)
    if timeMatch:
        timeStr = dtStr[timeMatch.regs[0][0]:timeMatch.regs[0][1]]
    else:
        return None
    timePart = re.split(re.escape(dtFmtDefs[tfmt][0]), timeStr)
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
    ts = datetime.datetime(year, month, day, hour, minute, second).timestamp()

    # Apply email's UTC offset to date/time
    # Need to separate the two 'if' statements because the init routines crash otherwise
    # (Referencing globs.opts[] before they're set)
    if utcOffset is not None:
        if globs.opts['applyutcoffset']:
            ts += float(utcOffset)

    globs.log.write(1,'Date/Time converted to [{}]'.format(ts))

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
# Return current timestamp
def currenttimestamp():
    curtimestamp = int(time.time())
    return curtimestamp
