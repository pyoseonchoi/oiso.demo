from datetime import datetime
from typing import List, Optional

from sqlalchemy import DateTime, Float, Integer, String, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.base import Base


# ─── Chat History 도메인 ─────────────────────────────────────────

class UserMessage(Base):
    """사용자 메시지 테이블"""
    __tablename__ = "user_message"

    unique_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    time_stamp: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    chat_order: Mapped[int] = mapped_column(Integer, nullable=False)

    # 선택적 이미지 첨부 (사용자가 채팅에 사진을 보낸 경우)
    picture_id: Mapped[Optional[str]] = mapped_column(
        ForeignKey("picture.unique_id"),
        nullable=True,
    )

    # 관계
    picture: Mapped[Optional["Picture"]] = relationship(
        "Picture",
        foreign_keys=[picture_id],
    )

    # Chats 역참조
    chat: Mapped[Optional["Chats"]] = relationship(
        back_populates="user_msg",
        uselist=False,
    )


class AIMessage(Base):
    """AI 응답 메시지 테이블"""
    __tablename__ = "ai_message"

    unique_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    time_stamp: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    chat_order: Mapped[int] = mapped_column(Integer, nullable=False)

    # Chats 역참조
    chat: Mapped[Optional["Chats"]] = relationship(
        back_populates="ai_msg",
        uselist=False,
    )


class Chats(Base):
    """채팅 세션(턴) 묶음 테이블: UserMessage ↔ AIMessage 한 쌍을 묶는다"""
    __tablename__ = "chats"

    unique_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    uuid: Mapped[str] = mapped_column(String(255), nullable=False, index=True)

    user_msg_id: Mapped[Optional[str]] = mapped_column(
        ForeignKey("user_message.unique_id"),
        nullable=True,
    )
    ai_msg_id: Mapped[Optional[str]] = mapped_column(
        ForeignKey("ai_message.unique_id"),
        nullable=True,
    )

    # 관계
    user_msg: Mapped[Optional["UserMessage"]] = relationship(
        back_populates="chat",
        foreign_keys=[user_msg_id],
    )
    ai_msg: Mapped[Optional["AIMessage"]] = relationship(
        back_populates="chat",
        foreign_keys=[ai_msg_id],
    )


# ─── OCR Data 도메인 ─────────────────────────────────────────────

class MenuList(Base):
    """OCR로 추출된 개별 메뉴 항목"""
    __tablename__ = "menu_list"

    unique_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    menu_name: Mapped[str] = mapped_column(String(255), nullable=False)
    menu_price: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    upload_time_stamp: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True,
    )

    # OCRMenuArray 역참조
    ocr_entries: Mapped[List["OCRMenuArray"]] = relationship(
        back_populates="menu",
    )


class OCRData(Base):
    """OCR 분석 1회를 나타내는 테이블"""
    __tablename__ = "ocr_data"

    ocr_no: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    uuid: Mapped[str] = mapped_column(String(255), nullable=False, index=True)

    # 분석 대상 사진
    pic_no: Mapped[str] = mapped_column(
        ForeignKey("picture.unique_id"),
        nullable=False,
    )

    # 관계
    picture: Mapped["Picture"] = relationship(
        "Picture",
        foreign_keys=[pic_no],
    )
    menu_entries: Mapped[List["OCRMenuArray"]] = relationship(
        back_populates="ocr_data",
    )


class OCRMenuArray(Base):
    """OCRData ↔ MenuList 다대다 연결 테이블"""
    __tablename__ = "ocr_menu_array"

    data_no: Mapped[int] = mapped_column(
        ForeignKey("ocr_data.ocr_no"),
        primary_key=True,
    )
    menu_no: Mapped[str] = mapped_column(
        ForeignKey("menu_list.unique_id"),
        primary_key=True,
    )

    # 관계
    ocr_data: Mapped["OCRData"] = relationship(back_populates="menu_entries")
    menu: Mapped["MenuList"] = relationship(back_populates="ocr_entries")


# Picture를 forward reference로 사용하기 위한 import
# (순환 참조 방지 — 런타임에서 relationship이 문자열 참조로 해결됨)
from models.mx_model import Picture  # noqa: E402, F401
