"""거래 데이터 API"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db import get_db
from app.services.transaction_service import (
    get_transactions, remap_transactions, delete_all_transactions,
)

router = APIRouter(prefix="/api/transactions", tags=["transactions"])


@router.get("")
def list_transactions(
    bank: str = "",
    user_name: str = "",
    card_number: str = "",
    year_month: str = "",
    mapping_status: str = "",
    page: int = 1,
    page_size: int = 50,
    db: Session = Depends(get_db),
):
    items, total = get_transactions(
        db,
        bank=bank or None,
        user_name=user_name or None,
        card_number=card_number or None,
        year_month=year_month or None,
        mapping_status=mapping_status or None,
        page=page,
        page_size=page_size,
    )
    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": [_tx_to_dict(tx) for tx in items],
    }


@router.post("/remap")
def remap(db: Session = Depends(get_db)):
    """카드 사용자 마스터 기준으로 미매핑 거래 재매핑"""
    count = remap_transactions(db)
    return {"status": "ok", "remapped": count}


@router.delete("")
def delete_all(db: Session = Depends(get_db)):
    """거래내역 전체 삭제"""
    count = delete_all_transactions(db)
    return {"status": "ok", "deleted": count}


def _tx_to_dict(tx) -> dict:
    return {
        "id": tx.id,
        "source_bank": tx.source_bank,
        "use_year_month": tx.use_year_month,
        "approval_date": tx.approval_date,
        "approval_time": tx.approval_time,
        "card_number_raw": tx.card_number_raw,
        "card_last4": tx.card_last4,
        "card_owner_name": tx.card_owner_name,
        "merchant_name": tx.merchant_name,
        "approval_amount": tx.approval_amount,
        "project_name": tx.project_name,
        "solution_name": tx.solution_name,
        "account_subject": tx.account_subject,
        "flex_pre_approved": tx.flex_pre_approved,
        "attendees": tx.attendees,
        "purchase_detail": tx.purchase_detail,
        "remarks": tx.remarks,
        "mapping_status": tx.mapping_status,
    }
