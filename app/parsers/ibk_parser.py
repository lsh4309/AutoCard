"""IBK 법인카드 승인내역 파서"""
import logging
import re
from pathlib import Path
from typing import Any
import pandas as pd
from app.parsers.common import (
    extract_last4, normalize_date, normalize_time,
    safe_float, find_header_row, match_column, extract_yyyymm_from_date,
)

logger = logging.getLogger(__name__)

# IBK 컬럼명 alias 매핑
IBK_COLUMN_ALIASES: dict[str, list[str]] = {
    "approval_datetime":  ["승인일시", "이용일시", "거래일시"],
    "approval_date":      ["승인일", "거래일", "이용일"],
    "approval_time":      ["승인시간", "거래시간", "이용시간"],
    "card_number":        ["카드번호"],
    "merchant_name":      ["이용가맹점명", "가맹점명", "가맹점"],
    "merchant_category":  ["업종명", "업종"],
    "approval_amount":    ["승인금액", "이용금액", "거래금액"],
}


def _split_datetime(dt_str: str) -> tuple[str | None, str | None]:
    """'2026-01-30 18:06:52' 형식을 날짜/시간으로 분리"""
    if not dt_str or dt_str in ("nan", "None"):
        return None, None
    m = re.match(r"(\d{4}[-./]\d{2}[-./]\d{2})\s+(\d{2}:\d{2}:\d{2})", dt_str)
    if m:
        date_part = normalize_date(m.group(1))
        time_part = m.group(2)
        return date_part, time_part
    return normalize_date(dt_str), None


def parse_ibk_file(file_path: str | Path, batch_id: str) -> dict[str, Any]:
    """
    IBK 승인내역 엑셀 파일 파싱.
    Returns: {"records": [...], "errors": [...], "total": N, "success": N}
    """
    file_path = Path(file_path)
    records: list[dict] = []
    errors: list[dict] = []

    try:
        raw = pd.read_excel(file_path, header=None, dtype=str)
    except Exception as e:
        logger.error(f"IBK 파일 읽기 실패: {e}")
        return {"records": [], "errors": [{"row": 0, "message": f"파일 읽기 실패: {e}"}], "total": 0, "success": 0}

    # 헤더 행 탐지 (IBK는 보통 2번 행)
    header_row = find_header_row(raw, ["승인일시", "카드번호", "이용가맹점명"], max_rows=10)
    logger.info(f"IBK 헤더 행: {header_row}")

    df = pd.read_excel(file_path, header=header_row, dtype=str)
    df.columns = [str(c).strip() for c in df.columns]
    columns = list(df.columns)

    col_map = {key: match_column(columns, aliases) for key, aliases in IBK_COLUMN_ALIASES.items()}
    logger.info(f"IBK 컬럼 매핑: {col_map}")

    # 승인일시 컬럼으로 날짜/시간 분리
    has_datetime = col_map.get("approval_datetime") is not None
    has_date = col_map.get("approval_date") is not None

    if not has_datetime and not has_date:
        msg = f"날짜 관련 컬럼 없음 / 감지된 컬럼: {columns[:10]}"
        return {"records": [], "errors": [{"row": 0, "message": msg}], "total": 0, "success": 0}

    merchant_col = col_map.get("merchant_name")
    amount_col = col_map.get("approval_amount")
    if not merchant_col or not amount_col:
        msg = f"필수 컬럼 없음 (가맹점명/승인금액) / 감지된 컬럼: {columns[:10]}"
        return {"records": [], "errors": [{"row": 0, "message": msg}], "total": 0, "success": 0}

    for idx, row in df.iterrows():
        row_no = int(idx) + header_row + 2
        try:
            card_raw = str(row.get(col_map.get("card_number", ""), "")).strip()
            if not card_raw or card_raw in ("nan", "None"):
                continue

            # 날짜/시간 파싱
            if has_datetime:
                dt_raw = str(row.get(col_map["approval_datetime"], "")).strip()
                date_str, time_str = _split_datetime(dt_raw)
            else:
                date_str = normalize_date(row.get(col_map["approval_date"]))
                time_col = col_map.get("approval_time")
                time_str = normalize_time(row.get(time_col)) if time_col else None

            approval_dt = f"{date_str} {time_str}" if date_str and time_str else date_str
            yyyymm = extract_yyyymm_from_date(date_str)
            card_last4 = extract_last4(card_raw)
            amount = safe_float(row.get(amount_col))
            merchant = str(row.get(merchant_col, "")).strip()

            cat_col = col_map.get("merchant_category")
            category = str(row.get(cat_col, "")).strip() if cat_col else ""
            if category in ("nan", "None"):
                category = ""

            record = {
                "source_bank": "IBK",
                "use_year_month": yyyymm,
                "approval_date": date_str,
                "approval_time": time_str,
                "approval_datetime": approval_dt,
                "card_number_raw": card_raw,
                "card_last4": card_last4,
                "card_owner_name": None,  # IBK는 마스터에서 보강
                "card_owner_email": None,
                "merchant_name": merchant,
                "merchant_category": category,
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
            logger.warning(f"IBK 파싱 오류 (행 {row_no}): {e}")
            errors.append({"row": row_no, "message": str(e)})

    return {
        "records": records,
        "errors": errors,
        "total": len(records) + len(errors),
        "success": len(records),
    }
