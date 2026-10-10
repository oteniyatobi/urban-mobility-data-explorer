#Algorithm for finding the busiest locations

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from database.database import engine, Trip

with Session(engine) as session:
    statement = select(Trip.pickup_location_id)
    results = session.execute(statement)
    pickup_locations = results.scalars().all()
print(pickup_locations[:10])