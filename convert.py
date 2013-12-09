from __future__ import print_function
from geopy.geocoders import GoogleV3
import config
import psycopg2

class AddressConverter(object):
    def __init__(self, curs):
        self.curs = curs
        self.geolocator = GoogleV3()
        
    def convert(self, address):
        result = self.geolocator.geocode(address, region="za")
        if not result: return None

        address, (latitude, longitude) = result
        poi = (longitude, latitude)
        sql ="""
            SELECT
                province,
                municname,
                ward_id,
                ward_no
            FROM
                {database} as wards,
                (SELECT ST_MakePoint(%s, %s)::geography AS poi) AS f
            WHERE ST_DWithin(geom, poi, 1);""".format(database=config.database)

        self.curs.execute(sql, poi)

        for row in self.curs.fetchall():
            return {
                "address" : address,
                "coords" : poi,
                "province" : row[0],
                "municipality" : row[1],
                "ward" : row[2],
                "ward_no" : int(row[3]),
            }

if __name__ == "__main__":
    conn = psycopg2.connect(
        database=config.database, user="wards",
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
            print("Ward No: %s" % js["ward_no"])
            print("")
    finally:
        conn.close()
