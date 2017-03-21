#!/usr/bin/env python
import gspread
from flask import Flask, render_template
from flask_script import Manager, Shell
from oauth2client.service_account import ServiceAccountCredentials
from mapbox import Geocoder

app = Flask(__name__)
manager = Manager(app)

def make_shell_context():
    return dict(app=app)

manager.add_command("shell", Shell(make_context=make_shell_context))


highland_park_bbox = 	[-79.936351, 40.464845, -79.908334, 40.484]
highland_park_center = [-79.9195, 40.4723]
geocoder = Geocoder()

scope = ['https://spreadsheets.google.com/feeds']
creds = ServiceAccountCredentials.from_json_keyfile_name('client_secret.json', scope)
client = gspread.authorize(creds)
workbook = client.open_by_key('12OdDOCSp67kNgb1eVVamZJWpZQUcUyVAiZOghMamnJU')
sheet = workbook.get_worksheet(0)




@app.route('/')
def index():
    spreadsheet_list = sheet.get_all_values()
    for row in range(1,len(spreadsheet_list)):
        if spreadsheet_list[row][3] is '':
            geocoder_response = geocoder.forward(spreadsheet_list[row][0], bbox=highland_park_bbox)
            if geocoder_response.geojson()['features']:
                lon, lat= geocoder_response.geojson()['features'][0]['center']
                sheet.update_cell(row+1,4, lat)
                sheet.update_cell(row+1,5, lon)
 
    
    #print sheet.get_all_records()
    return render_template('index.html', highland_park_center=list(reversed(highland_park_center)), locations=sheet.get_all_records())

if __name__ == '__main__':
    manager.run()

