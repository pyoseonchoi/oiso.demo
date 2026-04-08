from sqlalchemy import String, Integer, Float, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from datetime import datetime
from db.base import Base


class Image(Base):
    __tablename__ = "images"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    original_filename: Mapped[str] = mapped_column(String(255), nullable = False)
    saved_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_url: Mapped[str] = mapped_column(String(500), nullable=False) #MinIO URL
    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )
   
    image_metadata: Mapped["ImageMetaData | None"] = relationship(back_populates="image")
    marker_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("markers.id"), nullable=True)

    #image입장에서는 하나의 marker와 연결되어있다
    marker: Mapped["Marker | None"] = relationship(back_populates="images")

class ImageMetaData(Base):
    __tablename__ = "image_metadata"
    
    id: Mapped[int] = mapped_column(Integer, primary_key = True, autoincrement=True)
    image_id: Mapped[int] = mapped_column(Integer, ForeignKey("images.id"), unique = True)

    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    captured_at: Mapped[str | None] = mapped_column(String(50), nullable=True)

    image: Mapped["Image"] = relationship(back_populates="image_metadata")

