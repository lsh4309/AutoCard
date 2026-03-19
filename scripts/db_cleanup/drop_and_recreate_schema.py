"""
Step 2 & 3: 기존 테이블 삭제 후 신규 스키마 생성
실행: python scripts/db_cleanup/drop_and_recreate_schema.py
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

from app.db.connection import get_pg_conn

TABLES_TO_DROP = [
    "card_master", "corp_cards", "card_users", "CARD_USERS",
    "project_master", "projects", "PROJECTS",
    "solution_master", "solutions", "SOLUTIONS",
    "account_subject_master", "expense_categories", "EXPENSE_CATEGORIES",
    "transactions", "card_transactions", "CARD_TRANSACTIONS",
]


def drop_tables(conn):
    with conn.cursor() as cur:
        for name in TABLES_TO_DROP:
            try:
                cur.execute(f'DROP TABLE IF EXISTS "{name}" CASCADE')
            except Exception as e:
                print(f"  Skip {name}: {e}")


def create_schema(conn):
    with conn.cursor() as cur:
        cur.execute("""
            CREATE TABLE "CARD_USERS" (
                card_no VARCHAR(30) NOT NULL,
                user_name VARCHAR(50) NOT NULL,
                card_type VARCHAR(20) NOT NULL,
                card_no_normalized VARCHAR(30),
                card_last4 CHAR(4),
                user_email VARCHAR(100),
                CONSTRAINT pk_card_users PRIMARY KEY (card_no)
            )
        """)
        cur.execute('CREATE INDEX idx_card_users_normalized ON "CARD_USERS"(card_no_normalized)')
        cur.execute('CREATE INDEX idx_card_users_last4 ON "CARD_USERS"(card_last4)')
        print("  Created: CARD_USERS")

        cur.execute("""
            CREATE TABLE "PROJECTS" (
                id SERIAL PRIMARY KEY,
                name VARCHAR(200) NOT NULL UNIQUE,
                active_yn BOOLEAN NOT NULL DEFAULT TRUE,
                sort_order INTEGER NOT NULL DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        print("  Created: PROJECTS")

        cur.execute("""
            CREATE TABLE "SOLUTIONS" (
                id SERIAL PRIMARY KEY,
                name VARCHAR(200) NOT NULL UNIQUE,
                active_yn BOOLEAN NOT NULL DEFAULT TRUE,
                sort_order INTEGER NOT NULL DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        print("  Created: SOLUTIONS")

        cur.execute("""
            CREATE TABLE "EXPENSE_CATEGORIES" (
                id SERIAL PRIMARY KEY,
                name VARCHAR(200) NOT NULL UNIQUE,
                active_yn BOOLEAN NOT NULL DEFAULT TRUE,
                sort_order INTEGER NOT NULL DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        print("  Created: EXPENSE_CATEGORIES")

        cur.execute("""
            CREATE TABLE "CARD_TRANSACTIONS" (
                id SERIAL PRIMARY KEY,
                source_bank VARCHAR(10) NOT NULL,
                use_year_month VARCHAR(6),
                approval_date VARCHAR(10),
                approval_time VARCHAR(8),
                approval_datetime VARCHAR(20),
                card_number_raw VARCHAR(50),
                card_last4 VARCHAR(4),
                card_owner_name VARCHAR(50),
                merchant_name VARCHAR(200),
                approval_amount REAL,
                project_name VARCHAR(200),
                solution_name VARCHAR(200),
                account_subject VARCHAR(200),
                flex_pre_approved VARCHAR(1),
                attendees TEXT,
                purchase_detail TEXT,
                remarks TEXT,
                mapping_status VARCHAR(20) DEFAULT 'unmapped',
                upload_batch_id VARCHAR(50),
                CONSTRAINT uq_card_transaction UNIQUE (
                    source_bank, approval_datetime, card_number_raw, merchant_name, approval_amount
                )
            )
        """)
        cur.execute('CREATE INDEX ix_card_transactions_card_last4 ON "CARD_TRANSACTIONS"(card_last4)')
        cur.execute('CREATE INDEX ix_card_transactions_upload_batch_id ON "CARD_TRANSACTIONS"(upload_batch_id)')
        cur.execute('CREATE INDEX ix_card_transactions_use_year_month ON "CARD_TRANSACTIONS"(use_year_month)')
        print("  Created: CARD_TRANSACTIONS")


def main():
    print("=== Step 2: 기존 테이블 삭제 ===")
    with get_pg_conn() as conn:
        drop_tables(conn)
    print("\n=== Step 3: 신규 스키마 생성 ===")
    with get_pg_conn() as conn:
        create_schema(conn)
    print("\n완료.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
