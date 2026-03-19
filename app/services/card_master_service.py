"""카드 사용자 마스터 서비스 - PostgreSQL card_master 테이블"""
import re
from typing import Any

from app.database.repositories import CardRepository

_card_repo = CardRepository()


def _extract_last4(card_no: str) -> str:
    digits = re.findall(r"\d", str(card_no))
    return "".join(digits[-4:]) if len(digits) >= 4 else ""


def _to_ui_format(row: dict[str, Any] | None, email_domain: str = "pine-partners.com") -> dict[str, Any] | None:
    if not row:
        return None
    return {
        "id": row["card_no"],
        "card_no": row["card_no"],
        "card_number_full": row["card_no"],
        "card_last4": _extract_last4(row["card_no"]),
        "user_name": row["user_name"],
        "bank_type": row["card_type"],
        "user_email": f"{row['user_name']}@{email_domain}",
        "active_yn": True,
        "note": None,
    }


def get_all_card_users() -> list[dict[str, Any]]:
    """card_master 전체 조회 (UI 호환 형식)"""
    rows = _card_repo.get_all()
    return [_to_ui_format(r) for r in rows]


def get_card_user_by_card_number(card_number_raw: str, bank_type: str | None = None) -> dict | None:
    """전체 카드번호로 사용자 조회"""
    r = _card_repo.find_by_card_number(card_number_raw, bank_type)
    return _to_ui_format(r, "pinetree.com")


def get_card_user_by_last4(card_last4: str, bank_type: str | None = None) -> dict | None:
    """끝 4자리로 사용자 조회"""
    r = _card_repo.find_by_last4(card_last4, bank_type)
    return _to_ui_format(r, "pinetree.com")


def create_card_user(card_no: str, user_name: str, card_type: str) -> dict:
    r = _card_repo.create(card_no=card_no, user_name=user_name, card_type=card_type)
    if not r:
        raise RuntimeError("카드 사용자 등록 실패")
    result = _to_ui_format(r, "pinetree.com")
    return result or {}


def update_card_user(card_no: str, user_name: str, card_type: str) -> dict | None:
    r = _card_repo.update(card_no=card_no, user_name=user_name, card_type=card_type)
    return _to_ui_format(r, "pinetree.com")


def delete_card_user(card_no: str) -> bool:
    return _card_repo.delete(card_no)
