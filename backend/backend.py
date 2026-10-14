from flask import Flask, jsonify, request, render_template
from sqlalchemy import create_engine
from sqlalchemy import  text, String, Integer, Float, DateTime, Boolean, Column, ForeignKey, insert
from sqlalchemy.orm import DeclarativeBase
from dotenv import load_dotenv
import os
import flask
from flask_cors import CORS
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "dsa"))

from algo import find_busiest_vendor # type: ignore



load_dotenv()
DB_HOST = os.getenv("DB_HOST")
DB_USER = os.getenv("DB_USER")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")
DB_PASSWORD = os.getenv("DB_PASSWORD")

engine = create_engine(f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}")


app = Flask(__name__)
CORS(app) # enable CORS for all routes

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
        location_id = request.args.get('location_id', type=int)
        if location_id is not None and location_id < 1:
            return jsonify({"error": "Location ID must be greater than or equal to 1"}), 400
        with engine.connect() as connection:
            query = "SELECT * FROM zones WHERE 1=1"
            params = {}
            if location_id is not None:
                query += " AND location_id = :location_id"
                params["location_id"] = location_id
            result = connection.execute(text(query), params)
            data = [dict(row._mapping) for row in result]
            if not data:
                return jsonify({"error": "No zones found"}), 404
            return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/stats/hourly', methods=['GET'])
def get_hourly_stats():
    try:
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT pickup_hour, is_weekend, COUNT(*) AS trips
                FROM trips
                GROUP BY pickup_hour, is_weekend
                ORDER BY pickup_hour, is_weekend
                """))
            return jsonify([dict(r._mapping) for r in result])
    except Exception as e:
        return jsonify({"error": str(e)}), 500

#custom algo endpoint on the way
_busiest_vendor_cache = None
@app.route('/api/busiest-vendor', methods=['GET'])
def get_busiest_vendor():
    global _busiest_vendor_cache
    #returns cached result if available
    if _busiest_vendor_cache is not None:
        return jsonify(_busiest_vendor_cache)

    
    try:
        with engine.connect() as conn:
            rows = conn.execute(text("SELECT vendor_id FROM trips")).fetchall()
        
        vendor_ids = [r[0] for r in rows if r[0] is not None]
        result = find_busiest_vendor(vendor_ids)
        
        with engine.connect() as conn:
            name_row = conn.execute(
                text("SELECT name FROM vendors WHERE vendor_id = :vid"),
                {"vid": result["busiest_vendor"]},
            ).fetchone()
            result["vendor_name"] = name_row[0] if name_row else "Unknown"
        _busiest_vendor_cache = result
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/stats/payments', methods=['GET'])
def get_payment_stats():
    try:
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT pt.description AS payment_type, COUNT(*) AS trips
                FROM trips t
                JOIN payment_types pt ON t.payment_type_id = pt.payment_type_id
                GROUP BY pt.description
                ORDER BY trips DESC
            """))
            return jsonify([dict(r._mapping) for r in result])
    except Exception as e:
        return jsonify({"error": str(e)}, 500)

@app.route('/api/stats/top-zones', methods=['GET'])
def get_top_zones():
    try:
        k = request.args.get('k', default=10, type=int)
        if k < 1 or k > 100:
            return jsonify({"error": "k must be between 1 and 100"}), 400
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT z.location_id, z.zone_name, z.borough, COUNT(*) AS pickups
                FROM trips t
                JOIN zones z ON t.pickup_location_id = z.location_id
                WHERE z.location_id NOT IN (264, 265)
                GROUP BY z.location_id, z.zone_name, z.borough
                ORDER BY pickups DESC
                LIMIT :k
            """), {"k": k})
            return jsonify([dict(r._mapping) for r in result])
    except Exception as e:
        return jsonify({"error": str(e)}), 500
        


if __name__ == "__main__":
    app.run(debug=True, port= 7000 )
