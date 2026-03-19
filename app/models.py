from sqlalchemy import Column, Integer, String, Text, Float
from app.db import Base


class Transaction(Base):
    """거래 데이터 - 거래내역 화면 표시 + 엑셀 내보내기용 최소 컬럼"""
    __tablename__ = "CARD_TRANSACTIONS"

    id = Column(Integer, primary_key=True, index=True)
    source_bank = Column(String(10), nullable=False)       # KB / IBK
    use_year_month = Column(String(6), nullable=True)     # YYYYMM
    approval_date = Column(String(10), nullable=True)      # YYYY-MM-DD
    approval_time = Column(String(8), nullable=True)      # HH:MM:SS
    approval_datetime = Column(String(20), nullable=True)  # 정렬용

    card_number_raw = Column(String(50), nullable=True)
    card_last4 = Column(String(4), nullable=True, index=True)
    card_owner_name = Column(String(50), nullable=True)
    merchant_name = Column(String(200), nullable=True)
    approval_amount = Column(Float, nullable=True)

    # 엑셀 내보내기용 (관리자 입력)
    project_name = Column(String(200), nullable=True)
    solution_name = Column(String(200), nullable=True)
    account_subject = Column(String(200), nullable=True)
    flex_pre_approved = Column(String(1), nullable=True)   # O / X
    attendees = Column(Text, nullable=True)
    purchase_detail = Column(Text, nullable=True)
    remarks = Column(Text, nullable=True)

    mapping_status = Column(String(20), default="unmapped")
    upload_batch_id = Column(String(50), nullable=True, index=True)
