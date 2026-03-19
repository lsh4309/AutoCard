"""거래 데이터 저장/조회/수정 서비스"""
import re
import uuid
import logging
from pathlib import Path
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.models import Transaction
from app.services.lookup_service import get_all_card_users
from app.parsers.common import is_full_card_number, normalize_card_number
from app.parsers.kb_parser import parse_kb_file
from app.parsers.ibk_parser import parse_ibk_file

logger = logging.getLogger(__name__)


def _build_card_lookups(db: Session) -> tuple[dict, dict]:
    """카드 마스터 1회 조회 후 (전체번호, 끝4자리) → user 매핑 반환. N+1 방지용."""
    users = get_all_card_users(db)
    full_lookup: dict[tuple[str, str], dict] = {}
    last4_lookup: dict[tuple[str, str], dict] = {}
    for u in users:
        card_no = u.get("card_no") or u.get("card_number_full")
        if not card_no:
            continue
        bank = u.get("bank_type")
        cn = normalize_card_number(card_no)
        digits = re.findall(r"\d", str(card_no))
        last4 = "".join(digits[-4:]) if len(digits) >= 4 else ""
        if cn and len(cn) >= 16:
            key = (cn, bank)
            if key not in full_lookup:
                full_lookup[key] = u
        if last4:
            key = (last4, bank)
            if key not in last4_lookup:
                last4_lookup[key] = u
    return full_lookup, last4_lookup


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
    skipped = 0  # 중복으로 스킵된 건수
    full_lookup, last4_lookup = _build_card_lookups(db)
    cols = {c.name for c in Transaction.__table__.columns}

    for rec in records:
        savepoint = db.begin_nested()
        try:
            # 카드 사용자 매핑 (룩업 1회 로드로 N+1 방지)
            card_raw = rec.get("card_number_raw")
            card_last4 = rec.get("card_last4")
            user = None
            if card_raw and "*" not in str(card_raw):
                cn = normalize_card_number(card_raw)
                if cn and len(cn) >= 16:
                    user = full_lookup.get((cn, bank_type))
            if not user and card_last4:
                user = last4_lookup.get((card_last4, bank_type))
            if user:
                rec["card_owner_name"] = user["user_name"]
                rec["mapping_status"] = "mapped"
            else:
                rec["mapping_status"] = "unmapped"

            tx = Transaction(**{k: v for k, v in rec.items() if k in cols})
            db.add(tx)
            db.flush()
            savepoint.commit()
            saved += 1
        except IntegrityError as ie:
            savepoint.rollback()
            err_str = str(ie)
            is_dup = (
                "unique_transaction_idx" in err_str
                or "23505" in err_str
                or (ie.orig and getattr(ie.orig, "pgcode", None) == "23505")
            )
            if is_dup:
                skipped += 1
            else:
                logger.error(f"거래 저장 실패: {ie} / 데이터: {rec}")
                errors.append({"row": rec.get("source_row_no", 0), "message": "데이터 저장 중 제약 위반이 발생했습니다."})
        except Exception as e:
            savepoint.rollback()
            logger.error(f"거래 저장 실패: {e} / 데이터: {rec}")
            errors.append({"row": rec.get("source_row_no", 0), "message": str(e)})

    db.commit()
    return {
        "batch_id": batch_id,
        "success": saved,
        "skipped": skipped,
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
    card_number: str | None = None,
    year_month: str | None = None,
    mapping_status: str | None = None,
    page: int = 1,
    page_size: int = 100,
) -> tuple[list[Transaction], int]:
    from app.parsers.common import normalize_card_number, extract_last4

    q = db.query(Transaction)

    if bank:
        q = q.filter(Transaction.source_bank == bank)
    if user_name:
        q = q.filter(Transaction.card_owner_name.contains(user_name))
    if year_month:
        q = q.filter(Transaction.use_year_month == year_month)
    if mapping_status:
        q = q.filter(Transaction.mapping_status == mapping_status)
    if card_number:
        norm = normalize_card_number(card_number)
        if norm and len(norm) >= 16:
            last4 = extract_last4(card_number)
            q = q.filter(Transaction.card_last4 == last4)  # DB 필터로 후보 축소 후 메모리 필터
            all_tx = q.all()
            ids = [t.id for t in all_tx if (t.card_number_raw and normalize_card_number(t.card_number_raw) == norm) or (not t.card_number_raw and t.card_last4 == last4)]
            from sqlalchemy import false
            q = db.query(Transaction).filter(Transaction.id.in_(ids)) if ids else db.query(Transaction).filter(false())
        else:
            q = q.filter(Transaction.card_last4 == card_number)

    total = q.count()
    items = q.order_by(Transaction.approval_datetime.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return items, total


def remap_transactions(db: Session) -> int:
    """카드 사용자 마스터 기준으로 미매핑 거래를 재매핑"""
    unmapped = db.query(Transaction).filter(Transaction.mapping_status == "unmapped").all()
    if not unmapped:
        return 0
    full_lookup, last4_lookup = _build_card_lookups(db)
    updated = 0
    for tx in unmapped:
        user = None
        if tx.card_number_raw and "*" not in str(tx.card_number_raw):
            cn = normalize_card_number(tx.card_number_raw)
            if cn and len(cn) >= 16:
                user = full_lookup.get((cn, tx.source_bank))
        if not user and tx.card_last4:
            user = last4_lookup.get((tx.card_last4, tx.source_bank))
        if user:
            tx.card_owner_name = user["user_name"]
            tx.mapping_status = "mapped"
            updated += 1
    db.commit()
    return updated


def get_cards_for_export(db: Session, year_month: str | None = None) -> list[dict]:
    """결과 파일 생성 대상 카드 목록 (전체번호 기반, 마스킹 시 CARD_USERS에서 card_no 조회)"""
    from collections import defaultdict

    full_lookup, last4_lookup = _build_card_lookups(db)
    q = db.query(Transaction).filter(Transaction.source_bank.isnot(None))
    if year_month:
        q = q.filter(Transaction.use_year_month == year_month)

    seen: dict[tuple[str, str], dict] = {}
    counts: dict[tuple[str, str], int] = defaultdict(int)
    for tx in q.all():
        card_number = ""
        matched_user: dict | None = None
        if tx.card_number_raw and is_full_card_number(tx.card_number_raw):
            card_number = tx.card_number_raw
            matched_user = full_lookup.get((normalize_card_number(tx.card_number_raw), tx.source_bank))
        elif tx.card_last4:
            matched_user = last4_lookup.get((tx.card_last4, tx.source_bank))
            card_number = matched_user["card_no"] if matched_user else tx.card_last4

        if not card_number:
            continue
        key = (tx.source_bank, card_number)
        counts[key] += 1
        if key in seen:
            continue
        display_name = tx.card_owner_name or (
            f"미매핑({tx.card_last4})" if tx.card_last4 else "미매핑"
        )
        user_email = matched_user.get("user_email") if matched_user else None
        seen[key] = {
            "bank": tx.source_bank,
            "card_number": card_number,
            "user_name": display_name,
            "user_email": user_email,
            "year_month": tx.use_year_month,
            "total": 0,
        }
    for key, total in counts.items():
        seen[key]["total"] = total
    return list(seen.values())
