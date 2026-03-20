"""참조 데이터 CRUD 서비스 (CARD_USERS, PROJECTS, SOLUTIONS, EXPENSE_CATEGORIES)"""
from sqlalchemy.orm import Session

from app.services import card_user_service as card_svc
from app.db.repositories import (
    ProjectRepository,
    SolutionRepository,
    AccountSubjectRepository,
)

_project_repo = ProjectRepository()
_solution_repo = SolutionRepository()
_account_repo = AccountSubjectRepository()


# ── CARD_USERS ─────────────────────────────────────────────────────────────
def get_all_card_users(db: Session = None) -> list[dict]:
    return card_svc.get_all_card_users()


def get_card_user_by_card_number(db: Session, card_number_raw: str, bank_type: str | None = None) -> dict | None:
    return card_svc.get_card_user_by_card_number(card_number_raw, bank_type)


def get_card_user_by_last4(db: Session, card_last4: str, bank_type: str | None = None) -> dict | None:
    return card_svc.get_card_user_by_last4(card_last4, bank_type)


def create_card_user(db: Session, data: dict):
    card_no = data.get("card_number_full") or data.get("card_no")
    if not card_no:
        raise ValueError("card_no required")
    return card_svc.create_card_user(
        card_no=card_no,
        user_name=data["user_name"],
        card_type=data.get("bank_type", "KB"),
        user_email=data.get("user_email") or None,
    )


def update_card_user(db: Session, card_no: str, data: dict):
    return card_svc.update_card_user(
        card_no=card_no,
        user_name=data["user_name"],
        card_type=data.get("bank_type", "KB"),
        user_email=data.get("user_email") or None,
    )


def delete_card_user(db: Session, card_no: str) -> bool:
    return card_svc.delete_card_user(card_no)


# ── PROJECTS ───────────────────────────────────────────────────────────────
def get_all_projects(db: Session = None, active_only: bool = False) -> list[dict]:
    return _project_repo.get_all(active_only=active_only)


def create_project(db: Session, data: dict) -> dict:
    sort_order = _project_repo.get_max_sort_order() + 100
    row = _project_repo.create(
        name=data["name"],
        active_yn=data.get("active_yn", True),
        sort_order=sort_order,
    )
    if not row:
        raise RuntimeError("프로젝트 등록 실패")
    return row


def update_project(db: Session, project_id: int | str, data: dict) -> dict | None:
    return _project_repo.update(str(project_id), data)


def delete_project(db: Session, project_id: int | str) -> bool:
    return _project_repo.delete(str(project_id))


def reorder_projects(db: Session, ordered_ids: list[str]) -> None:
    _project_repo.reorder_keys(ordered_ids)


# ── SOLUTIONS ──────────────────────────────────────────────────────────────
def get_all_solutions(db: Session = None, active_only: bool = False) -> list[dict]:
    return _solution_repo.get_all(active_only=active_only)


def create_solution(db: Session, data: dict) -> dict:
    sort_order = _solution_repo.get_max_sort_order() + 100
    row = _solution_repo.create(
        name=data["name"],
        active_yn=data.get("active_yn", True),
        sort_order=sort_order,
    )
    if not row:
        raise RuntimeError("솔루션 등록 실패")
    return row


def update_solution(db: Session, sol_id: int, data: dict) -> dict | None:
    return _solution_repo.update(sol_id, data)


def delete_solution(db: Session, sol_id: int) -> bool:
    return _solution_repo.delete(sol_id)


def reorder_solutions(db: Session, ordered_ids: list[int]) -> None:
    _solution_repo.reorder_keys(ordered_ids)


# ── EXPENSE_CATEGORIES ──────────────────────────────────────────────────────
def get_all_account_subjects(db: Session = None, active_only: bool = False) -> list[dict]:
    return _account_repo.get_all(active_only=active_only)


def create_account_subject(db: Session, data: dict) -> dict:
    sort_order = _account_repo.get_max_sort_order() + 100
    row = _account_repo.create(
        name=data["name"],
        active_yn=data.get("active_yn", True),
        sort_order=sort_order,
    )
    if not row:
        raise RuntimeError("계정과목 등록 실패")
    return row


def update_account_subject(db: Session, subj_id: int | str, data: dict) -> dict | None:
    return _account_repo.update(str(subj_id), data)


def delete_account_subject(db: Session, subj_id: int | str) -> bool:
    return _account_repo.delete(str(subj_id))


def reorder_account_subjects(db: Session, ordered_ids: list[str]) -> None:
    _account_repo.reorder_keys(ordered_ids)
