"""마스터 데이터 API"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.db import get_db
from app.services import master_service as svc

router = APIRouter(prefix="/api/masters", tags=["masters"])


# ── 카드 사용자 (PostgreSQL card_master) ───────────────────────────────────────────
class CardUserIn(BaseModel):
    bank_type: str
    card_last4: str
    card_number_full: str | None = None
    user_name: str
    user_email: str | None = None
    active_yn: bool = True
    note: str | None = None


@router.get("/cards")
def list_card_users(db: Session = Depends(get_db)):
    users = svc.get_all_card_users(db)
    return [_cu_dict(u) for u in users]


@router.post("/cards")
def create_card_user(body: CardUserIn, db: Session = Depends(get_db)):
    card_no = body.card_number_full or body.card_last4
    if not card_no or len(card_no) < 4:
        raise HTTPException(status_code=400, detail="카드번호(전체 또는 끝4자리)가 필요합니다.")
    if body.card_number_full:
        existing = svc.get_card_user_by_card_number(db, body.card_number_full, body.bank_type)
        if existing:
            raise HTTPException(status_code=409, detail=f"동일한 카드번호가 이미 등록되어 있습니다.")
    existing = svc.get_card_user_by_last4(db, body.card_last4, body.bank_type)
    if existing:
        raise HTTPException(status_code=409, detail=f"동일한 카드(은행:{body.bank_type}, 끝4자리:{body.card_last4})가 이미 등록되어 있습니다.")
    obj = svc.create_card_user(db, {
        "card_number_full": card_no,
        "user_name": body.user_name,
        "bank_type": body.bank_type,
    })
    return _cu_dict(obj)


@router.put("/cards/{card_no}")
def update_card_user(card_no: str, body: CardUserIn, db: Session = Depends(get_db)):
    obj = svc.update_card_user(db, card_no, body.model_dump())
    if not obj:
        raise HTTPException(status_code=404, detail="사용자 없음")
    return _cu_dict(obj)


@router.delete("/cards/{card_no}")
def delete_card_user(card_no: str, db: Session = Depends(get_db)):
    if not svc.delete_card_user(db, card_no):
        raise HTTPException(status_code=404, detail="사용자 없음")
    return {"status": "deleted"}


def _cu_dict(u):
    return {
        "id": u.get("id") or u.get("card_no"),
        "bank_type": u.get("bank_type"),
        "card_last4": u.get("card_last4"),
        "card_number_full": u.get("card_number_full") or u.get("card_no"),
        "user_name": u.get("user_name"),
        "user_email": u.get("user_email"),
        "active_yn": u.get("active_yn", True),
        "note": u.get("note"),
    }


# ── 프로젝트 ──────────────────────────────────────────────
class ProjectIn(BaseModel):
    name: str
    active_yn: bool = True
    sort_order: int = 0


@router.get("/projects")
def list_projects(db: Session = Depends(get_db)):
    return [{"id": p.id, "name": p.name, "active_yn": p.active_yn, "sort_order": p.sort_order}
            for p in svc.get_all_projects(db)]


@router.post("/projects")
def create_project(body: ProjectIn, db: Session = Depends(get_db)):
    obj = svc.create_project(db, body.model_dump())
    return {"id": obj.id, "name": obj.name, "active_yn": obj.active_yn, "sort_order": obj.sort_order}


@router.put("/projects/{pid}")
def update_project(pid: int, body: ProjectIn, db: Session = Depends(get_db)):
    obj = svc.update_project(db, pid, body.model_dump())
    if not obj:
        raise HTTPException(status_code=404, detail="프로젝트 없음")
    return {"id": obj.id, "name": obj.name, "active_yn": obj.active_yn, "sort_order": obj.sort_order}


@router.delete("/projects/{pid}")
def delete_project(pid: int, db: Session = Depends(get_db)):
    if not svc.delete_project(db, pid):
        raise HTTPException(status_code=404, detail="프로젝트 없음")
    return {"status": "deleted"}


# ── 솔루션 ────────────────────────────────────────────────
class SolutionIn(BaseModel):
    name: str
    active_yn: bool = True
    sort_order: int = 0


@router.get("/solutions")
def list_solutions(db: Session = Depends(get_db)):
    return [{"id": s.id, "name": s.name, "active_yn": s.active_yn, "sort_order": s.sort_order}
            for s in svc.get_all_solutions(db)]


@router.post("/solutions")
def create_solution(body: SolutionIn, db: Session = Depends(get_db)):
    obj = svc.create_solution(db, body.model_dump())
    return {"id": obj.id, "name": obj.name, "active_yn": obj.active_yn, "sort_order": obj.sort_order}


@router.put("/solutions/{sid}")
def update_solution(sid: int, body: SolutionIn, db: Session = Depends(get_db)):
    obj = svc.update_solution(db, sid, body.model_dump())
    if not obj:
        raise HTTPException(status_code=404, detail="솔루션 없음")
    return {"id": obj.id, "name": obj.name, "active_yn": obj.active_yn, "sort_order": obj.sort_order}


@router.delete("/solutions/{sid}")
def delete_solution(sid: int, db: Session = Depends(get_db)):
    if not svc.delete_solution(db, sid):
        raise HTTPException(status_code=404, detail="솔루션 없음")
    return {"status": "deleted"}


# ── 계정과목 ──────────────────────────────────────────────
class AccountIn(BaseModel):
    name: str
    active_yn: bool = True
    sort_order: int = 0


@router.get("/accounts")
def list_accounts(db: Session = Depends(get_db)):
    return [{"id": a.id, "name": a.name, "active_yn": a.active_yn, "sort_order": a.sort_order}
            for a in svc.get_all_account_subjects(db)]


@router.post("/accounts")
def create_account(body: AccountIn, db: Session = Depends(get_db)):
    obj = svc.create_account_subject(db, body.model_dump())
    return {"id": obj.id, "name": obj.name, "active_yn": obj.active_yn, "sort_order": obj.sort_order}


@router.put("/accounts/{aid}")
def update_account(aid: int, body: AccountIn, db: Session = Depends(get_db)):
    obj = svc.update_account_subject(db, aid, body.model_dump())
    if not obj:
        raise HTTPException(status_code=404, detail="계정과목 없음")
    return {"id": obj.id, "name": obj.name, "active_yn": obj.active_yn, "sort_order": obj.sort_order}


@router.delete("/accounts/{aid}")
def delete_account(aid: int, db: Session = Depends(get_db)):
    if not svc.delete_account_subject(db, aid):
        raise HTTPException(status_code=404, detail="계정과목 없음")
    return {"status": "deleted"}
