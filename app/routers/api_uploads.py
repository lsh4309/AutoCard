"""업로드 API"""
import shutil
import uuid
from pathlib import Path
from fastapi import APIRouter, Depends, File, UploadFile, HTTPException
from sqlalchemy.orm import Session
from app.db import get_db
from app.services.transaction_service import upload_and_save
from app.parsers.common import detect_bank_type_from_file
from app.config import UPLOAD_DIR

router = APIRouter(prefix="/api/uploads", tags=["uploads"])


@router.post("")
async def upload_files(
    files: list[UploadFile] = File(...),
    db: Session = Depends(get_db),
):
    if not files:
        raise HTTPException(status_code=400, detail="업로드할 파일을 선택해주세요.")

    results = []
    total_success = 0
    total_errors = []
    total_rows = 0

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
            total_rows += result.get("total", 0)
            for err in result.get("errors", []):
                err["message"] = f"[{file.filename}] {err.get('message', '')}"
                total_errors.append(err)
            results.append({
                "original_filename": file.filename,
                "bank_type": bank_type,
                **result,
            })
        except Exception as e:
            total_errors.append({"row": 0, "message": f"{file.filename}: {str(e)}"})
        finally:
            if save_path.exists():
                save_path.unlink(missing_ok=True)

    return {
        "status": "ok",
        "success": total_success,
        "total": total_rows,
        "errors": total_errors,
        "files": results,
    }
