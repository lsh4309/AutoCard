-- PostgreSQL 마스터 테이블 DDL 및 초기 데이터
-- 실행: psql -U postgres -d postgres -f scripts/sql/init_pg_masters.sql

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
