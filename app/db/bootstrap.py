"""테이블 생성 및 시드 데이터 - 스키마/초기화 전용 (대문자 테이블명)"""
from app.db.connection import get_pg_conn


def init_card_users_table() -> None:
    """CARD_USERS 테이블 생성"""
    with get_pg_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS "CARD_USERS" (
                    card_no   VARCHAR(30) NOT NULL,
                    user_name VARCHAR(50) NOT NULL,
                    card_type VARCHAR(20) NOT NULL,
                    card_no_normalized VARCHAR(30),
                    card_last4 CHAR(4),
                    user_email VARCHAR(100),
                    CONSTRAINT pk_card_users PRIMARY KEY (card_no)
                )
            """)
            cur.execute('CREATE INDEX IF NOT EXISTS idx_card_users_normalized ON "CARD_USERS"(card_no_normalized)')
            cur.execute('CREATE INDEX IF NOT EXISTS idx_card_users_last4 ON "CARD_USERS"(card_last4)')


def init_lookup_tables() -> None:
    """PROJECTS, SOLUTIONS, EXPENSE_CATEGORIES 테이블 생성"""
    with get_pg_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS "PROJECTS" (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(200) NOT NULL UNIQUE,
                    active_yn BOOLEAN NOT NULL DEFAULT TRUE,
                    sort_order INTEGER NOT NULL DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS "SOLUTIONS" (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(200) NOT NULL UNIQUE,
                    active_yn BOOLEAN NOT NULL DEFAULT TRUE,
                    sort_order INTEGER NOT NULL DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS "EXPENSE_CATEGORIES" (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(200) NOT NULL UNIQUE,
                    active_yn BOOLEAN NOT NULL DEFAULT TRUE,
                    sort_order INTEGER NOT NULL DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)


def seed_default_lookups() -> None:
    """솔루션/계정과목 기본 데이터 삽입 (없을 때만)"""
    with get_pg_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO "SOLUTIONS" (name, active_yn, sort_order) VALUES
                    ('DataRobot', TRUE, 1),
                    ('Github', TRUE, 2),
                    ('Presales - 솔루션', TRUE, 3),
                    ('해당사항 없음', TRUE, 4)
                ON CONFLICT (name) DO NOTHING
            """)
            cur.execute("""
                INSERT INTO "EXPENSE_CATEGORIES" (name, active_yn, sort_order) VALUES
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


# 하위 호환용 별칭
def init_card_master_table() -> None:
    init_card_users_table()


def init_master_tables() -> None:
    init_lookup_tables()


def seed_default_masters() -> None:
    seed_default_lookups()
