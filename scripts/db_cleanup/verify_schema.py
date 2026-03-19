"""
결과물 확인: 테이블 목록 및 행 수
실행: python scripts/db_cleanup/verify_schema.py
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

from app.db.connection import get_pg_conn


def main():
    print("=== information_schema.tables 조회 ===\n")
    with get_pg_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT table_name FROM information_schema.tables
                WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
                ORDER BY table_name
            """)
            tables = [row[0] for row in cur.fetchall()]
    print("테이블 목록:")
    for t in tables:
        print(f"  - {t}")
    print("\n=== 테이블별 행 수 ===\n")
    with get_pg_conn() as conn:
        with conn.cursor() as cur:
            for t in tables:
                cur.execute(f'SELECT COUNT(*) FROM "{t}"')
                cnt = cur.fetchone()[0]
                print(f"  {t}: {cnt}행")
    print("\n완료.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
