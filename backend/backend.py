from flask import Flask, jsonify
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



if __name__ == "__main__":
    app.run(debug=True, port= 7000 )
