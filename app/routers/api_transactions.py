"""거래 데이터 API"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.db import get_db
from app.services.transaction_service import (
    get_transactions, update_transaction, bulk_update_transactions, remap_transactions,
    delete_all_transactions,
)

router = APIRouter(prefix="/api/transactions", tags=["transactions"])


class TransactionUpdate(BaseModel):
    project_name: str | None = None
    solution_name: str | None = None
    account_subject: str | None = None
    flex_pre_approved: str | None = None
    attendees: str | None = None
    purchase_detail: str | None = None
    remarks: str | None = None


class BulkUpdateRequest(BaseModel):
    ids: list[int]
    data: TransactionUpdate


@router.get("")
def list_transactions(
    bank: str = "",
    user_name: str = "",
    card_last4: str = "",
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
        card_last4=card_last4 or None,
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


@router.patch("/{tx_id}")
def patch_transaction(
    tx_id: int,
    body: TransactionUpdate,
    db: Session = Depends(get_db),
):
    tx = update_transaction(db, tx_id, body.model_dump(exclude_none=False))
    if not tx:
        raise HTTPException(status_code=404, detail="거래 없음")
    return {"status": "ok", "item": _tx_to_dict(tx)}


@router.post("/bulk-update")
def bulk_update(body: BulkUpdateRequest, db: Session = Depends(get_db)):
    count = bulk_update_transactions(db, body.ids, body.data.model_dump(exclude_none=False))
    return {"status": "ok", "updated": count}


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
        "merchant_category": tx.merchant_category,
        "approval_amount": tx.approval_amount,
        "project_name": tx.project_name,
        "solution_name": tx.solution_name,
        "account_subject": tx.account_subject,
        "flex_pre_approved": tx.flex_pre_approved,
        "attendees": tx.attendees,
        "purchase_detail": tx.purchase_detail,
        "remarks": tx.remarks,
        "mapping_status": tx.mapping_status,
        "validation_status": tx.validation_status,
        "validation_message": tx.validation_message,
    }
