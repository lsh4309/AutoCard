-- PostgreSQL 거래내역 테이블 DDL
-- DBeaver: PostgreSQL 연결 후 SQL 편집기에 붙여넣기 → 실행
-- 테이블이 생성되어야만 거래내역 관리 화면에 데이터 표시됨

-- ============================================================
-- transactions (법인카드 승인내역)
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
