"""PostgreSQL 연결 및 트랜잭션 관리"""
from contextlib import contextmanager
from typing import Iterator

import psycopg2
from psycopg2.extensions import connection

from app.core.config import PG_HOST, PG_PORT, PG_DATABASE, PG_USER, PG_PASSWORD


def create_connection() -> connection:
    """PostgreSQL 연결 생성"""
    return psycopg2.connect(
        host=PG_HOST,
        port=PG_PORT,
        dbname=PG_DATABASE,
        user=PG_USER,
        password=PG_PASSWORD,
    )


@contextmanager
def get_pg_conn() -> Iterator[connection]:
    """연결 컨텍스트 매니저. 정상 종료 시 commit, 예외 시 rollback"""
    conn = create_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
