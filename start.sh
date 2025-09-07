#!/bin/sh
cd /var/www/FlaskApp
. venv/bin/activate
exec gunicorn -w 1 -b 127.0.0.1:8000 app:app
