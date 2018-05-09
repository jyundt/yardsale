# yardsale
## tl;dr
`yardsale` is a lightweight python (Flask) application that reads data from a Google Docs spreadsheet and generates a list + map of yard sale locations and items for sale.
 
## Background
The `yardsale` app was created for the 2017 [Highland Park](https://hpccpgh.org) yard sale. Previously, the yard sale map only existed in paper form. This project is an attempt to display an online list and map of all Highland Park yard sale participants and the items they are selling.
 
### Data
All data is read from a Google doc spreadsheet, there are **no** local storage requirements (e.g. there isn't a database).
 
[A service account](http://gspread.readthedocs.io/en/latest/oauth2.html) is required to read data from the Google doc spreadsheet. Additionally, [the Google doc spreadsheet ID/key](http://www.coolheadtech.com/blog/use-data-from-other-google-spreadsheets) will also be needed.
 
### Mapping
All mapping and geolocation is performed with [leaflet.js](http://leafletjs.com/) and [Mapbox](https://www.mapbox.com/). A [Mapbox API token](https://www.mapbox.com/help/create-api-access-token/) is required to run `yardsale`.
 
 
## Installation
### Requirements
The requirements for `yardsale` are pretty light; it should run on any version of Linux (or probably OSX) that has the following:
* python >= 2.7
* redis (tested with redis 3.2.9 but any version _should_ work)
* WSGI application server (I'd **highly** recommend [uwsgi](https://uwsgi-docs.readthedocs.io/en/latest/))
* webserver (I normally use nginx, but apache is fine too)
 
### Environment configuration
The following environment variables are parsed by `yardsale` and must be [set appropriately](https://www.cyberciti.biz/faq/set-environment-variable-linux/):
 - `SPREADSHEET_KEY` - [Google doc spreadsheet ID/key](http://www.coolheadtech.com/blog/use-data-from-other-google-spreadsheets)
 - `GAPPS_JSON_KEY` - *Path* to Google apps service account [client JSON secret file](http://gspread.readthedocs.io/en/latest/oauth2.html) [Note: this ENV var should be set to the *location* of the file, not the contents of the file.]
 - `MAPBOX_ACCESS_TOKEN` - [Mapbox API access token](https://www.mapbox.com/help/create-api-access-token/)
 
Depending on the WSGI application server used, an additional file may need to be created that contains these ENV vars. As an example, if using uWSGI, create a file with the variables listed above:
```
SPREADSHEET_KEY=###
GAPPS_JSON_KEY=###
MAPBOX_ACCESS_TOKEN=###
```
 
 
 
 ### Setup
 Start by checking out the `yardsale` code from github:
 ```
 $ git clone https://github.com/jyundt/yardsale.git
 ```
 
 Create a python virtual environment (virtualenv), activate the virtualenv install all python dependencies:
 
 Python 2.7:
 ```
 $ virtualenv venv
 $ . ./venv/bin/activate
 $ pip install -r yardsale/requirements.txt
 ```
 
 Python 3.x:
 ```
 $ python3 -m venv venv
 $ . ./venv/bin/activate
 $ pip install -r yardsale/requirements.txt
 ```
 
### Local dev server
To verify everything installed properly (and the ENV vars are configured properly), Flask can launch a local dev server. This server will only listen on `localhost:5000` by default, it should **not** be used for production purposes!
 
Note that you will still need to have a local redis instance for this development server.
 
 ```
 $ . ./venv/bin/activate
 $ ./yardsale/yardsale.py runserver -d -r
 ```
 
## Deployment
Instructions are provided for two different deployment models: ansible and "manual mode"
### Ansible
Checkout [the ansible readme](ansible/README.md) for instructions on deploying `yardsale` via ansible. The ansible playbook will configure redis/uwsgi/nginx identically to the manual steps listed below.

### Manual

A redis instance, WSGI application server and webserver are required to run the server side components. Any WSGI application server and webserver can be used, but uWSGI and nginx are used below for reference.
 
#### Redis
Install and start a redis instance using the appropriate package manager for your server. Or, use a [Docker container](https://hub.docker.com/_/redis/) (probably the easiest method). 
 
If docker is already configured and running on your server, something like this should work fine:
 
```
docker run -d -p 127.0.0.1:6379:6379 redis:3.2-alpine
```
 
Note that `yardsale` assume redis is running on the default port: `6379`.
 
#### uWSGI
The following steps can be used to deploy a uWSGI application server, but as previously mentioned, any WSGI compatible server can be used.
 
Note that it is *highly* suggested to create a non-privileged service account (and group) for running the application server.
 
First install uWSGI using the appropriate package manager for your server.
 
Create a uwsgi configuration file (locations may vary between distributions) with the following:
```
[uwsgi]
uid = YOURAPPLICATIONSERVICEACCOUNT
gid = YOURAPPLICATIONGROUPNAME
socket = 127.0.0.1:5000
master = true
enable-threads = True
chdir = LOCATIONOFTHEYARDSALECODE
venv = LOCATIONOFTHEVIRTUALENV
module = yardsale:app
plugin = python
for-readline = LOCATIONOFAFILETHATCONTAINSYOURENVVARS
  env = %(_)
endfor =
```
 
Start the uWSGI application server using the appropriate service management tool for your server: systemd, upstart, etc.
 
#### nginx
 
These instructions assume you are using uWSGI for the application server, please adjust them accordingly if you are using something else (gunicorn, tornado, etc)
 
##### SSL/TLS
It is **highly** recommended to secure your webserver with SSL/TLS. The [Let's Encrypt project](https://letsencrypt.org/) offers free SSL certificates if costs are a concern. The documentation below will assume SSL will be enabled and all traffic will be redirected from HTTP (unencrypted) -> HTTPS (encrypted) and that strong encryption will be enabled.
 
Install nginx using the appropriate package manager for your server.
 
Create a [strong DH key](https://michael.lustfield.net/nginx/getting-a-perfect-ssl-labs-score):
```
openssl dhparam -out /etc/nginx/dhparam.pem 4096
```
 
Create an nginx config file in the "conf.d" directory (locations may vary based on your server):
 
```
upstream uwsgicluster {
        server 127.0.0.1:5000;
    }
 
server {
    listen       80;
    server_name  yardsale.hpccpgh.org;
    return       301 https://$host$request_uri;
}
 
 
server {
    listen       443 ssl;
    server_name  yardsale.hpccpgh.org;
    add_header Strict-Transport-Security "max-age=31536000; 
    includeSubDomains";
    ssl_certificate YOURSSLCERT.PEM;
    ssl_certificate_key YOURSSLKEY.KEY;
    ssl_protocols TLSv1.2;
    ssl_prefer_server_ciphers on;
    ssl_ciphers ECDH+AESGCM:DH+AESGCM:ECDH+AES256:DH+AES256:ECDH+AES128:DH+AES:ECDH+3DES:DH+3DES:RSA+AESGCM:RSA+AES:RSA+3DES:!aNULL:!MD5:!DSS;
    ssl_ecdh_curve secp384r1; 
    ssl_session_cache shared:SSL:10m;
    ssl_session_tickets off; 
    ssl_stapling on; 
    ssl_stapling_verify on;
    ssl_dhparam /etc/nginx/dhparams.pem;
 
 
    location / {
        include            uwsgi_params;
        uwsgi_pass         uwsgi://uwsgicluster;
 
        proxy_redirect     off;
        proxy_set_header   Host $host;
        proxy_set_header   X-Real-IP $remote_addr;
        proxy_set_header   X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header   X-Forwarded-Host $server_name;
    }
}
```
Start nginx using the appropriate process manager for your server.
 
## Test!
At this point you should have a fully functional server. Validate that website loads and the map is drawn as expected. The first pageload _may_ timeout if a large amount of GPS coordinates need to be resolved. If that happens, don't worry, try again. Additionally, the redis cache may be "cold" (e.g. empty) which can also cause slow page loads. 
 
