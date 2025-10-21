from sqlalchemy import CheckConstraint, Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from models.database import Base


class Activity(Base):
    __tablename__ = "activities"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)
    parent_id = Column(Integer, ForeignKey("activities.id"), nullable=True)
    level = Column(Integer, nullable=False, default=1)

    parent = relationship("Activity", remote_side=[id], back_populates="children")
    children = relationship(
        "Activity", back_populates="parent", cascade="all, delete-orphan"
    )

    organizations = relationship(
        "Organization", secondary="organization_activities", back_populates="activities"
    )

    __table_args__ = (
        CheckConstraint("level >= 1 AND level <= 3", name="check_activity_level"),
    )

    def __repr__(self):
        return f"<Activity(id={self.id}, name='{self.name}', level={self.level})>"
