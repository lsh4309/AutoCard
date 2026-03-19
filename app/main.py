"""FastAPI 애플리케이션 진입점"""
import logging
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from app.db import init_db
from app.routers import pages, api_uploads, api_transactions, api_masters, api_exports
from app.services.master_service import (
    get_all_solutions, create_solution,
    get_all_account_subjects, create_account_subject,
)
from app.db import SessionLocal

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

STATIC_DIR = Path(__file__).parent / "static"


def _seed_defaults(db):
    """기본 솔루션 / 계정과목 시드 데이터"""
    default_solutions = [
        ("DataRobot", 1),
        ("Github", 2),
        ("Presales - 솔루션", 3),
        ("해당사항 없음", 4),
    ]
    existing = {s.name for s in get_all_solutions(db)}
    for name, order in default_solutions:
        if name not in existing:
            create_solution(db, {"name": name, "active_yn": True, "sort_order": order})

    default_accounts = [
        ("식대", 1),
        ("교통비", 2),
        ("접대비", 3),
        ("회의비", 4),
        ("소모품비", 5),
        ("도서인쇄비", 6),
        ("교육훈련비", 7),
        ("기타경비", 8),
    ]
    existing_acc = {a.name for a in get_all_account_subjects(db)}
    for name, order in default_accounts:
        if name not in existing_acc:
            create_account_subject(db, {"name": name, "active_yn": True, "sort_order": order})


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    with SessionLocal() as db:
        _seed_defaults(db)
    logger.info("DB 초기화 완료")
    yield


app = FastAPI(
    title="Card Auto - 법인카드 승인내역 관리",
    version="1.0.0",
    lifespan=lifespan,
)

app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

app.include_router(pages.router)
app.include_router(api_uploads.router)
app.include_router(api_transactions.router)
app.include_router(api_masters.router)
app.include_router(api_exports.router)
