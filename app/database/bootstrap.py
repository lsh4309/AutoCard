"""테이블 생성 및 시드 데이터 - 스키마/초기화 전용"""
from app.database.connection import get_pg_conn


def init_card_master_table() -> None:
    """card_master 테이블 생성 (card_no_normalized, card_last4 포함)"""
    with get_pg_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS card_master (
                    card_no   VARCHAR(30) NOT NULL,
                    user_name VARCHAR(50) NOT NULL,
                    card_type VARCHAR(20) NOT NULL,
                    card_no_normalized VARCHAR(30),
                    card_last4 CHAR(4),
                    CONSTRAINT pk_card_master PRIMARY KEY (card_no)
                )
            """)
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_card_master_card_no_normalized
                ON card_master(card_no_normalized)
            """)
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_card_master_card_last4
                ON card_master(card_last4)
            """)


def migrate_card_master_add_columns() -> None:
    """기존 card_master에 card_no_normalized, card_last4 컬럼 추가 및 백필"""
    with get_pg_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("ALTER TABLE card_master ADD COLUMN IF NOT EXISTS card_no_normalized VARCHAR(30)")
            cur.execute("ALTER TABLE card_master ADD COLUMN IF NOT EXISTS card_last4 CHAR(4)")
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_card_master_card_no_normalized
                ON card_master(card_no_normalized)
            """)
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_card_master_card_last4
                ON card_master(card_last4)
            """)
            # 백필: 숫자만 추출, 끝 4자리
            cur.execute("""
                UPDATE card_master
                SET card_no_normalized = regexp_replace(card_no, '[^0-9]', '', 'g'),
                    card_last4 = RIGHT(regexp_replace(card_no, '[^0-9]', '', 'g'), 4)
                WHERE card_no_normalized IS NULL AND card_no IS NOT NULL
            """)


def init_master_tables() -> None:
    """project_master, solution_master, account_subject_master 테이블 생성"""
    with get_pg_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS project_master (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(200) NOT NULL UNIQUE,
                    active_yn BOOLEAN NOT NULL DEFAULT TRUE,
                    sort_order INTEGER NOT NULL DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS solution_master (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(200) NOT NULL UNIQUE,
                    active_yn BOOLEAN NOT NULL DEFAULT TRUE,
                    sort_order INTEGER NOT NULL DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS account_subject_master (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(200) NOT NULL UNIQUE,
                    active_yn BOOLEAN NOT NULL DEFAULT TRUE,
                    sort_order INTEGER NOT NULL DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)


def seed_default_masters() -> None:
    """솔루션/계정과목 기본 데이터 삽입 (없을 때만)"""
    with get_pg_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO solution_master (name, active_yn, sort_order) VALUES
                    ('DataRobot', TRUE, 1),
                    ('Github', TRUE, 2),
                    ('Presales - 솔루션', TRUE, 3),
                    ('해당사항 없음', TRUE, 4)
                ON CONFLICT (name) DO NOTHING
            """)
            cur.execute("""
                INSERT INTO account_subject_master (name, active_yn, sort_order) VALUES
                    ('식대', TRUE, 1),
                    ('교통비', TRUE, 2),
                    ('접대비', TRUE, 3),
                    ('회의비', TRUE, 4),
                    ('소모품비', TRUE, 5),
                    ('도서인쇄비', TRUE, 6),
                    ('교육훈련비', TRUE, 7),
                    ('기타경비', TRUE, 8)
                ON CONFLICT (name) DO NOTHING
            """)
