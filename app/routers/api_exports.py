"""엑셀 결과 파일 생성/다운로드 API"""
import io
import zipfile
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.excel_export_service import generate_card_excel
from app.services.transaction_service import get_cards_for_export

router = APIRouter(prefix="/api/exports", tags=["exports"])


class ExportRequest(BaseModel):
    card_number: str
    bank: str
    year_month: str | None = None
    user_name: str


class DownloadAllRequest(BaseModel):
    cards: list[ExportRequest]


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
    from app.core.config import EXPORT_DIR
    file_path = EXPORT_DIR / file_name
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="파일 없음")
    return FileResponse(
        path=str(file_path),
        filename=file_name,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


@router.post("/download-all-zip")
def download_all_as_zip(body: DownloadAllRequest, db: Session = Depends(get_db)):
    """모든 카드 엑셀을 생성하여 ZIP으로 묶어 다운로드"""
    if not body.cards:
        raise HTTPException(status_code=400, detail="카드 목록이 비어 있습니다")

    buffer = io.BytesIO()
    used_names: dict[str, int] = {}
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for card in body.cards:
            try:
                file_path = generate_card_excel(
                    db,
                    card_number=card.card_number,
                    bank=card.bank,
                    year_month=card.year_month,
                    user_name=card.user_name,
                )
                base_name = file_path.name
                if base_name in used_names:
                    used_names[base_name] += 1
                    arcname = base_name.replace(".xlsx", f"_{used_names[base_name]}.xlsx")
                else:
                    used_names[base_name] = 1
                    arcname = base_name
                zf.write(file_path, arcname)
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"엑셀 생성 실패: {e}")

    buffer.seek(0)
    year_month = body.cards[0].year_month or "all"
    zip_name = f"card_exports_{year_month}.zip"
    return StreamingResponse(
        buffer,
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{zip_name}"'},
    )


@router.get("/cards")
def list_export_targets(year_month: str = "", db: Session = Depends(get_db)):
    cards = get_cards_for_export(db, year_month or None)
    return cards
