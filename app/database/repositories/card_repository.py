"""카드 사용자 마스터 Repository - SQL WHERE 기반 조회 (전체 스캔 제거)"""
from typing import Any

from app.database.base import PgRepository
from app.parsers.common import normalize_card_number, extract_last4


def _normalize(card_no: str) -> str | None:
    n = normalize_card_number(card_no)
    return n if n and len(n) >= 4 else None


def _last4(card_no: str) -> str | None:
    return extract_last4(card_no)


class CardRepository(PgRepository):
    """card_master 테이블 CRUD. card_no_normalized, card_last4로 SQL 필터링"""

    def get_all(self) -> list[dict[str, Any]]:
        return self.fetch_all(
            """
            SELECT card_no, user_name, card_type, card_no_normalized, card_last4
            FROM card_master
            ORDER BY card_type, card_no
            """
        )

    def create(
        self, card_no: str, user_name: str, card_type: str
    ) -> dict[str, Any] | None:
        norm = _normalize(card_no)
        last4 = _last4(card_no)
        return self.fetch_one(
            """
            INSERT INTO card_master (card_no, user_name, card_type, card_no_normalized, card_last4)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING card_no, user_name, card_type
            """,
            (card_no, user_name, card_type, norm, last4),
        )

    def update(
        self, card_no: str, user_name: str, card_type: str
    ) -> dict[str, Any] | None:
        return self.fetch_one(
            """
            UPDATE card_master
               SET user_name = %s,
                   card_type = %s
             WHERE card_no = %s
         RETURNING card_no, user_name, card_type
            """,
            (user_name, card_type, card_no),
        )

    def delete(self, card_no: str) -> bool:
        deleted = self.execute(
            "DELETE FROM card_master WHERE card_no = %s",
            (card_no,),
        )
        return deleted > 0

    def find_by_card_number(
        self, card_number_raw: str, card_type: str | None = None
    ) -> dict[str, Any] | None:
        """전체 카드번호로 사용자 조회 - SQL WHERE card_no_normalized 사용"""
        normalized = normalize_card_number(card_number_raw)
        if not normalized or len(normalized) < 16:
            return None

        if card_type:
            return self.fetch_one(
                """
                SELECT card_no, user_name, card_type
                FROM card_master
                WHERE card_no_normalized = %s AND card_type = %s
                """,
                (normalized, card_type),
            )
        return self.fetch_one(
            """
            SELECT card_no, user_name, card_type
            FROM card_master
            WHERE card_no_normalized = %s
            LIMIT 1
            """,
            (normalized,),
        )

    def find_by_last4(
        self, card_last4: str, card_type: str | None = None
    ) -> dict[str, Any] | None:
        """끝 4자리로 사용자 조회 - SQL WHERE card_last4 사용"""
        if not card_last4 or len(card_last4) != 4:
            return None

        if card_type:
            return self.fetch_one(
                """
                SELECT card_no, user_name, card_type
                FROM card_master
                WHERE card_last4 = %s AND card_type = %s
                LIMIT 1
                """,
                (card_last4, card_type),
            )
        return self.fetch_one(
            """
            SELECT card_no, user_name, card_type
            FROM card_master
            WHERE card_last4 = %s
            LIMIT 1
            """,
            (card_last4,),
        )

    def get_card_type_map(self) -> dict[str, str]:
        """카드번호(정규화) -> card_type 매핑. card_no_normalized 있으면 활용"""
        rows = self.fetch_all(
            """
            SELECT card_no, card_no_normalized, card_last4, card_type
            FROM card_master
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
