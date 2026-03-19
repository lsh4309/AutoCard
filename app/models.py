from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, Text, Float, func
)
from app.db import Base


class CardUser(Base):
    """카드 사용자 마스터"""
    __tablename__ = "card_users"

    id = Column(Integer, primary_key=True, index=True)
    bank_type = Column(String(10), nullable=False)          # KB / IBK
    card_last4 = Column(String(4), nullable=False, index=True)
    card_number_full = Column(String(50), nullable=True)
    user_name = Column(String(50), nullable=False)
    user_email = Column(String(100), nullable=True)
    active_yn = Column(Boolean, default=True)
    note = Column(Text, nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


class ProjectMaster(Base):
    """프로젝트 마스터"""
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False, unique=True)
    active_yn = Column(Boolean, default=True)
    sort_order = Column(Integer, default=0)
    created_at = Column(DateTime, default=func.now())


class SolutionMaster(Base):
    """솔루션 마스터"""
    __tablename__ = "solutions"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False, unique=True)
    active_yn = Column(Boolean, default=True)
    sort_order = Column(Integer, default=0)
    created_at = Column(DateTime, default=func.now())


class AccountSubjectMaster(Base):
    """계정과목/지출내역 마스터"""
    __tablename__ = "account_subjects"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False, unique=True)
    active_yn = Column(Boolean, default=True)
    sort_order = Column(Integer, default=0)
    created_at = Column(DateTime, default=func.now())


class Transaction(Base):
    """거래 데이터 (파싱 후 정규화된 내부 저장용)"""
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    source_bank = Column(String(10), nullable=False)       # KB / IBK
    use_year_month = Column(String(6), nullable=True)      # YYYYMM
    approval_date = Column(String(10), nullable=True)      # YYYY-MM-DD
    approval_time = Column(String(8), nullable=True)       # HH:MM:SS
    approval_datetime = Column(String(20), nullable=True)

    card_number_raw = Column(String(50), nullable=True)
    card_last4 = Column(String(4), nullable=True, index=True)
    card_owner_name = Column(String(50), nullable=True)
    card_owner_email = Column(String(100), nullable=True)

    merchant_name = Column(String(200), nullable=True)
    merchant_category = Column(String(100), nullable=True)
    approval_amount = Column(Float, nullable=True)

    # 관리자 입력 필드
    project_name = Column(String(200), nullable=True)
    solution_name = Column(String(200), nullable=True)
    account_subject = Column(String(200), nullable=True)
    flex_pre_approved = Column(String(1), nullable=True)   # O / X
    attendees = Column(Text, nullable=True)
    purchase_detail = Column(Text, nullable=True)
    remarks = Column(Text, nullable=True)

    # 상태 필드
    mapping_status = Column(String(20), default="unmapped")   # mapped / unmapped
    validation_status = Column(String(20), default="pending") # ok / warning / error
    validation_message = Column(Text, nullable=True)
    source_row_no = Column(Integer, nullable=True)

    upload_batch_id = Column(String(50), nullable=True, index=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
