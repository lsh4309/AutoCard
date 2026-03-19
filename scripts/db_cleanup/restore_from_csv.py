"""
Step 5: 백업 CSV를 신규 대문자 테이블에 복구
실행: python scripts/db_cleanup/restore_from_csv.py
"""
import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

from app.db.connection import get_pg_conn

BACKUP_DIR = ROOT / "backups"
RESTORE_MAP = {
    "backup_card_master.csv": "CARD_USERS",
    "backup_project_master.csv": "PROJECTS",
    "backup_solution_master.csv": "SOLUTIONS",
    "backup_account_subject_master.csv": "EXPENSE_CATEGORIES",
    "backup_transactions.csv": "CARD_TRANSACTIONS",
}


def restore_table(conn, csv_path: Path, table: str) -> int:
    with open(csv_path, "r", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    if not rows:
        return 0
    cols = list(rows[0].keys())
    if table in ("PROJECTS", "SOLUTIONS", "EXPENSE_CATEGORIES", "CARD_TRANSACTIONS"):
        cols = [c for c in cols if c != "id"]
    if not cols:
        return 0
    placeholders = ", ".join(["%s"] * len(cols))
    col_list = ", ".join(f'"{c}"' for c in cols)
    sql = f'INSERT INTO "{table}" ({col_list}) VALUES ({placeholders})'
    if table == "CARD_TRANSACTIONS":
        sql += " ON CONFLICT ON CONSTRAINT uq_card_transaction DO NOTHING"
    inserted = 0
    with conn.cursor() as cur:
        for row in rows:
            vals = []
            for c in cols:
                v = row.get(c, "")
                if v == "":
                    vals.append(None)
                elif c == "active_yn":
                    vals.append(str(v).lower() in ("true", "1", "t", "yes"))
                elif c == "sort_order":
                    try:
                        vals.append(int(float(v)))
                    except (ValueError, TypeError):
                        vals.append(0)
                elif c == "approval_amount":
                    try:
                        vals.append(float(v))
                    except (ValueError, TypeError):
                        vals.append(None)
                else:
                    vals.append(v)
            try:
                cur.execute(sql, vals)
                inserted += cur.rowcount
            except Exception as e:
                print(f"    Row error: {e}")
    return inserted


def main():
    print("=== CSV 복구 시작 ===")
    print(f"백업 디렉터리: {BACKUP_DIR}")
    if not BACKUP_DIR.exists():
        print("백업 폴더가 없습니다. 먼저 backup_db_to_csv.py를 실행하세요.")
        return 1
    total = 0
    with get_pg_conn() as conn:
        for csv_name, table in RESTORE_MAP.items():
            csv_path = BACKUP_DIR / csv_name
            if not csv_path.exists():
                print(f"  [SKIP] {csv_name} 없음")
                continue
            try:
                n = restore_table(conn, csv_path, table)
                print(f"  [OK] {csv_name} -> {table} ({n}행)")
                total += n
            except Exception as e:
                print(f"  [FAIL] {csv_name}: {e}")
                raise
    print(f"\n복구 완료. 총 {total}행 삽입됨.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
