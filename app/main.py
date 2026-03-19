"""FastAPI 애플리케이션 진입점"""
import logging
from pathlib import Path
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from app.routers import pages, api_uploads, api_transactions, api_masters, api_exports, api_mail

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

STATIC_DIR = Path(__file__).parent / "static"

app = FastAPI(
    title="Card Auto - 법인카드 승인내역 관리",
    version="1.0.0",
)

app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

app.include_router(pages.router)
app.include_router(api_uploads.router)
app.include_router(api_transactions.router)
app.include_router(api_masters.router)
app.include_router(api_exports.router)
app.include_router(api_mail.router)
