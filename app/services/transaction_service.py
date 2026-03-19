"""거래 데이터 저장/조회/수정 서비스"""
import uuid
import logging
from pathlib import Path
from sqlalchemy.orm import Session
from app.models import Transaction
from app.services.master_service import get_card_user_by_last4, get_card_user_by_card_number
from app.services.validation_service import validate_transaction

from app.parsers.common import is_full_card_number
from app.parsers.kb_parser import parse_kb_file
from app.parsers.ibk_parser import parse_ibk_file

logger = logging.getLogger(__name__)


def upload_and_save(db: Session, file_path: Path, bank_type: str) -> dict:
    """파일 파싱 → 사용자 매핑 → DB 저장"""
    batch_id = str(uuid.uuid4())[:8]

    if bank_type == "KB":
        result = parse_kb_file(file_path, batch_id)
    elif bank_type == "IBK":
        result = parse_ibk_file(file_path, batch_id)
    else:
        return {"success": 0, "total": 0, "errors": [{"row": 0, "message": f"알 수 없는 은행 타입: {bank_type}"}]}

    records = result["records"]
    errors = result["errors"]
    saved = 0

    for rec in records:
        try:
            # 카드 사용자 매핑
            card_raw = rec.get("card_number_raw")
            card_last4 = rec.get("card_last4")
            user = None
            if card_raw and "*" not in str(card_raw):
                user = get_card_user_by_card_number(db, card_raw, bank_type)  # 새 함수
            if not user and card_last4:
                user = get_card_user_by_last4(db, card_last4, bank_type)
            if user:
                rec["card_owner_name"] = user["user_name"]
                rec["card_owner_email"] = user.get("user_email")
                rec["mapping_status"] = "mapped"
            else:
                rec["mapping_status"] = "unmapped"

            tx = Transaction(**rec)
            # 검증
            status, msg = validate_transaction(tx)
            tx.validation_status = status
            tx.validation_message = msg

            db.add(tx)
            saved += 1
        except Exception as e:
            logger.error(f"거래 저장 실패: {e} / 데이터: {rec}")
            errors.append({"row": rec.get("source_row_no", 0), "message": str(e)})

    db.commit()
    return {
        "batch_id": batch_id,
        "success": saved,
        "total": result["total"],
        "errors": errors,
    }


def delete_all_transactions(db: Session) -> int:
    """거래내역 전체 삭제"""
    count = db.query(Transaction).delete()
    db.commit()
    return count


def get_transactions(
    db: Session,
    bank: str | None = None,
    user_name: str | None = None,
    card_last4: str | None = None,
    year_month: str | None = None,
    mapping_status: str | None = None,
    page: int = 1,
    page_size: int = 100,
) -> tuple[list[Transaction], int]:
    q = db.query(Transaction)

    if bank:
        q = q.filter(Transaction.source_bank == bank)
    if user_name:
        q = q.filter(Transaction.card_owner_name.contains(user_name))
    if card_last4:
        q = q.filter(Transaction.card_last4 == card_last4)
    if year_month:
        q = q.filter(Transaction.use_year_month == year_month)
    if mapping_status:
        q = q.filter(Transaction.mapping_status == mapping_status)

    total = q.count()
    items = q.order_by(Transaction.approval_datetime.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return items, total


def update_transaction(db: Session, tx_id: int, data: dict) -> Transaction | None:
    tx = db.query(Transaction).filter(Transaction.id == tx_id).first()
    if not tx:
        return None

    editable_fields = [
        "project_name", "solution_name", "account_subject",
        "flex_pre_approved", "attendees", "purchase_detail", "remarks",
    ]
    for field in editable_fields:
        if field in data:
            setattr(tx, field, data[field])

    status, msg = validate_transaction(tx)
    tx.validation_status = status
    tx.validation_message = msg
    db.commit()
    db.refresh(tx)
    return tx


def bulk_update_transactions(db: Session, tx_ids: list[int], data: dict) -> int:
    """다건 일괄 수정"""
    updated = 0
    editable_fields = [
        "project_name", "solution_name", "account_subject",
        "flex_pre_approved", "attendees", "purchase_detail", "remarks",
    ]
    for tx_id in tx_ids:
        tx = db.query(Transaction).filter(Transaction.id == tx_id).first()
        if tx:
            for field in editable_fields:
                if field in data and data[field] is not None and data[field] != "":
                    setattr(tx, field, data[field])
            status, msg = validate_transaction(tx)
            tx.validation_status = status
            tx.validation_message = msg
            updated += 1
    db.commit()
    return updated


def remap_transactions(db: Session) -> int:
    """카드 사용자 마스터 기준으로 미매핑 거래를 재매핑"""
    from app.models import CardUser
    unmapped = db.query(Transaction).filter(Transaction.mapping_status == "unmapped").all()
    updated = 0
    
    for tx in unmapped:
        user = None
        if tx.card_number_raw and "*" not in str(tx.card_number_raw):
            user = get_card_user_by_card_number(db, tx.card_number_raw, tx.source_bank)
        if not user and tx.card_last4:
            user = get_card_user_by_last4(db, tx.card_last4, tx.source_bank)
        if user:
            tx.card_owner_name = user["user_name"]
            tx.card_owner_email = user.get("user_email")
            tx.mapping_status = "mapped"
            status, msg = validate_transaction(tx)
            tx.validation_status = status
            tx.validation_message = msg
            updated += 1
    db.commit()
    return updated


def get_cards_for_export(db: Session, year_month: str | None = None) -> list[dict]:
    """결과 파일 생성 대상 카드 목록 (card_number_raw 전체번호 우선, 마스킹 시 card_last4)"""
    q = db.query(Transaction).filter(Transaction.source_bank.isnot(None))
    if year_month:
        q = q.filter(Transaction.use_year_month == year_month)

    seen: dict[tuple[str, str], dict] = {}
    for tx in q.all():
        card_key = (
            tx.card_number_raw
            if tx.card_number_raw and is_full_card_number(tx.card_number_raw)
            else tx.card_last4 or ""
        )
        if not card_key:
            continue
        key = (tx.source_bank, card_key)
        if key in seen:
            continue
        count_q = db.query(Transaction).filter(Transaction.source_bank == tx.source_bank)
        if is_full_card_number(tx.card_number_raw):
            count_q = count_q.filter(Transaction.card_number_raw == tx.card_number_raw)
        else:
            count_q = count_q.filter(Transaction.card_last4 == tx.card_last4)
        if year_month:
            count_q = count_q.filter(Transaction.use_year_month == year_month)

        total = count_q.count()
        ok = count_q.filter(Transaction.validation_status == "ok").count()
        display_name = tx.card_owner_name or (
            f"미매핑({tx.card_last4})" if tx.card_last4 else "미매핑"
        )
        seen[key] = {
            "bank": tx.source_bank,
            "card_last4": tx.card_last4,
            "card_number_raw": tx.card_number_raw if is_full_card_number(tx.card_number_raw) else None,
            "user_name": display_name,
            "year_month": tx.use_year_month,
            "total": total,
            "ok": ok,
            "warning": total - ok,
        }
    return list(seen.values())
