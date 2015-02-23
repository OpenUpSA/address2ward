Simple script that converts street addresses to South African Wards.

Local Development
=================

Clone the repo and ensure you have python, virtualenv and pip installed.

    virtualenv env --no-site-packages
    source env/bin/activate
    pip install -r requirements.txt
    python web.py

You'll need Postgres with the PostGIS extension.

Production Deployment
=====================


Production deployment assumes you're running on Heroku.

You will need:

* a Google API key for the Google geocoding API
* a New Relic license key

The run:

    heroku create
    heroku addons:add heroku-postgresql
    heroku addons:add newrelic:stark
    heroku config:set GOOGLE_API_KEY=the-key \
                      NEW_RELIC_APP_NAME="Address2Ward" \
                      NEW_RELIC_LICENSE_KEY=some-license-key
    git push heroku master
