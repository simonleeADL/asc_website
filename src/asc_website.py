"""Backend for downloading All Sky Camera images
"""

import os
import zipfile
import io
import json

from pathlib import Path
from datetime import datetime

import pandas as pd
import numpy as np
import pytz

from flask import Flask, request, send_file, render_template, jsonify
from tools import get_sidereal_time

pd.options.mode.copy_on_write = True

app = Flask(__name__)

# Load the CSV database

CONFIG_NAME = 'config_local.json'

CONFIG_DIR = "../config/" + CONFIG_NAME
CONFIG_PATH = (Path(__file__).parent / CONFIG_DIR).resolve()

with open(CONFIG_PATH, 'r', encoding="utf-8") as f:
    config = json.load(f)

# Access the parameters
db_location = config['db_location']
base_dir = config['base_dir']

df = pd.read_csv(db_location, parse_dates=['Timestamp middle','Timestamp middle UTC'])

df['night_date'] = df['Directory'].str[:8]
image_counts = df.groupby(df['night_date']).size().reset_index(name='image_count_per_night')
df['night_date'] = pd.to_datetime(df['night_date'])

adelaide_tz = pytz.timezone('Australia/Adelaide')

@app.route('/')
def index():
    """ Provides HTML file for the website
    """
    return render_template('index.html')

@app.route('/get_image_counts')
def get_image_counts():
    """ Provides counts of the number of images per night
    """
    data = image_counts.to_dict(orient='records')
    return jsonify(data)

@app.route('/download', methods=['POST'])
def download_images():
    """ Allows for downloading images based on date range and sidereal time
    
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
    
    A reference time is also provided from which the
    refernce sidereal time will be calculated.
    Currently, one image is chosen per "night" that is
    closest to this sidereal time, so the stars should
    all be in the same place in the image.
    
    A checkbox can be ticked to that instead of downloading
    the images, just the total filesize is presented.
    
    Parameters
    ----------
    start_date : str 
        First night in the date range.
        Formatted as "%Y-%m-%d"
        
    end_date : str 
        Last night in the date range.
        Formatted as "%Y-%m-%d"
        
    sidereal_datetime : str 
        Date and time from which the 
        reference sidereal time will be calculated.
        Formatted as "%Y-%m-%dT%H:%M"
        
    limit_clear_images : str
        Boolean to restrict to images that are
        more likely to have clear skies
        (right now just based on filesize).
        
    only_calculate : bool
        If true, just return the total filesize
        of chosen images.
        
    Returns
    -------
    total_size_mb : float
        Total size of all the chosen images.
    
    zip_buffer : .zip
        Compressed folder including all chosen images
    """
    start_date = request.form['start_date']
    end_date = request.form['end_date']
    sidereal_datetime = request.form['sidereal_datetime']
    limit_clear_images = request.form.get('limit_clear_images') == 'on'  # Checkbox value
    only_calculate = False
    if request.form['only_calculate'] == "true":
        only_calculate = True
    time_limit = 0.5 # Max number of hours from sidereal time acceptable

    # Convert Adelaide time to UTC
    adelaide_time = adelaide_tz.localize(
                    datetime.strptime(
                    sidereal_datetime, "%Y-%m-%dT%H:%M")
                    )

    # Get the sidereal time for this specific UTC time
    sidereal_target = get_sidereal_time(
                        adelaide_time.astimezone(pytz.utc))

    # Filter based on date range
    df_filtered = df[(df['night_date'] >= start_date) & (df['night_date'] <= end_date)]

    selected_images = []
    total_size_mb = 0.0

    # Group images by night
    for _, night_group in df_filtered.groupby('night_date'):

        if limit_clear_images:
            night_group = night_group[
            night_group['Filesize (bytes)'].between(10500000, 11000000)
            ]
        if len(night_group) == 0:
            continue

        night_group['sidereal_time'] = night_group['Timestamp middle UTC'].apply(get_sidereal_time)
        valid_images = night_group[
            np.minimum(
                (night_group['sidereal_time'] - sidereal_target) % 24,
                (sidereal_target - night_group['sidereal_time']) % 24
            ) < time_limit
        ]

        if len(valid_images) == 0:
            continue

        closest_image = valid_images.iloc[
        (valid_images['sidereal_time'] - sidereal_target).abs().argsort()[:1]
        ]

        total_size_mb += closest_image['Filesize (bytes)'].values[0] / (1000 * 1000)
        selected_images.append(closest_image['Directory'].values[0])

    if only_calculate:
        return jsonify({'total_size_mb': total_size_mb})
    # Zip the selected images (same as before)
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w') as zf:
        for directory in selected_images:
            file_path = base_dir + directory
            zf.write(file_path, os.path.basename(file_path))

    zip_buffer.seek(0)

    return send_file(zip_buffer,
                    mimetype='application/zip',
                    as_attachment=True,
                    download_name='images.zip')

@app.route('/download_by_date')
def download_by_date():
    """Downloads all images from one night
    """
    date = request.args.get('date')  # YYYYMMDD
    # Find all directories starting with the date
    matching_files = df[df['Directory'].str[:8]==date]

    # Create a ZIP file with those images
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w') as zf:
        for file_path in matching_files['Directory'].values:
            file_path = base_dir + file_path
            print(file_path)
            zf.write(file_path, os.path.basename(file_path))

    zip_buffer.seek(0)
    return send_file(zip_buffer,
                    as_attachment=True,
                    download_name=f'{date}_images.zip',
                    mimetype='application/zip')

if __name__ == '__main__':
    app.run(debug=True)
