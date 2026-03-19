"""업로드 API"""
import shutil
import uuid
from pathlib import Path
from fastapi import APIRouter, Depends, File, UploadFile, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.transaction_service import upload_and_save
from app.parsers.common import detect_bank_type_from_file
from app.core.config import UPLOAD_DIR

router = APIRouter(prefix="/api/uploads", tags=["uploads"])


def _friendly_error_message(filename: str, e: Exception) -> str:
    """UniqueViolation 등 DB 제약 위반 시 사용자 친화적 메시지"""
    err_str = str(e)
    if "UniqueViolation" in type(e).__name__ or "unique_transaction_idx" in err_str or "23505" in err_str:
        return f"{filename}: 이미 등록된 거래내역이 포함되어 있습니다. (중복 데이터)"
    return f"{filename}: 처리 중 오류가 발생했습니다."


@router.post("")
async def upload_files(
    files: list[UploadFile] = File(...),
    db: Session = Depends(get_db),
):
    if not files:
        raise HTTPException(status_code=400, detail="업로드할 파일을 선택해주세요.")

    results = []
    total_success = 0
    total_skipped = 0
    total_rows = 0
    total_errors = []

    for file in files:
        suffix = Path(file.filename).suffix.lower()
        if suffix not in (".xlsx", ".xls"):
            total_errors.append({"row": 0, "message": f"{file.filename}: 엑셀 파일(.xlsx, .xls)만 업로드 가능합니다."})
            continue

        temp_name = f"{uuid.uuid4().hex}{suffix}"
        save_path = UPLOAD_DIR / temp_name

        try:
            with open(save_path, "wb") as f:
                shutil.copyfileobj(file.file, f)

            bank_type = detect_bank_type_from_file(save_path)
            result = upload_and_save(db, save_path, bank_type)
            total_success += result.get("success", 0)
            total_skipped += result.get("skipped", 0)
            total_rows += result.get("total", 0)
            for err in result.get("errors", []):
                total_errors.append({"row": err.get("row"), "message": f"[{file.filename}] {err.get('message', '')}"})
            results.append({
                "original_filename": file.filename,
                "bank_type": bank_type,
                **result,
            })
        except Exception as e:
            db.rollback()
            total_errors.append({"row": 0, "message": _friendly_error_message(file.filename, e)})
        finally:
            if save_path.exists():
                save_path.unlink(missing_ok=True)

    return {
        "status": "ok",
        "success": total_success,
        "skipped": total_skipped,
        "total": total_rows,
        "errors": total_errors,
        "files": results,
    }
