from sqlalchemy import Column, ForeignKey, Integer, String, Table
from sqlalchemy.orm import relationship

from models.database import Base

organization_activities = Table(
    "organization_activities",
    Base.metadata,
    Column(
        "organization_id",
        Integer,
        ForeignKey("organizations.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "activity_id",
        Integer,
        ForeignKey("activities.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)


class Organization(Base):
    __tablename__ = "organizations"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)
    building_id = Column(
        Integer, ForeignKey("buildings.id", ondelete="CASCADE"), nullable=False
    )

    building = relationship("Building", back_populates="organizations")
    phones = relationship(
        "Phone", back_populates="organization", cascade="all, delete-orphan"
    )
    activities = relationship(
        "Activity", secondary=organization_activities, back_populates="organizations"
    )

    def __repr__(self):
        return f"<Organization(id={self.id}, name='{self.name}')>"
