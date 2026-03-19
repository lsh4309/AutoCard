"""파서 공통 유틸리티"""
import logging
import re
from typing import Optional
import pandas as pd

logger = logging.getLogger(__name__)


def extract_last4(card_number: Optional[str]) -> Optional[str]:
    """카드번호에서 끝 4자리 추출"""
    if not card_number:
        return None
    cleaned = re.sub(r"[^0-9*]", "", str(card_number))
    if len(cleaned) >= 4:
        digits_only = re.findall(r"\d", cleaned)
        if len(digits_only) >= 4:
            return "".join(digits_only[-4:])
        # 끝 4자리가 *가 아닌 경우
        return cleaned[-4:]
    return None


def normalize_date(value) -> Optional[str]:
    """다양한 날짜 형식을 YYYY-MM-DD로 정규화"""
    if pd.isna(value) or value is None:
        return None
    s = str(value).strip()
    # 2026.01.30 형식
    m = re.match(r"(\d{4})\.(\d{2})\.(\d{2})", s)
    if m:
        return f"{m.group(1)}-{m.group(2)}-{m.group(3)}"
    # 2026-01-30 형식
    m = re.match(r"(\d{4})-(\d{2})-(\d{2})", s)
    if m:
        return f"{m.group(1)}-{m.group(2)}-{m.group(3)}"
    # 20260130 형식
    m = re.match(r"(\d{4})(\d{2})(\d{2})", s)
    if m:
        return f"{m.group(1)}-{m.group(2)}-{m.group(3)}"
    return s


def normalize_time(value) -> Optional[str]:
    """다양한 시간 형식을 HH:MM:SS로 정규화"""
    if pd.isna(value) or value is None:
        return None
    s = str(value).strip()
    # HH:MM:SS 형식
    m = re.match(r"(\d{2}):(\d{2}):(\d{2})", s)
    if m:
        return f"{m.group(1)}:{m.group(2)}:{m.group(3)}"
    # HHMMSS 형식
    m = re.match(r"(\d{6})$", s)
    if m:
        t = m.group(1)
        return f"{t[:2]}:{t[2:4]}:{t[4:6]}"
    return s


def safe_float(value) -> Optional[float]:
    """안전하게 float 변환"""
    if pd.isna(value) or value is None:
        return None
    try:
        cleaned = re.sub(r"[,\s원]", "", str(value))
        return float(cleaned)
    except (ValueError, TypeError):
        return None


def find_header_row(df: pd.DataFrame, target_columns: list[str], max_rows: int = 10) -> int:
    """헤더 행 위치 자동 탐지"""
    for idx in range(min(max_rows, len(df))):
        row = df.iloc[idx].astype(str).tolist()
        row_str = " ".join(row)
        matches = sum(1 for col in target_columns if col in row_str)
        if matches >= len(target_columns) // 2:
            return idx
    return 0


def match_column(columns: list[str], aliases: list[str]) -> Optional[str]:
    """컬럼명 alias 매칭 (유연한 매핑)"""
    for alias in aliases:
        for col in columns:
            if alias in str(col):
                return col
    return None


def detect_bank_type_from_file(file_path) -> str:
    """엑셀 파일 헤더로 KB/IBK 자동 판별"""
    try:
        raw = pd.read_excel(file_path, header=None, nrows=10, dtype=str)
        for idx in range(min(5, len(raw))):
            row = raw.iloc[idx].astype(str).tolist()
            row_str = " ".join(row)
            if "승인일시" in row_str and "이용가맹점명" in row_str:
                return "IBK"
            if "승인일" in row_str and "가맹점명" in row_str:
                return "KB"
        return "KB"  # 기본
    except Exception:
        return "KB"


def extract_yyyymm_from_date(date_str: Optional[str]) -> Optional[str]:
    """날짜 문자열에서 YYYYMM 추출"""
    if not date_str:
        return None
    m = re.match(r"(\d{4})-?(\d{2})", date_str.replace(".", "-"))
    if m:
        return f"{m.group(1)}{m.group(2)}"
    return None

def normalize_card_number(card_number: Optional[str]) -> Optional[str]:
    """카드번호 정규화 (숫자만 추출, 비교용)"""
    if not card_number:
        return None
    digits = re.findall(r"\d", str(card_number))
    return "".join(digits) if digits else None


def is_full_card_number(card_raw: Optional[str]) -> bool:
    """전체 카드번호인지 (마스킹 * 없음)"""
    if not card_raw:
        return False
    return "*" not in str(card_raw)
    