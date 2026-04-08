from sqlalchemy import String, Integer, Float, DateTime, ForeignKey, Table, Column
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from datetime import datetime
from db.base import Base

marker_tag_association = Table(
    "marker_tag_association",
    Base.metadata,
    Column("marker_id", Integer, ForeignKey("markers.id"), primary_key=True),
    Column("tag_id", Integer, ForeignKey("tags.id"), primary_key=True),
)

class Tag(Base):
    __tablename__ = "tags"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    
    markers = relationship("Marker", secondary=marker_tag_association, back_populates="tags")

class Marker(Base):
    __tablename__ = "markers"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )
    
    # marker입장에서 여러 Image와 연결되어있다~ 의미
    images = relationship("Image", back_populates="marker")
    tags = relationship("Tag", secondary=marker_tag_association, back_populates="markers")