from geoalchemy2 import Geography
from sqlalchemy import Column, Float, Integer, String
from sqlalchemy.orm import relationship

from models.database import Base


class Building(Base):
    __tablename__ = "buildings"

    id = Column(Integer, primary_key=True, index=True)
    address = Column(String, nullable=False, index=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    location = Column(
        Geography(geometry_type="POINT", srid=4326, spatial_index=True), nullable=True
    )

    organizations = relationship("Organization", back_populates="building")

    def __repr__(self):
        return f"<Building(id={self.id}, address='{self.address}')>"
