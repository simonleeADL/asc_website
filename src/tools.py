def julian_date(year, month, day, utc=0):
    
    ## Copied from https://www.nies.ch/doc/astro/sternzeit.en.php
    ## Licensed under CC BY
    
    """
    Returns the Julian date, number of days since 1 January 4713 BC 12:00.
    utc is UTC in decimal hours. If utc=0, returns the date at 12:00 UTC.
    """
    if month > 2:
        y = year
        m = month
    else:
        y = year - 1
        m = month + 12
    d = day
    h = utc/24
    if year <= 1582 and month <= 10 and day <= 4:
        # Julian calendar
        b = 0
    elif year == 1582 and month == 10 and day > 4 and day < 15:
        # Gregorian calendar reform: 10 days (5 to 14 October 1582) were skipped.
        # In 1582 after 4 October follows the 15 October.
        d = 15
        b = -10
    else:
        # Gregorian Calendar
        a = int(y/100)
        b = 2 - a + int(a/4)
    jd = int(365.25*(y+4716)) + int(30.6001*(m+1)) + d + h + b - 1524.5
    return(jd)


def siderial_time(year, month, day, utc=0, long=0):

    ## Copied from https://www.nies.ch/doc/astro/sternzeit.en.php
    ## Licensed under CC BY
    
    """
    Returns the siderial time in decimal hours. Longitude (long) is in 
    decimal degrees. If long=0, return value is Greenwich Mean Siderial Time 
    (GMST).
    """
    jd = julian_date(year, month, day)
    t = (jd - 2451545.0)/36525
    # Greenwich siderial time at 0h UTC (hours)
    st = (24110.54841 + 8640184.812866 * t +
          0.093104 * t**2 - 0.0000062 * t**3) / 3600
    # Greenwich siderial time at given UTC
    st = st + 1.00273790935*utc
    # Local siderial time at given UTC (longitude in degrees)
    st = st + long/15
    st = st % 24
    return(st)

def get_sidereal_time(utc_time):
    year = utc_time.year
    month = utc_time.month
    day = utc_time.day
    utc = utc_time.hour + utc_time.minute/60 + utc_time.second/3600

    long = 138.60298
    lmst = siderial_time(year, month, day, utc, long)
    return lmst
