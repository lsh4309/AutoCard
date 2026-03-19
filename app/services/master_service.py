"""마스터 데이터 CRUD 서비스"""
from sqlalchemy.orm import Session
from app.models import ProjectMaster, SolutionMaster, AccountSubjectMaster
from app.services import card_master_service as card_svc


# ── 카드 사용자 마스터 (PostgreSQL card_master) ─────────────────────────────────────
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
    )


def update_card_user(db: Session, card_no: str, data: dict):
    return card_svc.update_card_user(
        card_no=card_no,
        user_name=data["user_name"],
        card_type=data.get("bank_type", "KB"),
    )


def delete_card_user(db: Session, card_no: str) -> bool:
    return card_svc.delete_card_user(card_no)


# ── 프로젝트 마스터 ───────────────────────────────────────
def get_all_projects(db: Session, active_only: bool = False) -> list[ProjectMaster]:
    q = db.query(ProjectMaster)
    if active_only:
        q = q.filter(ProjectMaster.active_yn == True)
    return q.order_by(ProjectMaster.sort_order, ProjectMaster.name).all()


def create_project(db: Session, data: dict) -> ProjectMaster:
    obj = ProjectMaster(**data)
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def update_project(db: Session, project_id: int, data: dict) -> ProjectMaster | None:
    obj = db.query(ProjectMaster).filter(ProjectMaster.id == project_id).first()
    if not obj:
        return None
    for k, v in data.items():
        setattr(obj, k, v)
    db.commit()
    db.refresh(obj)
    return obj


def delete_project(db: Session, project_id: int) -> bool:
    obj = db.query(ProjectMaster).filter(ProjectMaster.id == project_id).first()
    if not obj:
        return False
    db.delete(obj)
    db.commit()
    return True


# ── 솔루션 마스터 ─────────────────────────────────────────
def get_all_solutions(db: Session, active_only: bool = False) -> list[SolutionMaster]:
    q = db.query(SolutionMaster)
    if active_only:
        q = q.filter(SolutionMaster.active_yn == True)
    return q.order_by(SolutionMaster.sort_order, SolutionMaster.name).all()


def create_solution(db: Session, data: dict) -> SolutionMaster:
    obj = SolutionMaster(**data)
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def update_solution(db: Session, sol_id: int, data: dict) -> SolutionMaster | None:
    obj = db.query(SolutionMaster).filter(SolutionMaster.id == sol_id).first()
    if not obj:
        return None
    for k, v in data.items():
        setattr(obj, k, v)
    db.commit()
    db.refresh(obj)
    return obj


def delete_solution(db: Session, sol_id: int) -> bool:
    obj = db.query(SolutionMaster).filter(SolutionMaster.id == sol_id).first()
    if not obj:
        return False
    db.delete(obj)
    db.commit()
    return True


# ── 계정과목 마스터 ───────────────────────────────────────
def get_all_account_subjects(db: Session, active_only: bool = False) -> list[AccountSubjectMaster]:
    q = db.query(AccountSubjectMaster)
    if active_only:
        q = q.filter(AccountSubjectMaster.active_yn == True)
    return q.order_by(AccountSubjectMaster.sort_order, AccountSubjectMaster.name).all()


def create_account_subject(db: Session, data: dict) -> AccountSubjectMaster:
    obj = AccountSubjectMaster(**data)
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def update_account_subject(db: Session, subj_id: int, data: dict) -> AccountSubjectMaster | None:
    obj = db.query(AccountSubjectMaster).filter(AccountSubjectMaster.id == subj_id).first()
    if not obj:
        return None
    for k, v in data.items():
        setattr(obj, k, v)
    db.commit()
    db.refresh(obj)
    return obj


def delete_account_subject(db: Session, subj_id: int) -> bool:
    obj = db.query(AccountSubjectMaster).filter(AccountSubjectMaster.id == subj_id).first()
    if not obj:
        return False
    db.delete(obj)
    db.commit()
    return True
