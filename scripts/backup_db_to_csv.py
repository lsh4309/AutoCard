"""
Step 1: 기존 DB 테이블 데이터를 CSV로 백업
실행: python scripts/backup_db_to_csv.py
"""
import csv
import sys
from pathlib import Path

# 프로젝트 루트를 path에 추가
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database.connection import get_pg_conn

# 논리적 테이블별로 시도할 실제 테이블명 (기존/변경 시도 등 혼재 대응)
TABLE_SOURCES = {
    "card_master": ["card_master", "corp_cards", "CARD_USERS", "card_users"],
    "project_master": ["project_master", "projects", "PROJECTS"],
    "solution_master": ["solution_master", "solutions", "SOLUTIONS"],
    "account_subject_master": ["account_subject_master", "expense_categories", "EXPENSE_CATEGORIES"],
    "transactions": ["transactions", "card_transactions", "CARD_TRANSACTIONS"],
}

BACKUP_DIR = Path(__file__).resolve().parent.parent / "backups"
BACKUP_DIR.mkdir(exist_ok=True)


def get_existing_tables(conn) -> set[str]:
    """public 스키마의 테이블 목록 조회"""
    with conn.cursor() as cur:
        cur.execute("""
            SELECT table_name FROM information_schema.tables
            WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
        """)
        return {row[0] for row in cur.fetchall()}


def backup_table(conn, table_name: str, output_path: Path) -> int:
    """테이블을 CSV로 저장. 반환: 행 수"""
    from psycopg2.extras import RealDictCursor

    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(f'SELECT * FROM "{table_name}"')
        rows = cur.fetchall()
        if not rows:
            return 0

        with open(output_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=rows[0].keys())
            writer.writeheader()
            for row in rows:
                writer.writerow({k: ("" if v is None else v) for k, v in row.items()})

    return len(rows)


def main():
    print("=== DB 백업 시작 ===")
    print(f"백업 디렉터리: {BACKUP_DIR}")

    with get_pg_conn() as conn:
        existing = get_existing_tables(conn)
        print(f"존재하는 테이블: {sorted(existing)}")

        backed = 0
        for logical_name, candidates in TABLE_SOURCES.items():
            for candidate in candidates:
                if candidate in existing:
                    out_path = BACKUP_DIR / f"backup_{logical_name}.csv"
                    try:
                        count = backup_table(conn, candidate, out_path)
                        print(f"  [OK] {candidate} -> {out_path.name} ({count}행)")
                        backed += 1
                    except Exception as e:
                        print(f"  [FAIL] {candidate}: {e}")
                    break
            else:
                print(f"  [SKIP] {logical_name}: 해당 테이블 없음")

    print(f"\n백업 완료. 총 {backed}개 테이블 저장됨.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
