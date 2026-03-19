-- Card Auto 신규 스키마 (대문자 테이블명, Master 명칭 제거)
-- DBeaver: PostgreSQL 연결 후 SQL 편집기에 붙여넣기 → 실행
-- 또는: python scripts/db_cleanup/drop_and_recreate_schema.py

-- ============================================================
-- CARD_USERS (카드 사용자)
-- ============================================================
CREATE TABLE IF NOT EXISTS "CARD_USERS" (
    card_no           VARCHAR(30) NOT NULL,
    user_name         VARCHAR(50) NOT NULL,
    card_type         VARCHAR(20) NOT NULL,
    card_no_normalized VARCHAR(30),
    card_last4        CHAR(4),
    user_email        VARCHAR(100),
    CONSTRAINT pk_card_users PRIMARY KEY (card_no)
);
CREATE INDEX IF NOT EXISTS idx_card_users_normalized ON "CARD_USERS"(card_no_normalized);
CREATE INDEX IF NOT EXISTS idx_card_users_last4 ON "CARD_USERS"(card_last4);

-- ============================================================
-- PROJECTS
-- ============================================================
CREATE TABLE IF NOT EXISTS "PROJECTS" (
    id          SERIAL PRIMARY KEY,
    name        VARCHAR(200) NOT NULL UNIQUE,
    active_yn    BOOLEAN NOT NULL DEFAULT TRUE,
    sort_order   INTEGER NOT NULL DEFAULT 0,
    created_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- SOLUTIONS
-- ============================================================
CREATE TABLE IF NOT EXISTS "SOLUTIONS" (
    id          SERIAL PRIMARY KEY,
    name        VARCHAR(200) NOT NULL UNIQUE,
    active_yn    BOOLEAN NOT NULL DEFAULT TRUE,
    sort_order   INTEGER NOT NULL DEFAULT 0,
    created_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- EXPENSE_CATEGORIES (계정과목)
-- ============================================================
CREATE TABLE IF NOT EXISTS "EXPENSE_CATEGORIES" (
    id          SERIAL PRIMARY KEY,
    name        VARCHAR(200) NOT NULL UNIQUE,
    active_yn    BOOLEAN NOT NULL DEFAULT TRUE,
    sort_order   INTEGER NOT NULL DEFAULT 0,
    created_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- CARD_TRANSACTIONS (거래내역, 중복 방지 유니크 제약)
-- ============================================================
CREATE TABLE IF NOT EXISTS "CARD_TRANSACTIONS" (
    id                  SERIAL PRIMARY KEY,
    source_bank         VARCHAR(10) NOT NULL,
    use_year_month      VARCHAR(6),
    approval_date       VARCHAR(10),
    approval_time       VARCHAR(8),
    approval_datetime   VARCHAR(20),
    card_number_raw     VARCHAR(50),
    card_last4          VARCHAR(4),
    card_owner_name     VARCHAR(50),
    merchant_name       VARCHAR(200),
    approval_amount     REAL,
    project_name        VARCHAR(200),
    solution_name       VARCHAR(200),
    account_subject     VARCHAR(200),
    flex_pre_approved   VARCHAR(1),
    attendees           TEXT,
    purchase_detail     TEXT,
    remarks             TEXT,
    mapping_status      VARCHAR(20) DEFAULT 'unmapped',
    upload_batch_id     VARCHAR(50),
    CONSTRAINT uq_card_transaction UNIQUE (
        source_bank, approval_datetime, card_number_raw, merchant_name, approval_amount
    )
);
CREATE INDEX IF NOT EXISTS ix_card_transactions_card_last4 ON "CARD_TRANSACTIONS"(card_last4);
CREATE INDEX IF NOT EXISTS ix_card_transactions_upload_batch_id ON "CARD_TRANSACTIONS"(upload_batch_id);
CREATE INDEX IF NOT EXISTS ix_card_transactions_use_year_month ON "CARD_TRANSACTIONS"(use_year_month);
