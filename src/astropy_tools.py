"""All-Sky Camera tools based on astropy"""

import io
import base64
from pathlib import Path

import astropy.units as u
from astropy.coordinates import AltAz, EarthLocation, SkyCoord, get_body
from astropy.time import Time
from astroquery.vizier import Vizier
from astropy.visualization import quantity_support

import matplotlib.pyplot as plt
import matplotlib
import numpy as np
import pandas as pd

from tools import latinise_bayer_id

quantity_support()
matplotlib.use("agg")

asc = EarthLocation(lat=-34.92 * u.deg, lon=138.6 * u.deg, height=50 * u.m)


def source_from_name(name):
    """
    Get the astropy SkyCoord based on the name of the source
    """
    try:
        return SkyCoord.from_name(name)
    except:
        print(f"Whoops can't find {name}")
    return None


def source_from_coord(ra, dec):
    """
    Get the astropy SkyCoord based on the ra and dec (in degrees)
    """
    return SkyCoord(ra=ra * u.deg, dec=dec * u.deg)


def plot_over_sidereal(sidereal_times, altitudes, min_alt=10 * u.deg, name=""):
    """
    Plot source altitude based on sidereal time
    """
    img = io.BytesIO()
    plt.figure(figsize=(4, 3))

    plt.scatter(sidereal_times, altitudes, 2, c="goldenrod")
    plt.axhline(min_alt, color="r", ls=":")
    plt.fill_between([0, 24], -10, 0, color="grey", alpha=0.33)

    plt.fill_between(
        sidereal_times,
        min_alt,
        altitudes,
        color="goldenrod",
        alpha=0.33,
        where=altitudes > min_alt,
    )

    plt.xticks((np.arange(13) * 2) * u.hour)

    plt.ylim(-10, 90)
    plt.xlim(0, 24)
    plt.xlabel("Sidereal time (h)")
    plt.ylabel("Altitude (deg)")
    plt.title(name)

    plt.savefig(img, format="png", bbox_inches="tight")
    img.seek(0)
    plot_url = base64.b64encode(img.getvalue()).decode()
    plt.close()
    return '<img src="data:image/png;base64,{}">'.format(plot_url)


def plot_over_night(source, date, location=asc, min_alt=10 * u.deg, name=""):
    """
    Plot source altitude over a given night
    """
    times = Time(date) + (np.linspace(0.5, 1.5, 1000) * u.day) - 10.5 * u.h
    altaz_frame = AltAz(obstime=times, location=location)

    altitudes = source.transform_to(altaz_frame).alt

    delta_midnight = np.linspace(-12, 12, 1000) * u.hour

    img = io.BytesIO()

    plt.figure(figsize=(4, 3.4))
    plt.axhline(min_alt, color="r", ls=":")

    plt.plot(delta_midnight, altitudes, lw=4, c="red", label=name, zorder=100)
    plt.fill_between(delta_midnight, -10, 0, color="grey", alpha=0.33)

    sun = get_body("sun", times).transform_to(altaz_frame)
    moon = get_body("moon", times).transform_to(altaz_frame)

    plt.plot(delta_midnight, sun.alt, color="goldenrod", label="Sun")

    plt.plot(delta_midnight, moon.alt, color="silver", label="Moon")

    plt.fill_between(
        delta_midnight,
        0 * u.deg,
        90 * u.deg,
        sun.alt < -0 * u.deg,
        color="0.5",
        zorder=0,
    )

    plt.fill_between(
        delta_midnight,
        0 * u.deg,
        90 * u.deg,
        sun.alt < -18 * u.deg,
        color="k",
        zorder=0,
    )

    plt.ylim(-10, 90)
    plt.xlim(-12, 12)

    plt.xticks(
        [-12, -8, -4, 0, 4, 8, 12],
        ["12:00", "16:00", "20:00", "00:00", "04:00", "08:00", "12:00"],
    )
    plt.gcf().autofmt_xdate()

    plt.xlabel("")
    plt.ylabel("Altitude (deg)")
    plt.title(f"Night of {date}")

    plt.legend(bbox_to_anchor=(1.02, 1.02), edgecolor="k")

    plt.savefig(img, format="png", bbox_inches="tight")
    img.seek(0)
    plot_url = base64.b64encode(img.getvalue()).decode()
    plt.close()
    return '<img src="data:image/png;base64,{}">'.format(plot_url)


def sidereal_times_alts(source, location=asc):
    """
    Return a list of sidereal times for one sidereal day,
    and the altitudes of a source in those times
    """
    times = (
        Time("2002-05-04 00:00:00") + (np.linspace(0, 0.99726956666, 1000) * u.day)[:-1]
    )  # That is a day where sidereal time 0h and midnight line up
    altaz_frame = AltAz(obstime=times, location=location)

    sidereal_times = times.sidereal_time("apparent", longitude=location.lon).hour
    altitudes = source.transform_to(altaz_frame).alt

    return sidereal_times, altitudes


def sidereal_start_end_times(sidereal_times, altitudes, min_alt=15 * u.deg, name=""):
    """
    Return the start and end sideral times wherein
    a source will be above a certain altitude
    """
    mask = altitudes >= min_alt

    if sum(mask) == 0:
        print(f"Sorry, {name} only got to {max(altitudes):.2f}")
        return 0.0, 0.0

    if sum(mask) == len(mask):
        return 0.0, 24.0

    transitions = np.diff(
        mask.astype(int)
    )  # Compute the difference between consecutive elements
    start_index = np.where(transitions == 1)[0] + 1  # Indices of False -> True (start)
    end_index = np.where(transitions == -1)[0]  # Indices of True -> False (end)

    start_lst = sidereal_times[start_index][0]
    end_lst = sidereal_times[end_index][0]

    return start_lst, end_lst


def get_bright_star_catalogue(n=100):
    """
    Return a pandas dataframe of bright stars visible from Adelaide.
    """
    # Observer's latitude (Adelaide)
    latitude = -34.92

    vizier_hip = Vizier(
        columns=["RAICRS", "DEICRS", "Vmag", "HD", "HIP"],
        column_filters={"Vmag": "<6"},
        row_limit=10000,
    )  # Query Hipparcos
    hip_catalog = vizier_hip.query_constraints(catalog="I/239")[
        0
    ]  # Stars brighter than Vmag 6

    visible_declination = (hip_catalog["DEICRS"] > latitude - 90) & (
        hip_catalog["DEICRS"] < latitude + 90
    )  # Filter by declination
    visible_objects = hip_catalog[visible_declination]  # Filter the catalog
    visible_objects.sort("Vmag")  # Sort by brightness (Vmag)

    brightest_objects = visible_objects[:n].to_pandas()  # Select the n brightess

    # From https://exopla.net/star-names/modern-iau-star-names/
    star_names = (Path(__file__).parent / "../data/stars.csv").resolve()
    name_catalog = pd.read_csv(star_names)  # Read star names file
    name_catalog["Bayer ID"] = name_catalog["Bayer ID"].apply(
        latinise_bayer_id
    )  # Latinise

    brightest_objects_names = pd.merge(brightest_objects, name_catalog, how="left")

    pd.set_option("display.max_rows", 400)

    brightest_objects_names = brightest_objects_names.rename(
        columns={"RAICRS": "ra", "DEICRS": "dec"}
    )

    return brightest_objects_names
