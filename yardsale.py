#!/usr/bin/env python
import gspread
import redis
import json
import time
from flask import Flask, render_template
from flask_script import Manager, Shell
from oauth2client.service_account import ServiceAccountCredentials
from mapbox import Geocoder

app = Flask(__name__)
manager = Manager(app)

def get_worksheet():
    """Auth to GApps and return a sheet"""
    scope = ['https://spreadsheets.google.com/feeds']
    creds = ServiceAccountCredentials.from_json_keyfile_name('client_secret.json', scope)
    client = gspread.authorize(creds)
    workbook = client.open_by_key('12OdDOCSp67kNgb1eVVamZJWpZQUcUyVAiZOghMamnJU')
    sheet = workbook.get_worksheet(0)
    return sheet


def add_lon_lat(sheet):
    """Update the sheet with lat/lon
    I didn't really spend the proper time debugging this behavior, but the
    oauth client will randomly time out and start to throw 401 errors.
    I added a simple try/except block to try to catch this error and
    re-auth if necessary.
    """
    try:
        spreadsheet_list = sheet.get_all_values()
    except gspread.exceptions.RequestError:
        sheet = get_worksheet()
        spreadsheet_list = sheet.get_all_values()

    """This is sorta clunky, but gspread can only update cells by position,
    so we have to get a list of lists and iterate through it.
    (Instead of returning a list of dicts similar to what we do for mapping.)
    """
    address_position = spreadsheet_list[0].index("address")
    lat_position = spreadsheet_list[0].index("lat")
    lon_position = spreadsheet_list[0].index("lon")
    for row in range(1,len(spreadsheet_list)):
        if spreadsheet_list[row][lat_position] is '':
            geocoder_response = geocoder.forward(spreadsheet_list[row][address_position],bbox=highland_park_bbox)
            if geocoder_response.geojson()['features']:
                lon, lat= geocoder_response.geojson()['features'][0]['center']
                sheet.update_cell(row+1, lat_position+1, lat)
                sheet.update_cell(row+1, lon_position+1, lon)
    return sheet

def get_all_data(redis_conn):
    """Query redis to see if we have a cached JSON blob of gspread data"""
    all_data = []
    if redis_conn.get('all_data') is None:
        sheet = get_worksheet()
        sheet = add_lon_lat(sheet)
        all_data = sheet.get_all_records()
        redis_conn.set('all_data', json.dumps(all_data), 300)
    else:
        all_data = json.loads(redis_conn.get('all_data'))

    return all_data
def make_shell_context():
    return dict(app=app)


manager.add_command("shell", Shell(make_context=make_shell_context))
highland_park_bbox = 	[-79.936351, 40.464845, -79.908334, 40.484]
highland_park_center = [-79.9195, 40.4723]
geocoder = Geocoder()
redis_conn = redis.StrictRedis(host='localhost', port=6379, db=0)




@app.route('/')
def index():
    
    return render_template('index.html',
                           highland_park_center=list(reversed(highland_park_center)),
                           locations=get_all_data(redis_conn))

if __name__ == '__main__':
    manager.run()

