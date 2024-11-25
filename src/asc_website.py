from flask import Flask, request, send_file, render_template, jsonify
import pandas as pd
import os
import zipfile
import io
from datetime import datetime, date, time, tzinfo, UTC, timedelta, timezone
import pytz
from tools import get_sidereal_time

pd.options.mode.copy_on_write = True

app = Flask(__name__)

# Load the CSV database

#db_location = '~/Dropbox/Uni/2024/ASC/asc_full_database.csv' # Not all files available on device
#base_dir = '/mnt/allsky/'
db_location = '~/Dropbox/Uni/2024/ASC/asc_website/data/asc_database.csv' # Use for testing on device
base_dir = '/home/simon/Desktop/allsky_test/'

df = pd.read_csv(db_location, parse_dates=['Timestamp middle','Timestamp middle UTC'])

df['image_date'] = df['Directory'].str[:8]
image_counts = df.groupby(df['image_date']).size().reset_index(name='image_count')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/get_image_counts')
def get_image_counts():
    # Return the data as JSON for the frontend to consume
    data = image_counts.to_dict(orient='records')
    return jsonify(data)

@app.route('/download', methods=['POST'])
def download_images():
    start_date = request.form['start_date']
    end_date = request.form['end_date']
    adelaide_time_str = request.form['sidereal_datetime']
    limit_clear_images = request.form.get('limit_clear_images') == 'on'  # Checkbox value
    if request.form['only_calculate'] == "true":
        only_calculate = True
    if request.form['only_calculate'] == "false":
        only_calculate = False

    # Convert Adelaide time to UTC
    adelaide_tz = pytz.timezone('Australia/Adelaide')
    adelaide_time = adelaide_tz.localize(datetime.strptime(adelaide_time_str, "%Y-%m-%dT%H:%M"))
    utc_time = adelaide_time.astimezone(pytz.utc)

    # Get the sidereal time for this specific UTC time
    sidereal_target = get_sidereal_time(utc_time)

    # Filter based on date range (same as before)
    df_filtered = df[(df['Timestamp middle'] >= start_date) & (df['Timestamp middle'] <= end_date)]

    # Group images by night (defined as 12:00 PM to 12:00 PM)
    selected_images = []
    total_size_mb = 0.0
    for _, night_group in df_filtered.groupby(pd.Grouper(key='Timestamp middle', freq='24h', offset='12h')):  # Grouping by night
        
        if limit_clear_images:
            night_group = night_group[(night_group['Filesize (bytes)'] >= 10500000)&(night_group['Filesize (bytes)'] <= 11000000)]  # Filter for clear images
        if len(night_group) == 0:
            continue
            
        night_group['sidereal_time'] = night_group['Timestamp middle UTC'].apply(get_sidereal_time)
        valid_images = night_group[(night_group['sidereal_time'] - sidereal_target).abs() < 0.5]
        if len(valid_images) == 0:
            continue
        closest_image = valid_images.iloc[(valid_images['sidereal_time'] - sidereal_target).abs().argsort()[:1]]
        
        total_size_mb += closest_image['Filesize (bytes)'].values[0] / (1000 * 1000)  # Convert bytes to MB
        selected_images.append(closest_image['Directory'].values[0])
        
    if only_calculate:
        return jsonify({'total_size_mb': total_size_mb})
    else:
        # Zip the selected images (same as before)
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w') as zf:
            for directory in selected_images:
                file_path = base_dir + directory
                zf.write(file_path, os.path.basename(file_path))

        zip_buffer.seek(0)

        return send_file(zip_buffer, mimetype='application/zip', as_attachment=True, download_name='images.zip')

@app.route('/download_by_date')
def download_by_date():
    date = request.args.get('date')  # YYYYMMDD
    # Find all directories starting with the date
    matching_files = df[df['Directory'].str[:8]==date]

    #base_dir = '/home/simon/Desktop/allsky_test/'
    base_dir = '/mnt/allsky/'
    
    # Create a ZIP file with those images
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w') as zf:
        for file_path in matching_files['Directory'].values:
            file_path = base_dir + file_path
            print(file_path)
            zf.write(file_path, os.path.basename(file_path))

    zip_buffer.seek(0)
    return send_file(zip_buffer, as_attachment=True, download_name=f'{date}_images.zip', mimetype='application/zip')

if __name__ == '__main__':
    app.run(debug=True)

