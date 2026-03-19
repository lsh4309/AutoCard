"""카드 사용자 Repository - SQL WHERE 기반 조회"""
from typing import Any

from app.db.base import PgRepository
from app.parsers.common import normalize_card_number, extract_last4


def _normalize(card_no: str) -> str | None:
    n = normalize_card_number(card_no)
    return n if n and len(n) >= 4 else None


def _last4(card_no: str) -> str | None:
    return extract_last4(card_no)


class CardRepository(PgRepository):
    """CARD_USERS 테이블 CRUD. card_no_normalized, card_last4로 SQL 필터링"""

    def get_all(self) -> list[dict[str, Any]]:
        return self.fetch_all(
            """
            SELECT card_no, user_name, card_type, card_no_normalized, card_last4, user_email
            FROM "CARD_USERS"
            ORDER BY card_type, card_no
            """
        )

    def create(
        self, card_no: str, user_name: str, card_type: str, user_email: str | None = None
    ) -> dict[str, Any] | None:
        norm = _normalize(card_no)
        last4 = _last4(card_no)
        return self.fetch_one(
            """
            INSERT INTO "CARD_USERS" (card_no, user_name, card_type, card_no_normalized, card_last4, user_email)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING card_no, user_name, card_type, user_email
            """,
            (card_no, user_name, card_type, norm, last4, user_email),
        )

    def update(
        self, card_no: str, user_name: str, card_type: str, user_email: str | None = None
    ) -> dict[str, Any] | None:
        return self.fetch_one(
            """
            UPDATE "CARD_USERS"
               SET user_name = %s,
                   card_type = %s,
                   user_email = %s
             WHERE card_no = %s
         RETURNING card_no, user_name, card_type, user_email
            """,
            (user_name, card_type, user_email, card_no),
        )

    def delete(self, card_no: str) -> bool:
        deleted = self.execute(
            'DELETE FROM "CARD_USERS" WHERE card_no = %s',
            (card_no,),
        )
        return deleted > 0

    def find_by_card_number(
        self, card_number_raw: str, card_type: str | None = None
    ) -> dict[str, Any] | None:
        normalized = normalize_card_number(card_number_raw)
        if not normalized or len(normalized) < 16:
            return None
        if card_type:
            return self.fetch_one(
                """
                SELECT card_no, user_name, card_type, user_email
                FROM "CARD_USERS"
                WHERE card_no_normalized = %s AND card_type = %s
                """,
                (normalized, card_type),
            )
        return self.fetch_one(
            """
            SELECT card_no, user_name, card_type, user_email
            FROM "CARD_USERS"
            WHERE card_no_normalized = %s
            LIMIT 1
            """,
            (normalized,),
        )

    def find_by_last4(
        self, card_last4: str, card_type: str | None = None
    ) -> dict[str, Any] | None:
        if not card_last4 or len(card_last4) != 4:
            return None
        if card_type:
            return self.fetch_one(
                """
                SELECT card_no, user_name, card_type, user_email
                FROM "CARD_USERS"
                WHERE card_last4 = %s AND card_type = %s
                LIMIT 1
                """,
                (card_last4, card_type),
            )
        return self.fetch_one(
            """
            SELECT card_no, user_name, card_type, user_email
            FROM "CARD_USERS"
            WHERE card_last4 = %s
            LIMIT 1
            """,
            (card_last4,),
        )

    def get_card_type_map(self) -> dict[str, str]:
        rows = self.fetch_all(
            """
            SELECT card_no, card_no_normalized, card_last4, card_type
            FROM "CARD_USERS"
            """
        )
        result: dict[str, str] = {}
        for r in rows:
            norm = r.get("card_no_normalized") or normalize_card_number(r["card_no"])
            if norm:
                result[norm] = r["card_type"]
            last4 = r.get("card_last4") or _last4(r["card_no"])
            if last4 and len(last4) == 4:
                result[f"last4_{last4}_{r['card_type']}"] = r["card_type"]
        return result
