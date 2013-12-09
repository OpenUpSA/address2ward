import json
import psycopg2
from flask import Flask
from flask import Response
from flask import request
from flask import render_template
from flask import g
import config
from convert import AddressConverter

app = Flask(__name__)

connections = {}

def get_connection(database):
    if not database in connections:
        connections[database] = psycopg2.connect(
        database=config.database, user="wards",
        host="localhost", password="wards"
    )
    return connections[database]

def close_connections():
    for key, val in connections.items():
        val.close()

def get_db(database):
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = get_connection(database)
    return db

def get_converter(database):
    converter = getattr(g, '_converter', None)
    if converter is None:
        converter = g._converter = AddressConverter(get_db(database).cursor())
    return converter

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

@app.route("/", methods=["GET"])
def a2w():
    address = request.args.get("address")
    database = request.args.get("address", config.database)
    
    if address:
        js = get_converter(database).convert(address)
        js = js or {"error" : "address not found"}
        return Response(
            response=json.dumps(js, indent=4), status=200, mimetype="application/json"
        )
    else:
        return render_template("search.html")

if __name__ == "__main__":
    conn = get_connection("wards_2006")
    try:
        converter = AddressConverter(conn.cursor())
        app.run(debug=True)
    finally:
        close_connections()
        
