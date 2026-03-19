"""카드 사용자 마스터 서비스 - PostgreSQL card_master 테이블"""
import re
from typing import Any
from app import pg_card_master as pg


def _extract_last4(card_no: str) -> str:
    digits = re.findall(r"\d", str(card_no))
    return "".join(digits[-4:]) if len(digits) >= 4 else ""


def get_all_card_users() -> list[dict[str, Any]]:
    """card_master 전체 조회 (UI 호환 형식)"""
    rows = pg.get_all_card_users()
    return [
        {
            "id": r["card_no"],  # PK로 card_no 사용
            "card_no": r["card_no"],
            "card_number_full": r["card_no"],
            "card_last4": _extract_last4(r["card_no"]),
            "user_name": r["user_name"],
            "bank_type": r["card_type"],
            "user_email": f"{r['user_name']}@pine-partners.com",
            "active_yn": True,
            "note": None,
        }
        for r in rows
    ]


def get_card_user_by_card_number(card_number_raw: str, bank_type: str | None = None) -> dict | None:
    """전체 카드번호로 사용자 조회"""
    r = pg.get_card_user_by_card_number(card_number_raw, bank_type)
    if not r:
        return None
    return {
        "id": r["card_no"],
        "card_no": r["card_no"],
        "card_number_full": r["card_no"],
        "card_last4": _extract_last4(r["card_no"]),
        "user_name": r["user_name"],
        "bank_type": r["card_type"],
        "user_email": f"{r['user_name']}@pinetree.com",
    }


def get_card_user_by_last4(card_last4: str, bank_type: str | None = None) -> dict | None:
    """끝 4자리로 사용자 조회"""
    r = pg.get_card_user_by_last4(card_last4, bank_type)
    if not r:
        return None
    return {
        "id": r["card_no"],
        "card_no": r["card_no"],
        "card_number_full": r["card_no"],
        "card_last4": _extract_last4(r["card_no"]),
        "user_name": r["user_name"],
        "bank_type": r["card_type"],
        "user_email": f"{r['user_name']}@pinetree.com",
    }


def create_card_user(card_no: str, user_name: str, card_type: str) -> dict:
    r = pg.create_card_user(card_no=card_no, user_name=user_name, card_type=card_type)
    return {
        "id": r["card_no"],
        "card_no": r["card_no"],
        "card_number_full": r["card_no"],
        "card_last4": _extract_last4(r["card_no"]),
        "user_name": r["user_name"],
        "bank_type": r["card_type"],
        "user_email": f"{r['user_name']}@pinetree.com",
        "active_yn": True,
        "note": None,
    }


def update_card_user(card_no: str, user_name: str, card_type: str) -> dict | None:
    r = pg.update_card_user(card_no=card_no, user_name=user_name, card_type=card_type)
    if not r:
        return None
    return {
        "id": r["card_no"],
        "card_no": r["card_no"],
        "card_number_full": r["card_no"],
        "card_last4": _extract_last4(r["card_no"]),
        "user_name": r["user_name"],
        "bank_type": r["card_type"],
        "user_email": f"{r['user_name']}@pinetree.com",
    }


def delete_card_user(card_no: str) -> bool:
    return pg.delete_card_user(card_no)
