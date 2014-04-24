import urllib2, urllib
import csv
import logging
import json
from datetime import datetime
import re

from geopy.geocoders import GoogleV3
import nominatim
from omgeo import Geocoder
from config import configuration, logger

def encode(s, encoding="utf8"):
    if type(s) == unicode:
        return s.encode(encoding)
    return s

def load_mps():
    data = {}
    reader = csv.reader(open("mp_population.csv"))
    mp_headers = reader.next()
    for row in reader:
        datum = dict(zip(mp_headers, row))
        data[datum["MP_NAME"].lower()] = datum 
    return data

main_places = load_mps()

re_coord = "\s*[+-]?\d+(\.\d+)?\s*"
re_is_latlng = re.compile(r"^{coord},{coord}$".format(coord=re_coord))

class AddressConverter(object):
    def __init__(self, curs):
        self.curs = curs
        self.geolocator = GoogleV3()
        self.nominatim = nominatim.Geocoder()
        
        self.geocoder = Geocoder()
        self.re_numbers = re.compile("^\d+$")

    def reject_all_numbers(self, address):
        if self.re_numbers.search(address):
            logger.info("Rejected by reject_all_numbers")
            return True
        return False

    def reject_short_words(self, address, length=4):
        if len(address) <= length:
            logger.info("Rejected by reject_short_words")
            return True
        return False

    def reject_large_main_places(self, address, threshold=15000):
        if address in main_places:
            population = main_places[address]["Population"]
            if int(population) >= threshold:
                return True
        return False

    def reject_resolution_to_main_place(self, address, threshold=15000):
        parts = address.split(",")
        first = parts[0].strip().lower()
        return self.reject_large_main_places(first, threshold)

    def reject_partial_match(self, result):
        if "partial_match" in result and result["partial_match"]:
            return True
        return False
        
    def resolve_address_google(self, address, **kwargs):
        try:
            encoded_address = encode(address)
            address = urllib.quote(encoded_address)

            url = "https://maps.googleapis.com/maps/api/geocode/json?address=%s&sensor=false&region=za&key=%s" % (address, configuration["environment"]["google_key"])
            response = urllib2.urlopen(url)
            js = response.read()
            try:
                js = json.loads(js)
            except ValueError:
                logger.exception("Error trying to resolve %s" % address)
                return None

            results = []
            if "status" in js and js["status"] != "OK": 
                logger.warn("Error trying to resolve %s - %s" % (address, js.get("error_message", "Generic Error")))
                return None

            if "results" in js and len(js["results"]) > 0:
                for result in js["results"]:

                    res = self.reject_partial_match(result)
                    if res: continue

                    if "reject_resolution_to_main_place" in kwargs:
                        try:
                            res = self.reject_resolution_to_main_place(result["formatted_address"], int(kwargs["reject_resolution_to_main_place"][0]))
                        except (ValueError, TypeError):
                            res = self.resolution_to_main_place(result["formatted_address"])
                        if res: continue

                    geom = result["geometry"]["location"]
                    results.append({
                        "lat" : geom["lat"],
                        "lng" : geom["lng"],   
                        "formatted_address" : result["formatted_address"],
                        "source" : "Google Geocoding API",
                    })

                if len(results) == 0: return None
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

    def resolve_address_nominatim(self, address, **kwargs):
        encoded_address = encode(address)
        results = self.nominatim.geocode(encoded_address)
        return [
            {
                "lat" : r["lat"],
                "lng" : r["lon"],   
                "formatted_address" : r["display_name"],
                "source" : "Nominatim",
            }
            for r in results
        ]

    def convert_address(self, address, **kwargs):
        address = address.strip()
        if address == "": return None

        if re_is_latlng.match(address):
            return self.resolve_coords(address)

        if "reject_numbers" in kwargs and self.reject_all_numbers(address): return None
        if "reject_short_words" in kwargs:
            try:
                val = self.reject_short_words(address, int(kwargs["reject_short_words"][0]))
            except (TypeError, ValueError):
                val = self.reject_short_words(address)
            if val: return None

        if "reject_large_main_places" in kwargs:
            try:
                val = self.reject_large_main_places(address, int(kwargs["reject_large_main_places"][0]))
            except (TypeError, ValueError):
                val = self.reject_large_main_places(address)
            if val: return None

        if not "south africa" in address.lower():
            address = address + ", South Africa"

        if "enable_nominatim" in kwargs:
            results = self.resolve_address_nominatim(address, **kwargs)

            if len(results) > 0:
                return results

        return self.resolve_address_google(address, **kwargs)

    def convert_to_geography(self, sql, latitude, longitude):
        poi = (longitude, latitude)

        self.curs.execute(sql, poi)

        return self.curs.fetchall()

    def resolve_coords(self, coords):
        try:
            lat, lng = [float(s) for s in coords.split(',', 1)]
            return [{
                "lat" : lat,
                "lng" : lng,
                "formatted_address" : "%s, %s" % (lat, lng), 
                "source" : "Direct",
            }]
        except ValueError:
            return None

