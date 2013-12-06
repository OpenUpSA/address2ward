from __future__ import print_function
from geopy.geocoders import GoogleV3
import config
import psycopg2

class AddressConverter(object):
    def __init__(self, curs):
        self.curs = curs
        self.geolocator = GoogleV3()
        
    def convert(self, address):
        result = self.geolocator.geocode(address)
        if not result: return None

        address, (latitude, longitude) = result
        poi = (longitude, latitude)
        self.curs.execute("""
            SELECT wards.province, wards.municname, wards.ward_id 
            FROM wards, (SELECT ST_MakePoint(%s, %s)::geography AS poi) AS f
            WHERE ST_DWithin(geom, poi, 1);""", poi
        )

        for row in self.curs.fetchall():
            return {
                "address" : address,
                "coords" : poi,
                "province" : row[0],
                "municipality" : row[1],
                "ward" : row[2],
            }

if __name__ == "__main__":
    conn = psycopg2.connect(
        database="wards", user="wards",
        host="localhost", password="wards"
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
            print("")
    finally:
        conn.close()
