"""PostgreSQL 프로젝트/솔루션/계정과목 마스터 테이블 연동"""
import logging
from contextlib import contextmanager
from typing import Any
import psycopg2

logger = logging.getLogger(__name__)
from psycopg2.extras import RealDictCursor
from app.config import PG_HOST, PG_PORT, PG_DATABASE, PG_USER, PG_PASSWORD


def _get_conn():
    return psycopg2.connect(
        host=PG_HOST,
        port=PG_PORT,
        dbname=PG_DATABASE,
        user=PG_USER,
        password=PG_PASSWORD,
    )


@contextmanager
def get_pg_conn():
    conn = _get_conn()
    try:
        yield conn
    finally:
        conn.close()


def init_master_tables():
    """프로젝트/솔루션/계정과목 마스터 테이블 생성"""
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
        conn.commit()


def seed_default_masters():
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
        conn.commit()


# ── 프로젝트 (id 컬럼 없음, name이 PK) ────────────────────────────────────────────────
def get_all_projects(active_only: bool = False) -> list[dict[str, Any]]:
    try:
        with get_pg_conn() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                sql = "SELECT name, active_yn, sort_order FROM project_master"
                if active_only:
                    sql += " WHERE active_yn = TRUE"
                sql += " ORDER BY sort_order, name"
                cur.execute(sql)
                rows = [dict(row) for row in cur.fetchall()]
                for r in rows:
                    r["id"] = r["name"]  # 템플릿/API 호환용
                return rows
    except Exception as e:
        logger.exception("get_all_projects 실패: %s", e)
        return []


def create_project(name: str, active_yn: bool = True, sort_order: int = 0) -> dict:
    with get_pg_conn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                "INSERT INTO project_master (name, active_yn, sort_order) VALUES (%s, %s, %s) RETURNING name, active_yn, sort_order",
                (name, active_yn, sort_order),
            )
            row = cur.fetchone()
        conn.commit()
    d = dict(row)
    d["id"] = d["name"]
    return d


def update_project(name_old: str, data: dict) -> dict | None:
    allowed = {"name", "active_yn", "sort_order"}
    updates, params = [], [name_old]
    for k, v in data.items():
        if k in allowed and v is not None:
            updates.append(f"{k} = %s")
            params.append(v)
    if not updates:
        for p in get_all_projects():
            if p["name"] == name_old:
                return p
        return None
    params = params[1:] + [name_old]
    with get_pg_conn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                f"UPDATE project_master SET {', '.join(updates)} WHERE name = %s RETURNING name, active_yn, sort_order",
                params,
            )
            row = cur.fetchone()
        conn.commit()
    if row:
        d = dict(row)
        d["id"] = d["name"]
        return d
    return None


def delete_project(name: str) -> bool:
    with get_pg_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM project_master WHERE name = %s", (name,))
            deleted = cur.rowcount
        conn.commit()
    return deleted > 0


# ── 솔루션 ──────────────────────────────────────────────────
def get_all_solutions(active_only: bool = False) -> list[dict[str, Any]]:
    try:
        with get_pg_conn() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                sql = "SELECT id, name, active_yn, sort_order FROM solution_master"
                if active_only:
                    sql += " WHERE active_yn = TRUE"
                sql += " ORDER BY sort_order, name"
                cur.execute(sql)
                return [dict(row) for row in cur.fetchall()]
    except Exception:
        return []


def create_solution(name: str, active_yn: bool = True, sort_order: int = 0) -> dict:
    with get_pg_conn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                "INSERT INTO solution_master (name, active_yn, sort_order) VALUES (%s, %s, %s) RETURNING id, name, active_yn, sort_order",
                (name, active_yn, sort_order),
            )
            row = cur.fetchone()
        conn.commit()
    return dict(row)


def update_solution(sid: int, data: dict) -> dict | None:
    allowed = {"name", "active_yn", "sort_order"}
    updates, params = [], [sid]
    for k, v in data.items():
        if k in allowed and v is not None:
            updates.append(f"{k} = %s")
            params.append(v)
    if not updates:
        for s in get_all_solutions():
            if s["id"] == sid:
                return s
        return None
    params = params[1:] + [sid]
    with get_pg_conn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                f"UPDATE solution_master SET {', '.join(updates)} WHERE id = %s RETURNING id, name, active_yn, sort_order",
                params,
            )
            row = cur.fetchone()
        conn.commit()
    return dict(row) if row else None


def delete_solution(sid: int) -> bool:
    with get_pg_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM solution_master WHERE id = %s", (sid,))
            deleted = cur.rowcount
        conn.commit()
    return deleted > 0


# ── 계정과목 (id 컬럼 없음, name이 PK) ─────────────────────────────────────────────────
def get_all_account_subjects(active_only: bool = False) -> list[dict[str, Any]]:
    try:
        with get_pg_conn() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                sql = "SELECT name, active_yn, sort_order FROM account_subject_master"
                if active_only:
                    sql += " WHERE active_yn = TRUE"
                sql += " ORDER BY sort_order, name"
                cur.execute(sql)
                rows = [dict(row) for row in cur.fetchall()]
                for r in rows:
                    r["id"] = r["name"]  # 템플릿/API 호환용
                return rows
    except Exception as e:
        logger.exception("get_all_account_subjects 실패: %s", e)
        return []


def create_account_subject(name: str, active_yn: bool = True, sort_order: int = 0) -> dict:
    with get_pg_conn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                "INSERT INTO account_subject_master (name, active_yn, sort_order) VALUES (%s, %s, %s) RETURNING name, active_yn, sort_order",
                (name, active_yn, sort_order),
            )
            row = cur.fetchone()
        conn.commit()
    d = dict(row)
    d["id"] = d["name"]
    return d


def update_account_subject(name_old: str, data: dict) -> dict | None:
    allowed = {"name", "active_yn", "sort_order"}
    updates, params = [], [name_old]
    for k, v in data.items():
        if k in allowed and v is not None:
            updates.append(f"{k} = %s")
            params.append(v)
    if not updates:
        for a in get_all_account_subjects():
            if a["name"] == name_old:
                return a
        return None
    params = params[1:] + [name_old]
    with get_pg_conn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                f"UPDATE account_subject_master SET {', '.join(updates)} WHERE name = %s RETURNING name, active_yn, sort_order",
                params,
            )
            row = cur.fetchone()
        conn.commit()
    if row:
        d = dict(row)
        d["id"] = d["name"]
        return d
    return None


def delete_account_subject(name: str) -> bool:
    with get_pg_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM account_subject_master WHERE name = %s", (name,))
            deleted = cur.rowcount
        conn.commit()
    return deleted > 0
