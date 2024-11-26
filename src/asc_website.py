"""Backend for downloading All Sky Camera images
"""

import os
import zipfile
import io
import json

from pathlib import Path
from datetime import datetime

import pandas as pd
import pytz

from flask import Flask, request, send_file, render_template, jsonify
from tools import get_sidereal_time,select_images

pd.options.mode.copy_on_write = True

app = Flask(__name__)

# Load the CSV database
CONFIG_NAME = 'config_local.json'
CONFIG_DIR = "../config/" + CONFIG_NAME
CONFIG_PATH = (Path(__file__).parent / CONFIG_DIR).resolve()
with open(CONFIG_PATH, 'r', encoding="utf-8") as f:
    config = json.load(f)
db_location = config['db_location']
base_dir = config['base_dir']
df = pd.read_csv(db_location, parse_dates=['Timestamp middle','Timestamp middle UTC'])

# Add column of the date of the night of capture
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

    For now, one image per night is chosen closest to
    the sidereal time of the reference date and time.

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

    reference_datetime : str
        Date and time from which the
        reference sidereal time will be calculated
        (or the start of the sidereal time range).
        Formatted as "%Y-%m-%dT%H:%M"
        
    reference_datetime_end : str
        Date and time from which the end of the
        sidereal time range will be calculated.
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
    reference_datetime = request.form['sidereal_datetime']
    reference_datetime_end = request.form['sidereal_datetime_end']
    limit_clear_images = request.form.get('limit_clear_images') == 'on'  # Checkbox value
    only_calculate = False
    if request.form['only_calculate'] == "true":
        only_calculate = True

    # Get sidereal time from reference time
    reference_datetime_utc = adelaide_tz.localize(
                    datetime.strptime(
                    reference_datetime, "%Y-%m-%dT%H:%M")
                    )
    sidereal_start = get_sidereal_time(
                        reference_datetime_utc.astimezone(pytz.utc))
    if reference_datetime_end:
        reference_datetime_end_utc = adelaide_tz.localize(
                        datetime.strptime(
                        reference_datetime_end, "%Y-%m-%dT%H:%M")
                        )
        sidereal_end = get_sidereal_time(
                            reference_datetime_end_utc.astimezone(pytz.utc))
    else:
        sidereal_end = None

    selected_images, total_size_mb = select_images(
                                    df,
                                    start_date,
                                    end_date,
                                    sidereal_start,
                                    sidereal_end = sidereal_end,
                                    limit_clear_images=limit_clear_images)

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