class WardAddressConverter(AddressConverter):

    def convert(self, address, **kwargs):
        now1 = datetime.now()
        results = self.convert_address(address, **kwargs) 
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
                    "source" : result["source"],
                    "address" : result["formatted_address"],
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
    def convert(self, address, **kwargs):
        now1 = datetime.now()
        results = self.convert_address(address, **kwargs) 
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
                stations.append({
                    "station" : row[0],
                    "address" : result["formatted_address"],
                    "coords" : (result["lat"], result["lng"]),
                })

        return stations

class VD2014Converter(AddressConverter):
    def convert(self, address, **kwargs):
        now1 = datetime.now()
        results = self.convert_address(address, **kwargs) 
        now2 = datetime.now()
        if not results: return None

        sql = """
            SELECT
                vd.vd_id, vd.ward_id, vd.munic_id, vd.province,
                vs.province, vs.municipali, vs.ward_id,
                vs.sstreetvil, vs.ssuburbadm, vs.stowntriba, vs.svs_type,
                vs.latitude, vs.longitude, vs.svs_name
            FROM
                vd_2014 vd
                INNER JOIN vs_2014 vs on vd.vd_id = vs.vd_id,
                (SELECT ST_MakePoint(%s, %s)::geography AS poi) AS f
            WHERE ST_DWithin(vd.geog, poi, 1);"""


        vds = []
        for result in results:
            rows = self.convert_to_geography(sql, result["lat"], result["lng"])
            now3 = datetime.now()

            for row in rows:
                vds.append({
                    "source" : result["source"],
                    "voting_district" : str(row[0]),
                    "ward" : str(row[1]),
                    "municipality" : str(row[2]),
                    "province" : str(row[3]),
                    "address" : result["formatted_address"],
                    "coords" : (result["lat"], result["lng"]),
                    "voting_station" : str(row[13]).title(),
                })

        return vds

class CensusConverter(AddressConverter):
    def convert(self, address, **kwargs):
        now1 = datetime.now()
        results = self.convert_address(address, **kwargs) 
        now2 = datetime.now()
        if not results: return None

        sql = """
            SELECT
                c.sp_code, c.sp_name, c.mp_code, c.mp_name,
                c.mn_code, c.mn_name, c.dc_name, c.pr_code, c.pr_name
            FROM
                sp_sa_2011 c, 
                (SELECT ST_MakePoint(%s, %s)::geography AS poi) AS f
            WHERE ST_DWithin(c.geog, poi, 1);"""


        sps = []
        for result in results:
            rows = self.convert_to_geography(sql, result["lat"], result["lng"])
            now3 = datetime.now()

            for row in rows:
                sps.append({
                    "source" : result["source"],
                    "sp_code" : int(row[0]),
                    "sp_name" : row[1],
                    "mp_code" : int(row[2]),
                    "mp_name" : row[3],
                    "mn_code" : int(row[4]),
                    "mn_name" : row[5],
                    "dc_name" : row[6],
                    "pr_code" : int(row[7]),
                    "pr_name" : row[8],
                    "address" : result["formatted_address"],
                    "coords" : (result["lat"], result["lng"]),
                })

        return sps

converters = {
    "wards_2006" : WardAddressConverter,
    "wards_2011" : WardAddressConverter,
    "police" : PoliceAddressConverter,
    "vd_2014" : VD2014Converter,
    "census_2011" : CensusConverter,
}
