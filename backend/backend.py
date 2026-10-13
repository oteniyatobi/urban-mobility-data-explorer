from flask import Flask, jsonify, request
from sqlalchemy import create_engine
from sqlalchemy import  text, String, Integer, Float, DateTime, Boolean, Column, ForeignKey, insert
from sqlalchemy.orm import DeclarativeBase
from dotenv import load_dotenv
import os
import flask


load_dotenv()
DB_HOST = os.getenv("DB_HOST")
DB_USER = os.getenv("DB_USER")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")
DB_PASSWORD = os.getenv("DB_PASSWORD")

engine = create_engine(f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}")


app = Flask(__name__)
@app.route('/api/fare_rates', methods=['GET'])   
def get_fare_rates():
    with engine.connect() as connection:
        result = connection.execute( text("SELECT * FROM fare_rates"))
        data = [dict(row._mapping) for row in result]
    return flask.jsonify(data)

@app.route('/api/payment_types', methods=['GET'])
def get_payment_types():
    with engine.connect() as connection:
        result = connection.execute( text("SELECT * FROM payment_types"))
        data = [dict(row._mapping) for row in result]
    return flask.jsonify(data)

@app.route('/api/trip_fares', methods=['GET'])
def get_trip_fares():
    limit = request.args.get('limit', default=100, type=int)
    page = request.args.get('page', default=1, type=int)
    
    with engine.connect() as connection:
        result = connection.execute( text("SELECT * FROM trip_fares LIMIT :limit OFFSET :offset"), {"limit": limit, "offset": (page - 1) * limit})
        data = [dict(row._mapping) for row in result]
    return jsonify(data)

@app.route('/api/trip', methods=['GET'])
def get_trip():
    trip_id = request.args.get('trip_id', type=int)
    limit = request.args.get('limit', default=100, type=int)
    page = request.args.get('page', default=1, type=int)
    payment_type = request.args.get('payment_type', type=str)
    date_from = request.args.get('date_from', type=str)
    date_to = request.args.get('date_to', type=str)

    with engine.connect() as connection:
        query = "SELECT * FROM trips WHERE 1=1"
        params = {}

        if trip_id is not None:
            query += " AND trip_id = :trip_id"
            params["trip_id"] = trip_id

        if payment_type is not None:
            query += " AND payment_type = :payment_type_id"
            params["payment_type_id"] = payment_type

        if date_from is not None:
            query += " AND pickup_datetime >= :date_from"
            params["date_from"] = date_from

        if date_to is not None:
            query += " AND pickup_datetime <= :date_to"
            params["date_to"] = date_to

        query += " LIMIT :limit OFFSET :offset"
        params["limit"] = limit
        params["offset"] = (page - 1) * limit

        result = connection.execute(text(query), params)
        data = [dict(row._mapping) for row in result]
        return jsonify(data)
@app.route('/api/vendor', methods=['GET'])
def get_vendor():
    vendor_id = request.args.get('vendor_id', type=int)

    with engine.connect() as connection:
        query = "SELECT * FROM vendors WHERE 1=1"
        params = {}

        if vendor_id is not None:
            query += " AND vendor_id = :vendor_id"
            params["vendor_id"] = vendor_id
        result = connection.execute(text(query), params)
        data = [dict(row._mapping) for row in result]
        return jsonify(data)

@app.route('/api/zone', methods=['GET'])
def get_zone():
    zone_id = request.args.get('zone_id', type=int)

    with engine.connect() as connection:
        query = "SELECT * FROM zones WHERE 1=1"
        params = {}
        if zone_id is not None:
            query += " AND zone_id = :zone_id"
            params["zone_id"] = zone_id
        result = connection.execute(text(query), params)
        data = [dict(row._mapping) for row in result]
        return jsonify(data)
    



if __name__ == "__main__":
    app.run(debug=True, port= 7000 )
