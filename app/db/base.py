"""PostgreSQL Repository 베이스 클래스 - SQL 실행 공통화"""
from typing import Any, Callable, Iterable

from psycopg2.extras import RealDictCursor

from app.db.connection import get_pg_conn


class PgRepository:
    """공통 fetch/execute 메서드 제공. conn_provider 주입으로 테스트 시 mock 가능"""

    def __init__(self, conn_provider: Callable = get_pg_conn):
        self._conn_provider = conn_provider

    def fetch_all(
        self, sql: str, params: Iterable[Any] | None = None
    ) -> list[dict[str, Any]]:
        with self._conn_provider() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(sql, params or ())
                return [dict(row) for row in cur.fetchall()]

    def fetch_one(
        self, sql: str, params: Iterable[Any] | None = None
    ) -> dict[str, Any] | None:
        with self._conn_provider() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(sql, params or ())
                row = cur.fetchone()
                return dict(row) if row else None

    def execute(self, sql: str, params: Iterable[Any] | None = None) -> int:
        with self._conn_provider() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, params or ())
                return cur.rowcount
