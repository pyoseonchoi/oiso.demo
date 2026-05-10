from datetime import datetime
from typing import List, Optional

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.base import Base


# ─── Tag 도메인 ──────────────────────────────────────────────────

class Tag(Base):
    __tablename__ = "tags"

    tag_string: Mapped[str] = mapped_column(String(100), primary_key=True)

    # 태그 하나는 여러 사진에 붙을 수 있다. 중간연결 테이블 - per_pic_tags
    pictures: Mapped[List["Picture"]] = relationship(
        secondary="per_pic_tags",
        back_populates="tags",
    )

    clusters: Mapped[List["ClusterArray"]] = relationship(
        secondary="tag_list",
        back_populates="tags",
    )


# ─── Picture 도메인 ──────────────────────────────────────────────

class Image(Base):
    """S3 저장 정보를 담는 테이블"""
    __tablename__ = "image"

    unique_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    s3_bucket: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    s3_key: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    s3_version: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # 1:1 역참조
    picture: Mapped[Optional["Picture"]] = relationship(
        back_populates="image",
        uselist=False,
    )


class Metadata(Base):
    __tablename__ = "metadata"

    unique_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    longitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    latitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    time_stamp: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # 1:1 역참조
    picture: Mapped[Optional["Picture"]] = relationship(
        back_populates="pic_metadata",
        uselist=False,
    )


class Picture(Base):
    __tablename__ = "picture"

    unique_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    created_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    image_id: Mapped[Optional[str]] = mapped_column(
        ForeignKey("image.unique_id"),
        nullable=True,
    )
    metadata_id: Mapped[Optional[str]] = mapped_column(
        ForeignKey("metadata.unique_id"),
        nullable=True,
    )

    # 관계
    image: Mapped[Optional["Image"]] = relationship(back_populates="picture")
    pic_metadata: Mapped[Optional["Metadata"]] = relationship(back_populates="picture")

    # 사진이 어떤 클러스터에 속하는지
    clusters: Mapped[List["ClusterArray"]] = relationship(
        secondary="picture_list",
        back_populates="pictures",
    )
    # 사진에 붙은 태그목록
    tags: Mapped[List["Tag"]] = relationship(
        secondary="per_pic_tags",
        back_populates="pictures",
    )


# ─── Cluster 도메인 ──────────────────────────────────────────────

class ClusterArray(Base):
    __tablename__ = "cluster_array"

    cluster_no: Mapped[int] = mapped_column(Integer, primary_key=True)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)
    latitude: Mapped[float] = mapped_column(Float, nullable=False)

    # 클러스터 하나에는 여러 사진이 붙을 수 있다.
    pictures: Mapped[List["Picture"]] = relationship(
        secondary="picture_list",
        back_populates="clusters",
    )

    tags: Mapped[List["Tag"]] = relationship(
        secondary="tag_list",
        back_populates="clusters",
    )


# ─── 연결(Association) 테이블 ────────────────────────────────────

class PictureList(Base):
    """ClusterArray ↔ Picture 다대다 연결"""
    __tablename__ = "picture_list"

    cluster_no: Mapped[int] = mapped_column(
        ForeignKey("cluster_array.cluster_no"),
        primary_key=True,
    )
    pic_no: Mapped[str] = mapped_column(
        ForeignKey("picture.unique_id"),
        primary_key=True,
    )


class PerPicTags(Base):
    """Picture ↔ Tag 다대다 연결"""
    __tablename__ = "per_pic_tags"

    unique_id: Mapped[str] = mapped_column(
        ForeignKey("picture.unique_id"),
        primary_key=True,
    )
    tag: Mapped[str] = mapped_column(
        ForeignKey("tags.tag_string"),
        primary_key=True,
    )


class TagList(Base):
    """ClusterArray ↔ Tag 다대다 연결"""
    __tablename__ = "tag_list"

    cluster_no: Mapped[int] = mapped_column(
        ForeignKey("cluster_array.cluster_no"),
        primary_key=True,
    )
    tag: Mapped[str] = mapped_column(
        ForeignKey("tags.tag_string"),
        primary_key=True,
    )
