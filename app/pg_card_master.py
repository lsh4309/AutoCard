"""PostgreSQL card_master 테이블 연동"""
import re
from contextlib import contextmanager
from typing import Any
import psycopg2
from psycopg2.extras import RealDictCursor
from app.config import PG_HOST, PG_PORT, PG_DATABASE, PG_USER, PG_PASSWORD


def _get_conn():
    return psycopg2.connect(
        host=PG_HOST,
        port=PG_PORT,
        dbname=PG_DATABASE,
        user=PG_USER,
        password=PG_PASSWORD,
    )


@contextmanager
def get_pg_conn():
    conn = _get_conn()
    try:
        yield conn
    finally:
        conn.close()


def init_card_master_table():
    """card_master 테이블 생성"""
    with get_pg_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS card_master (
                    card_no   VARCHAR(30) NOT NULL,
                    user_name VARCHAR(50) NOT NULL,
                    card_type VARCHAR(20) NOT NULL,
                    CONSTRAINT pk_card_master PRIMARY KEY (card_no)
                )
            """)
        conn.commit()


def get_all_card_users() -> list[dict[str, Any]]:
    """card_master 전체 조회"""
    try:
        with get_pg_conn() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    "SELECT card_no, user_name, card_type FROM card_master ORDER BY card_type, card_no"
                )
                return [dict(row) for row in cur.fetchall()]
    except Exception:
        return []


def get_card_user_by_card_number(card_number_raw: str, card_type: str | None = None) -> dict | None:
    """전체 카드번호로 사용자 조회 (숫자만 비교)"""
    try:
        from app.parsers.common import normalize_card_number
        normalized = normalize_card_number(card_number_raw)
        if not normalized or len(normalized) < 16:
            return None
        users = get_all_card_users()
        for u in users:
            cn = normalize_card_number(u["card_no"])
            if cn and cn == normalized:
                if card_type and u["card_type"] != card_type:
                    continue
                return u
        return None
    except Exception:
        return None


def get_card_user_by_last4(card_last4: str, card_type: str | None = None) -> dict | None:
    """끝 4자리로 사용자 조회 (동일 카드번호 끝 4자리 여러 시 매칭 시 첫 번째)"""
    users = get_all_card_users()
    for u in users:
        digits = re.findall(r"\d", str(u["card_no"]))
        last4 = "".join(digits[-4:]) if len(digits) >= 4 else ""
        if last4 == card_last4:
            if card_type and u["card_type"] != card_type:
                continue
            return u
    return None


def create_card_user(card_no: str, user_name: str, card_type: str) -> dict:
    """카드 사용자 등록"""
    with get_pg_conn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                "INSERT INTO card_master (card_no, user_name, card_type) VALUES (%s, %s, %s) RETURNING card_no, user_name, card_type",
                (card_no, user_name, card_type),
            )
            row = cur.fetchone()
        conn.commit()
    return dict(row)


def update_card_user(card_no: str, user_name: str, card_type: str) -> dict | None:
    """카드 사용자 수정"""
    with get_pg_conn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                "UPDATE card_master SET user_name = %s, card_type = %s WHERE card_no = %s RETURNING card_no, user_name, card_type",
                (user_name, card_type, card_no),
            )
            row = cur.fetchone()
        conn.commit()
    return dict(row) if row else None


def delete_card_user(card_no: str) -> bool:
    """카드 사용자 삭제"""
    with get_pg_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM card_master WHERE card_no = %s", (card_no,))
            deleted = cur.rowcount
        conn.commit()
    return deleted > 0


def get_card_type_map() -> dict[str, str]:
    """카드번호(정규화) -> card_type 매핑 (은행 자동 판별용)"""
    users = get_all_card_users()
    from app.parsers.common import normalize_card_number
    result = {}
    for u in users:
        cn = normalize_card_number(u["card_no"])
        if cn:
            result[cn] = u["card_type"]
        # 끝 4자리만 있는 경우 (마스킹) - IBK는 4140, 5298 등으로 시작
        last4 = "".join(re.findall(r"\d", str(u["card_no"]))[-4:])
        if last4 and len(last4) == 4:
            key = f"last4_{last4}_{u['card_type']}"
            result[key] = u["card_type"]
    return result
