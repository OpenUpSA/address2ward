from __future__ import print_function
import json
from geopy.geocoders import GoogleV3
import config
import psycopg2
from datetime import datetime
from omgeo import Geocoder
import urllib2, urllib
import logging

logger = logging.getLogger(config.LOGGER_NAME)

default_db = "wards_2006"
class AddressConverter(object):
    def __init__(self, curs):
        self.curs = curs
        self.geolocator = GoogleV3()
        
        self.geocoder = Geocoder()
        
    def resolve_address_google(self, address):
        try:
            address = urllib.quote(address)
            url = "https://maps.googleapis.com/maps/api/geocode/json?address=%s&sensor=false&region=za&key=%s" % (address, config.google_key)
            response = urllib2.urlopen(url)
            js = response.read()
            try:
                js = json.loads(js)
            except ValueError:
                logger.exception("Error trying to resolve %s" % address)
                return None

            if "results" in js and len(js["results"]) > 0:
                result = js["results"][0]
                geom = js["results"][0]["geometry"]["location"]
                lat = geom["lat"]; lng = geom["lng"]   
                formatted_address = result["formatted_address"]

                return formatted_address, lat, lng
        except Exception:
            logger.exception("Error trying to resolve %s" % address)
        return None
        
    def resolve_address_esri(self, address):
        result = self.geocoder.geocode(address + ", South Africa")
        if not result: return None
        if not "candidates" in result: return None
        if len(result["candidates"]) == 0: return None
        candidate = result["candidates"][0]
        address = candidate.match_addr
        latitude = candidate.y
        longitude = candidate.x

        return address, latitude, longitude
        
    def convert(self, address):
        now1 = datetime.now()
        result = self.resolve_address_google(address)
        if not result: return None
        address, latitude, longitude = result
        now2 = datetime.now()

        poi = (longitude, latitude)
        sql = """
            SELECT
                province,
                municname,
                ward_id,
                ward_no
            FROM
                wards,
                (SELECT ST_MakePoint(%s, %s)::geography AS poi) AS f
            WHERE ST_DWithin(geog, poi, 1);"""

        self.curs.execute(sql, poi)
        now3 = datetime.now()

        for row in self.curs.fetchall():
            return {
                "address" : address,
                "coords" : poi,
                "province" : row[0],
                "municipality" : row[1],
                "ward" : row[2],
                "ward_no" : int(row[3]),
                "now21" : str(now2 - now1),
                "now32" : str(now3 - now2),
                "now31" : str(now3 - now1),
            }

if __name__ == "__main__":
    conn = psycopg2.connect(
        database=config.database, user=config.db_user,
        host=config.db_host, password=config.db_password
    )
    try:
        curs = conn.cursor()
        c = AddressConverter(curs)

        while True:
            address = raw_input("Enter in an address: ")
            js = c.convert(address)
            if not js:
                print("Address: %s, could not be found" % address)
                continue

            print("Full Address: %s" % js["address"])
            print("Coords: %f, %f" % js["coords"])
            print("Province: %s" % js["province"])
            print("Municipality: %s" % js["municipality"])
            print("Ward: %s" % js["ward"])
            print("Ward No: %s" % js["ward_no"])
            print("")
    finally:
        conn.close()
