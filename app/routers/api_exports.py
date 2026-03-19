"""엑셀 결과 파일 생성/다운로드 API"""
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.db import get_db
from app.services.excel_export_service import generate_card_excel
from app.services.transaction_service import get_cards_for_export

router = APIRouter(prefix="/api/exports", tags=["exports"])


class ExportRequest(BaseModel):
    card_number: str
    bank: str
    year_month: str | None = None
    user_name: str


@router.post("/generate")
def generate_export(body: ExportRequest, db: Session = Depends(get_db)):
    try:
        file_path = generate_card_excel(
            db,
            card_number=body.card_number,
            bank=body.bank,
            year_month=body.year_month,
            user_name=body.user_name,
        )
        return {"status": "ok", "file_name": file_path.name}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/download/{file_name}")
def download_file(file_name: str):
    from app.config import EXPORT_DIR
    file_path = EXPORT_DIR / file_name
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="파일 없음")
    return FileResponse(
        path=str(file_path),
        filename=file_name,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


@router.get("/cards")
def list_export_targets(year_month: str = "", db: Session = Depends(get_db)):
    cards = get_cards_for_export(db, year_month or None)
    return cards
