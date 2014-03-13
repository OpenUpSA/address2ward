from __future__ import print_function
import json
from geopy.geocoders import GoogleV3
import config
from config import configuration
import psycopg2
from datetime import datetime
from omgeo import Geocoder
import urllib2, urllib
import logging

logger = logging.getLogger(config.LOGGER_NAME)

class AddressConverter(object):
    def __init__(self, curs):
        self.curs = curs
        self.geolocator = GoogleV3()
        
        self.geocoder = Geocoder()
        
    def resolve_address_google(self, address):
        try:
            address = urllib.quote(address)
            url = "https://maps.googleapis.com/maps/api/geocode/json?address=%s&sensor=false&region=za&key=%s" % (address, configuration["environment"]["google_key"])
            response = urllib2.urlopen(url)
            js = response.read()
            try:
                js = json.loads(js)
            except ValueError:
                logger.exception("Error trying to resolve %s" % address)
                return None

            results = []
            if "results" in js and len(js["results"]) > 0:
                for result in js["results"]:
                    geom = result["geometry"]["location"]
                    results.append({
                        "lat" : geom["lat"],
                        "lng" : geom["lng"],   
                        "formatted_address" : result["formatted_address"]
                    })

                return results
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

    def convert_address(self, address):
        return self.resolve_address_google(address)

    def convert_to_geography(self, sql, latitude, longitude):
        poi = (longitude, latitude)

        self.curs.execute(sql, poi)

        return self.curs.fetchall()

class Ward2006AddressConverter(AddressConverter):
    def convert(self, address):
        now1 = datetime.now()
        results = self.convert_address(address) 
        now2 = datetime.now()
        if not results: return None

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

        wards = []

        for result in results:
            rows = self.convert_to_geography(sql, result["lat"], result["lng"])
            now3 = datetime.now()

            for row in rows:
                wards.append({
                    "address" : address,
                    "coords" : (result["lat"], result["lng"]),
                    "province" : row[0],
                    "municipality" : row[1],
                    "ward" : row[2],
                    "wards_no" : int(row[3]),
                    "now21" : str(now2 - now1),
                    "now32" : str(now3 - now2),
                    "now31" : str(now3 - now1),
                })

        return wards

class PoliceAddressConverter(AddressConverter):
    def convert(self, address):
        now1 = datetime.now()
        results = self.convert_address(address) 
        now2 = datetime.now()
        if not results: return None

        sql = """
            SELECT
                station
            FROM
                police,
                (SELECT ST_MakePoint(%s, %s)::geography AS poi) AS f
            WHERE ST_DWithin(geog, poi, 1);"""

        stations = []
        for result in results:
            rows = self.convert_to_geography(sql, result["lat"], result["lng"])
            now3 = datetime.now()

            for row in rows:
                stations.append({ "station" : row[0] })

        return stations

if __name__ == "__main__":
    db_config = configuration["databases"]["wards_2006"]
    conn = psycopg2.connect(
        database=db_config["database"], user=db_config["db_user"],
        host=db_config["db_host"], password=db_config["db_password"]
    )
    try:
        curs = conn.cursor()
        c = Ward2006AddressConverter(curs)

        while True:
            address = raw_input("Enter in an address: ")
            js = c.convert(address)
            if not js:
                print("Address: %s, could not be found" % address)
                continue

            print(js)
            print("")
    finally:
        conn.close()

converters = {
    "wards_2006" : Ward2006AddressConverter,
    "police" : PoliceAddressConverter,
}
