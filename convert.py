from __future__ import print_function
import sys
import config
from config import configuration
import psycopg2
import logging
from converters import converters

logger = logging.getLogger(config.LOGGER_NAME)

if __name__ == "__main__":
    db = sys.argv[1]
    db_config = configuration["databases"][db]
    conn = psycopg2.connect(
        database=db_config["database"], user=db_config["db_user"],
        host=db_config["db_host"], password=db_config["db_password"]
    )
    try:
        curs = conn.cursor()
        c = converters[db](curs)

        while True:
            address = raw_input("Enter in an address: ")
            js = c.convert(address, remove_numbers=1)
            if not js:
                print("Address: %s, could not be found" % address)
                continue

            print(js)
            print("")
    finally:
        conn.close()

