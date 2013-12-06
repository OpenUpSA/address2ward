import json
import psycopg2
from flask import Flask
from flask import request
from flask import g
import config
from convert import AddressConverter

app = Flask(__name__)

def get_connection():
    return psycopg2.connect(
        database="wards", user="wards",
        host="localhost", password="wards"
    )

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = get_connection()
    return db

def get_converter():
    converter = getattr(g, '_converter', None)
    if converter is None:
        converter = g._converter = AddressConverter(get_db().cursor())
    return converter

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

@app.route("/", methods=["GET"])
def a2w():
    address = request.args.get("address")
    if address:
        js = get_converter().convert(address)
        js = js or {"error" : "address not found"}
        return json.dumps(js, indent=4)
    else:
        return """
<html>
<head><title>Address converter</title></head>
<body>
Use this API to look-up street addresses and find their wards
as an example:

For example, try:  <a href="/?address=12 Thicket St, Cape Town">12 Thicket street, Cape Town</a>
</body>
</html>
"""


if __name__ == "__main__":
    conn = get_connection()
    try:
        converter = AddressConverter(conn.cursor())
        app.run(debug=False)
    finally:
        conn.close()
        
