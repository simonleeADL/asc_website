"""Useful tools for the All Sky Camera image downloader

julian_date, siderial_time:
Copied from https://www.nies.ch/doc/astro/sternzeit.en.php
Licensed under CC BY
"""

import numpy as np


def latinise_bayer_id(bayer_id):
    """
    Change the Bayer ID (Greek letter for star number,
    short name for constallaton) to a full Latinsed name.
    """
    try:
        parts = bayer_id.split(" ", 1)
    except:
        return bayer_id
    # Mapping of Greek letters to their Latin equivalents
    greek_to_latin = {
        "α": "Alpha",
        "β": "Beta",
        "γ": "Gamma",
        "δ": "Delta",
        "ε": "Epsilon",
        "ζ": "Zeta",
        "η": "Eta",
        "θ": "Theta",
        "ι": "Iota",
        "κ": "Kappa",
        "λ": "Lambda",
        "μ": "Mu",
        "ν": "Nu",
        "ξ": "Xi",
        "ο": "Omicron",
        "π": "Pi",
        "ρ": "Rho",
        "σ": "Sigma",
        "τ": "Tau",
        "υ": "Upsilon",
        "φ": "Phi",
        "ϕ": "Phi",
        "χ": "Chi",
        "ψ": "Psi",
        "ω": "Omega",
    }

    # Mapping of constellation abbreviations to full names
    constellation_abbr_to_full = {
        "And": "Andromeda",
        "Ant": "Antlia",
        "Aps": "Apus",
        "Aql": "Aquila",
        "Aqr": "Aquarius",
        "Ara": "Ara",
        "Ari": "Aries",
        "Aur": "Auriga",
        "Boo": "Boötes",
        "Cae": "Caelum",
        "Cam": "Camelopardalis",
        "Cap": "Capricornus",
        "Car": "Carina",
        "Cas": "Cassiopeia",
        "Cen": "Centaurus",
        "Cep": "Cepheus",
        "Cet": "Cetus",
        "Cha": "Chamaeleon",
        "Cir": "Circinus",
        "Col": "Columba",
        "Com": "Coma Berenices",
        "CrA": "Corona Australis",
        "CrB": "Corona Borealis",
        "Crt": "Crater",
        "Cru": "Crux",
        "Cyg": "Cygnus",
        "Del": "Delphinus",
        "Dor": "Dorado",
        "Dra": "Draco",
        "Equ": "Equuleus",
        "Eri": "Eridanus",
        "For": "Fornax",
        "Gem": "Gemini",
        "Gru": "Grus",
        "Her": "Hercules",
        "Hor": "Horologium",
        "Hya": "Hydra",
        "Hyi": "Hydrus",
        "Ind": "Indus",
        "Lac": "Lacerta",
        "Leo": "Leonis",
        "Lep": "Lepus",
        "Lib": "Libra",
        "LMi": "Leo Minor",
        "Lup": "Lupus",
        "Lyn": "Lynx",
        "Lyr": "Lyra",
        "Men": "Mensa",
        "Mic": "Microscopium",
        "Mon": "Monoceros",
        "Mus": "Musca",
        "Nor": "Norma",
        "Oct": "Octans",
        "Oph": "Ophiuchus",
        "Ori": "Orion",
        "Pav": "Pavo",
        "Peg": "Pegasus",
        "Per": "Perseus",
        "Phe": "Phoenix",
        "Pic": "Pictor",
        "PsA": "Piscis Austrinus",
        "Psc": "Pisces",
        "Pup": "Puppis",
        "Pyx": "Pyxis",
        "Ret": "Reticulum",
        "Scl": "Sculptor",
        "Sco": "Scorpius",
        "Sct": "Scutum",
        "Ser": "Serpens",
        "Sex": "Sextans",
        "Sge": "Sagitta",
        "Sgr": "Sagittarius",
        "Tau": "Taurus",
        "Tel": "Telescopium",
        "Tri": "Triangulum",
        "Tuc": "Tucana",
        "UMa": "Ursa Major",
        "UMi": "Ursa Minor",
        "Vel": "Vela",
        "Vir": "Virgo",
        "Vol": "Volans",
        "Vul": "Vulpecula",
        "CMa": "Canis Majoris",
        "CMi": "Canis Minor",
        "TrA": "Triangulum Australe",
    }
    if len(parts) == 2:
        greek_letter, constellation = parts
        number = ""
        if len(greek_letter) == 2:
            number = greek_letter[1]
            greek_letter = greek_letter[0]
        latin_greek = greek_to_latin.get(greek_letter, greek_letter)
        full_constellation = constellation_abbr_to_full.get(
            constellation, constellation
        )
        return f"{latin_greek}{number} {full_constellation}"
    return bayer_id


def julian_date(year, month, day, utc=0):
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
    h = utc / 24
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
        a = int(y / 100)
        b = 2 - a + int(a / 4)
    jd = int(365.25 * (y + 4716)) + int(30.6001 * (m + 1)) + d + h + b - 1524.5
    return jd


