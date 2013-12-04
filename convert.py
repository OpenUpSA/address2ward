from __future__ import print_function
from geopy.geocoders import GoogleV3
import config
import psycopg2

geolocator = GoogleV3()
conn = psycopg2.connect(
    database=config.database, user=config.user, 
    host=config.host, password=config.password
)
curs = conn.cursor()

try:
    while True:
        address = raw_input("Enter in an address: ")
        address, (latitude, longitude) = geolocator.geocode(address)

        poi = (longitude, latitude)

        curs.execute("""
            SELECT wards.province, wards.municname, wards.ward_id 
            FROM wards, (SELECT ST_MakePoint(%s, %s)::geography AS poi) AS f
            WHERE ST_DWithin(geom, poi, 1);""", poi
        )

        for row in curs.fetchall():
            print("Full Address: %s" % address)
            print("Coords: %f, %f" % (latitude, longitude))
            print("Province: %s" % row[0])
            print("Municipality: %s" % row[1])
            print("Ward: %s" % row[2])
            print("")
finally:
    conn.close()
