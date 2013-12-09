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

def get_connection():
    return psycopg2.connect(
        database=config.database, user="wards",
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
    database = request.args.get("database", None)
    
    if address:
        js = get_converter().convert(address, database)
        js = js or {"error" : "address not found"}
        return Response(
            response=json.dumps(js, indent=4), status=200, mimetype="application/json"
        )
    else:
        return render_template("search.html")

if __name__ == "__main__":
    conn = get_connection()
    try:
        converter = AddressConverter(conn.cursor())
        app.run(debug=True)
    finally:
        conn.close()
        