def siderial_time(year, month, day, utc=0, long=0):

    ## Copied from https://www.nies.ch/doc/astro/sternzeit.en.php
    ## Licensed under CC BY

    """
    Returns the siderial time in decimal hours. Longitude (long) is in
    decimal degrees. If long=0, return value is Greenwich Mean Siderial Time
    (GMST).
    """
    jd = julian_date(year, month, day)
    t = (jd - 2451545.0) / 36525
    # Greenwich siderial time at 0h UTC (hours)
    st = (24110.54841 + 8640184.812866 * t + 0.093104 * t**2 - 0.0000062 * t**3) / 3600
    # Greenwich siderial time at given UTC
    st = st + 1.00273790935 * utc
    # Local siderial time at given UTC (longitude in degrees)
    st = st + long / 15
    st = st % 24
    return st


def get_sidereal_time(utc_time):
    """Provides sidereal time (hours) for a given UTC time (datetime)"""
    year = utc_time.year
    month = utc_time.month
    day = utc_time.day
    utc = utc_time.hour + utc_time.minute / 60 + utc_time.second / 3600

    long = 138.60298
    lmst = siderial_time(year, month, day, utc, long)
    return lmst


def select_images(
    df,
    start_date,
    end_date,
    sidereal_start,
    sidereal_end=None,
    time_limit=0.5,
    limit_clear_images=False,
):
    """Selects images based on date range and sidereal time

    This function is provided a start and end date.
    Images are chosen between these dates (at midday).

    The all-sky camera puts images in folders
    based on the "night" in which they were captured.
    e.g. a photo taken at 2020-01-02 01:00 (1AM on Jan 2nd)
    will be in the 20200101 folder and considered to be
    part of the 2020-01-01 "night".

    Thus, selecting 2020-01-02 as the start date
    will *not* include images taken before
    2020-01-02 12:00 (midday on Jan 2nd).

    But selecting 2020-01-03 as the end date
    will include images taken *all the way up to*
    2020-01-04 12:00 (midday on Jan 3rd).

    If "sidereal_end" is not given, one image is chosen
    per "night" that is closest to "sidereal_start",
    so the stars should be in the same place in the image.

    If "sidereal_end" *is* given, images are chosen
    within the range of sidereal times.

    Parameters
    ----------
    start_date : str
        First night in the date range.
        Formatted as "%Y-%m-%d"

    end_date : str
        Last night in the date range.
        Formatted as "%Y-%m-%d"

    sidereal_start : float
        Reference sidereal time
        (or start of sidereal time range).

    sidereal_end : float
        Sidereal time range end.

    limit_clear_images : bool
        Boolean to restrict to images that are
        more likely to have clear skies
        (right now just based on filesize).

    Returns
    -------
    selected_images : list of strings
        List of selected image paths.

    total_size_mb : float
        Total size of all the chosen images.
    """
    # Filter to just the images in the date range
    df_filtered = df[(df["night_date"] >= start_date) & (df["night_date"] <= end_date)]

    # Going to list files and count filesize
    selected_images = []
    total_size_mb = 0.0

    # Remove images outside of expected file size (likely to not be clear skies)
    if limit_clear_images:
        df_filtered = df_filtered[
            df_filtered["Filesize (bytes)"].between(10500000, 11000000)
        ]

    # Calculate sidereal time for all relevant images.
    # (done here and not earlier to save on processing time)
    df_filtered["sidereal_time"] = df_filtered["Timestamp middle UTC"].apply(
        get_sidereal_time
    )

    if sidereal_end is None:
        # If no sidereal end time is provided, choose one image
        # per night closest to the sideral start time.
        # Iterate through dates.
        for _, night_group in df_filtered.groupby("night_date"):
            # Sometimes limiting to clear images
            # results in nothing at all.
            if len(night_group) == 0:
                continue

            # Choose all images within the "time_limit"
            # distance from the reference sidereal time.
            valid_images = night_group[
                np.minimum(
                    (night_group["sidereal_time"] - sidereal_start) % 24,
                    (sidereal_start - night_group["sidereal_time"]) % 24,
                )
                < time_limit
            ]

            # Sometimes there are no images near the
            # reference time after selecting clear images
            # and requiring a narrow time limit.
            if len(valid_images) == 0:
                continue

            # Choose the image closest to the reference time.
            closest_image = valid_images.iloc[
                (valid_images["sidereal_time"] - sidereal_start).abs().argsort()[:1]
            ]

            # Update the total size and the selected image list.
            total_size_mb += closest_image["Filesize (bytes)"].values[0] / (1000 * 1000)
            selected_images.append(closest_image["Directory"].values[0])
    else:
        # Choose images between sidereal start and
        # end times. Different logic for whether
        # the end time is larger or small than
        # the start time (sidereal time is mod 24)
        if sidereal_start < sidereal_end:
            valid_images = df_filtered[
                (df_filtered["sidereal_time"] >= sidereal_start)
                & (df_filtered["sidereal_time"] <= sidereal_end)
            ]
        else:
            valid_images = df_filtered[
                (df_filtered["sidereal_time"] >= sidereal_start)
                | (df_filtered["sidereal_time"] <= sidereal_end)
            ]
        # Update the total size and the selected image list.
        selected_images += list(valid_images["Directory"])
        total_size_mb += sum(valid_images["Filesize (bytes)"]) / (1000 * 1000)
    return selected_images, total_size_mb
