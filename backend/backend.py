from flask import Flask, jsonify, request, render_template
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

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/api/fare_rates', methods=['GET'])   
def get_fare_rates():
    try:
        with engine.connect() as connection:
            result = connection.execute( text("SELECT * FROM fare_rates"))
            data = [dict(row._mapping) for row in result]
            if not data:
                return jsonify({"error": "No fare rates found"}), 404
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/payment_types', methods=['GET'])
def get_payment_types():
    try:
        with engine.connect() as connection:
            result = connection.execute( text("SELECT * FROM payment_types"))
            data = [dict(row._mapping) for row in result]
            if not data:
                return jsonify({"message": "No payment types found"}), 404
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/trip_fares', methods=['GET'])
def get_trip_fares():
    try:
        limit = request.args.get('limit', default=100, type=int)
        page = request.args.get('page', default=1, type=int)
        if page < 1:
            return jsonify({"error": "Page number must be greater than or equal to 1"}), 400
        if limit < 1:
            return jsonify({"error": "Limit must be greater than or equal to 1"}), 400
        with engine.connect() as connection:
            result = connection.execute( text("SELECT * FROM trip_fares LIMIT :limit OFFSET :offset"), {"limit": limit, "offset": (page - 1) * limit})
            data = [dict(row._mapping) for row in result]
            if not data:
                return jsonify({"error": "No trip fares found"}), 404
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
@app.route('/api/trip', methods=['GET'])
def get_trip():
    try:
        
        trip_id = request.args.get('trip_id', type=int)
        limit = request.args.get('limit', default=100, type=int)
        page = request.args.get('page', default=1, type=int)
        payment_type = request.args.get('payment_type', type=str)
        date_from = request.args.get('date_from', type=str)
        date_to = request.args.get('date_to', type=str)
        pickup_location_id = request.args.get('pickup_location_id', type=int)
        if page < 1:
            return jsonify({"error": "Page number must be greater than or equal to 1"}), 400
        if limit < 1:
            return jsonify({"error": "Limit must be greater than or equal to 1"}), 400
        if trip_id is not None and trip_id < 1:
            return jsonify({"error": "Trip ID must be greater than or equal to 1"}), 400
        if pickup_location_id is not None and pickup_location_id < 1:
            return jsonify({"error": "Pickup Location ID must be greater than or equal to 1"}), 400

        with engine.connect() as connection:
            query = "SELECT * FROM trips WHERE 1=1"
            params = {}

            if trip_id is not None:
                query += " AND trip_id = :trip_id"
                params["trip_id"] = trip_id

            if payment_type is not None:
                query += " AND payment_type_id = :payment_type_id"
                params["payment_type_id"] = payment_type

            if date_from is not None:
                query += " AND pickup_datetime >= :date_from"
                params["date_from"] = date_from

            if date_to is not None:
                query += " AND pickup_datetime <= :date_to"
                params["date_to"] = date_to
            if pickup_location_id is not None:
                query += " AND pickup_location_id = :pickup_location_id"
                params["pickup_location_id"] = pickup_location_id

            query += " LIMIT :limit OFFSET :offset"
            params["limit"] = limit
            params["offset"] = (page - 1) * limit

            result = connection.execute(text(query), params)
            data = [dict(row._mapping) for row in result]
            if not data:
                return jsonify({"error": "No trips found"}), 404
            return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/vendor', methods=['GET'])
def get_vendor():
    try:
        vendor_id = request.args.get('vendor_id', type=int)
        if vendor_id is not None and vendor_id < 1:
            return jsonify({"error": "Vendor ID must be greater than or equal to 1"}), 400

        with engine.connect() as connection:
            query = "SELECT * FROM vendors WHERE 1=1"
            params = {}

            if vendor_id is not None:
                query += " AND vendor_id = :vendor_id"
                params["vendor_id"] = vendor_id
            result = connection.execute(text(query), params)
            data = [dict(row._mapping) for row in result]
            if not data:
                return jsonify({"error": "No vendors found"}), 404
            return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
@app.route('/api/zone', methods=['GET'])
def get_zone():
    try:
        zone_id = request.args.get('zone_id', type=int)
        if zone_id is not None and zone_id < 1:
            return jsonify({"error": "Zone ID must be greater than or equal to 1"}), 400
        with engine.connect() as connection:
            query = "SELECT * FROM zones WHERE 1=1"
            params = {}
            if zone_id is not None:
                query += " AND zone_id = :zone_id"
                params["zone_id"] = zone_id
            result = connection.execute(text(query), params)
            data = [dict(row._mapping) for row in result]
            if not data:
                return jsonify({"error": "No zones found"}), 404
            return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500



if __name__ == "__main__":
    app.run(debug=True, port= 7000 )
