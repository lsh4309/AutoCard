-- PostgreSQL 마스터 + 거래내역 테이블 DDL 및 초기 데이터
-- DBeaver: PostgreSQL 연결 후 SQL 편집기에 붙여넣기 → 실행
-- 실행: psql -U postgres -d postgres -f scripts/sql/init_pg_masters.sql

-- ============================================================
-- 0. 카드 사용자 마스터
-- ============================================================
CREATE TABLE IF NOT EXISTS card_master (
    card_no           VARCHAR(30) NOT NULL,
    user_name         VARCHAR(50) NOT NULL,
    card_type         VARCHAR(20) NOT NULL,
    card_no_normalized VARCHAR(30),
    card_last4        CHAR(4),
    CONSTRAINT pk_card_master PRIMARY KEY (card_no)
);
CREATE INDEX IF NOT EXISTS idx_card_master_card_no_normalized ON card_master(card_no_normalized);
CREATE INDEX IF NOT EXISTS idx_card_master_card_last4 ON card_master(card_last4);

-- ============================================================
-- 1. 프로젝트 마스터
-- ============================================================
CREATE TABLE IF NOT EXISTS project_master (
    id          SERIAL PRIMARY KEY,
    name        VARCHAR(200) NOT NULL UNIQUE,
    active_yn    BOOLEAN NOT NULL DEFAULT TRUE,
    sort_order   INTEGER NOT NULL DEFAULT 0,
    created_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- 2. 솔루션 마스터
-- ============================================================
CREATE TABLE IF NOT EXISTS solution_master (
    id          SERIAL PRIMARY KEY,
    name        VARCHAR(200) NOT NULL UNIQUE,
    active_yn    BOOLEAN NOT NULL DEFAULT TRUE,
    sort_order   INTEGER NOT NULL DEFAULT 0,
    created_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- 3. 계정과목 마스터
-- ============================================================
CREATE TABLE IF NOT EXISTS account_subject_master (
    id          SERIAL PRIMARY KEY,
    name        VARCHAR(200) NOT NULL UNIQUE,
    active_yn    BOOLEAN NOT NULL DEFAULT TRUE,
    sort_order   INTEGER NOT NULL DEFAULT 0,
    created_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- 4. 초기 데이터 (ON CONFLICT로 중복 시 스킵)
-- ============================================================

-- 솔루션 기본 데이터
INSERT INTO solution_master (name, active_yn, sort_order) VALUES
    ('DataRobot', TRUE, 1),
    ('Github', TRUE, 2),
    ('Presales - 솔루션', TRUE, 3),
    ('해당사항 없음', TRUE, 4)
ON CONFLICT (name) DO NOTHING;

-- 계정과목 기본 데이터
INSERT INTO account_subject_master (name, active_yn, sort_order) VALUES
    ('식대', TRUE, 1),
    ('교통비', TRUE, 2),
    ('접대비', TRUE, 3),
    ('회의비', TRUE, 4),
    ('소모품비', TRUE, 5),
    ('도서인쇄비', TRUE, 6),
    ('교육훈련비', TRUE, 7),
    ('기타경비', TRUE, 8)
ON CONFLICT (name) DO NOTHING;

-- 프로젝트는 사용자가 화면에서 등록 (초기 데이터 없음)

-- ============================================================
-- 5. 거래내역 (transactions)
-- ============================================================
CREATE TABLE IF NOT EXISTS transactions (
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
    upload_batch_id     VARCHAR(50)
);
CREATE INDEX IF NOT EXISTS ix_transactions_card_last4 ON transactions(card_last4);
CREATE INDEX IF NOT EXISTS ix_transactions_upload_batch_id ON transactions(upload_batch_id);
CREATE INDEX IF NOT EXISTS ix_transactions_use_year_month ON transactions(use_year_month);
