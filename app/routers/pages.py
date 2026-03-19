"""페이지 렌더링 라우터"""
import json
from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.db import get_db
from app.services.master_service import (
    get_all_card_users, get_all_projects,
    get_all_solutions, get_all_account_subjects,
)
from app.services.transaction_service import get_transactions, get_cards_for_export
from pathlib import Path

router = APIRouter()
templates = Jinja2Templates(directory=str(Path(__file__).parent.parent / "templates"))

# tojson 필터 등록
def _tojson_filter(value):
    return json.dumps(value, ensure_ascii=False)

templates.env.filters["tojson"] = _tojson_filter


@router.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("upload.html", {"request": request})


@router.get("/upload", response_class=HTMLResponse)
async def upload_page(request: Request):
    return templates.TemplateResponse("upload.html", {"request": request})


@router.get("/transactions", response_class=HTMLResponse)
async def transactions_page(
    request: Request,
    bank: str = "",
    user_name: str = "",
    card_number: str = "",
    year_month: str = "",
    mapping_status: str = "",
    page: int = 1,
    db: Session = Depends(get_db),
):
    page_size = 50
    items, total = get_transactions(
        db,
        bank=bank or None,
        user_name=user_name or None,
        card_number=card_number or None,
        year_month=year_month or None,
        mapping_status=mapping_status or None,
        page=page,
        page_size=page_size,
    )
    total_pages = (total + page_size - 1) // page_size

    return templates.TemplateResponse("transactions.html", {
        "request": request,
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
        "filter_bank": bank,
        "filter_user": user_name,
        "filter_card_number": card_number,
        "filter_ym": year_month,
        "filter_mapping": mapping_status,
    })


@router.get("/masters/cards", response_class=HTMLResponse)
async def masters_cards(request: Request, db: Session = Depends(get_db)):
    users = get_all_card_users(db)
    return templates.TemplateResponse("masters_cards.html", {"request": request, "users": users})


@router.get("/masters/projects", response_class=HTMLResponse)
async def masters_projects(request: Request, db: Session = Depends(get_db)):
    projects = get_all_projects(db)
    return templates.TemplateResponse("masters_projects.html", {"request": request, "projects": projects})


@router.get("/masters/solutions", response_class=HTMLResponse)
async def masters_solutions(request: Request, db: Session = Depends(get_db)):
    solutions = get_all_solutions(db)
    return templates.TemplateResponse("masters_solutions.html", {"request": request, "solutions": solutions})


@router.get("/masters/accounts", response_class=HTMLResponse)
async def masters_accounts(request: Request, db: Session = Depends(get_db)):
    accounts = get_all_account_subjects(db)
    return templates.TemplateResponse("masters_accounts.html", {"request": request, "accounts": accounts})


@router.get("/exports", response_class=HTMLResponse)
async def exports_page(request: Request, year_month: str = "", db: Session = Depends(get_db)):
    cards = get_cards_for_export(db, year_month or None)
    return templates.TemplateResponse("exports.html", {
        "request": request,
        "cards": cards,
        "filter_ym": year_month,
    })
