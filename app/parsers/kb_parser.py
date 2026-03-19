"""KB 법인카드 승인내역 파서"""
import logging
from pathlib import Path
from typing import Any
import pandas as pd
from app.parsers.common import (
    extract_last4, normalize_date, normalize_time,
    safe_float, find_header_row, match_column, extract_yyyymm_from_date,
)

logger = logging.getLogger(__name__)

# KB 컬럼명 alias 매핑
KB_COLUMN_ALIASES: dict[str, list[str]] = {
    "approval_date":      ["승인일", "거래일", "이용일"],
    "approval_time":      ["승인시간", "거래시간", "이용시간"],
    "card_number":        ["카드번호"],
    "user_name":          ["이용자명", "이용자", "카드사용자"],
    "merchant_name":      ["가맹점명", "가맹점", "이용가맹점"],
    "merchant_category":  ["업종명", "업종", "가맹점업종"],
    "approval_amount":    ["승인금액", "이용금액", "거래금액"],
}


def parse_kb_file(file_path: str | Path, batch_id: str) -> dict[str, Any]:
    """
    KB 승인내역 엑셀 파일 파싱.
    Returns: {"records": [...], "errors": [...], "total": N, "success": N}
    """
    file_path = Path(file_path)
    records: list[dict] = []
    errors: list[dict] = []

    try:
        raw = pd.read_excel(file_path, header=None, dtype=str)
    except Exception as e:
        logger.error(f"KB 파일 읽기 실패: {e}")
        return {"records": [], "errors": [{"row": 0, "message": f"파일 읽기 실패: {e}"}], "total": 0, "success": 0}

    # 헤더 행 탐지
    header_row = find_header_row(raw, ["승인일", "카드번호", "가맹점명"])
    logger.info(f"KB 헤더 행: {header_row}")

    df = pd.read_excel(file_path, header=header_row, dtype=str)
    df.columns = [str(c).strip() for c in df.columns]
    columns = list(df.columns)

    # 컬럼 매핑
    col_map = {key: match_column(columns, aliases) for key, aliases in KB_COLUMN_ALIASES.items()}
    logger.info(f"KB 컬럼 매핑: {col_map}")

    required = ["approval_date", "card_number", "merchant_name", "approval_amount"]
    missing = [k for k in required if col_map.get(k) is None]
    if missing:
        msg = f"필수 컬럼 없음: {missing} / 감지된 컬럼: {columns[:10]}"
        logger.error(msg)
        return {"records": [], "errors": [{"row": 0, "message": msg}], "total": 0, "success": 0}

    for idx, row in df.iterrows():
        row_no = int(idx) + header_row + 2  # 원본 엑셀 행 번호
        try:
            card_raw = str(row.get(col_map["card_number"], "")).strip()
            if not card_raw or card_raw in ("nan", "None"):
                continue  # 빈 행 스킵

            date_str = normalize_date(row.get(col_map["approval_date"]))
            time_str = normalize_time(row.get(col_map["approval_time"])) if col_map.get("approval_time") else None
            approval_dt = f"{date_str} {time_str}" if date_str and time_str else date_str
            yyyymm = extract_yyyymm_from_date(date_str)
            card_last4 = extract_last4(card_raw)
            amount = safe_float(row.get(col_map["approval_amount"]))

            user_col = col_map.get("user_name")
            merchant_cat_col = col_map.get("merchant_category")

            record = {
                "source_bank": "KB",
                "use_year_month": yyyymm,
                "approval_date": date_str,
                "approval_time": time_str,
                "approval_datetime": approval_dt,
                "card_number_raw": card_raw,
                "card_last4": card_last4,
                "card_owner_name": str(row.get(user_col, "")).strip() if user_col else None,
                "card_owner_email": None,
                "merchant_name": str(row.get(col_map["merchant_name"], "")).strip(),
                "merchant_category": str(row.get(merchant_cat_col, "")).strip() if merchant_cat_col else "",
                "approval_amount": amount,
                "project_name": None,
                "solution_name": None,
                "account_subject": None,
                "flex_pre_approved": None,
                "attendees": None,
                "purchase_detail": None,
                "remarks": None,
                "mapping_status": "unmapped",
                "validation_status": "pending",
                "validation_message": None,
                "source_row_no": row_no,
                "upload_batch_id": batch_id,
            }
            records.append(record)
        except Exception as e:
            logger.warning(f"KB 파싱 오류 (행 {row_no}): {e}")
            errors.append({"row": row_no, "message": str(e)})

    return {
        "records": records,
        "errors": errors,
        "total": len(records) + len(errors),
        "success": len(records),
    }
