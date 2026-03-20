# 08. 파일 파싱 및 매핑 로직 (Batch Parsing & Mapping)

## 1. 문서 목적
업로드된 엑셀 파일을 읽고, 정제하고, 카드 사용자를 매핑하는 핵심 로직을 설명합니다.  
이 로직은 시스템의 핵심이며, 새 은행 추가나 파일 형식 변경 시 반드시 수정이 필요한 영역입니다.

---

## 2. 핵심 요약

```
[엑셀 파일 업로드]
    ↓
[은행 자동 판별]     detect_bank_type_from_file()
    ↓
[파일 파싱]          parse_kb_file() / parse_ibk_file()
    │                 헤더 자동 탐지, 컬럼 alias 매핑, 데이터 정규화
    ↓
[사용자 매핑]        _build_card_lookups() + 매핑 로직
    │                 전체번호 → 끝4자리 순서로 CARD_USERS 대조
    ↓
[DB 저장]            savepoint 트랜잭션, 중복 자동 skip
```

---

## 3. 입력 파일 형식

### KB 국민카드 엑셀
- **파일 특징:** 상단에 헤더가 아닌 메타 정보 몇 행이 있을 수 있음
- **헤더 식별 키워드:** `승인일`, `카드번호`, `가맹점명`
- **컬럼 구조:**

| 실제 컬럼명 | alias | 매핑 필드 |
|------------|-------|-----------|
| 승인일 / 거래일 / 이용일 | approval_date | approval_date |
| 승인시간 / 거래시간 | approval_time | approval_time |
| 카드번호 | card_number | card_number_raw |
| 이용자명 / 이용자 | user_name | card_owner_name (임시) |
| 가맹점명 / 가맹점 | merchant_name | merchant_name |
| 승인금액 / 이용금액 | approval_amount | approval_amount |

- **날짜 형식:** `2026.01.30` 또는 `2026-01-30`
- **시간 형식:** `HH:MM:SS`
- **카드번호:** 전체번호 또는 마스킹 번호 혼재 가능

### IBK 기업은행 엑셀
- **파일 특징:** 보통 상단 2~3행에 메타 정보
- **헤더 식별 키워드:** `승인일시`, `카드번호`, `이용가맹점명`
- **컬럼 구조:**

| 실제 컬럼명 | alias | 매핑 필드 |
|------------|-------|-----------|
| 승인일시 / 이용일시 | approval_datetime | approval_date + approval_time (분리) |
| 카드번호 | card_number | card_number_raw |
| 이용가맹점명 / 가맹점명 | merchant_name | merchant_name |
| 승인금액 / 이용금액 | approval_amount | approval_amount |

- **날짜+시간 형식:** `2026-01-30 18:06:52` (한 컬럼에 합쳐서)
- **이용자명 컬럼 없음** → 마스터에서 매핑으로 보강

---

## 4. 파싱 로직 위치 및 흐름

### 은행 자동 판별
**파일:** `app/parsers/common.py: detect_bank_type_from_file()`

```python
raw = pd.read_excel(file_path, header=None, nrows=10, dtype=str)
for idx in range(min(5, len(raw))):
    row_str = " ".join(raw.iloc[idx].astype(str).tolist())
    if "승인일시" in row_str and "이용가맹점명" in row_str:
        return "IBK"
    if "승인일" in row_str and "가맹점명" in row_str:
        return "KB"
return "KB"  # 기본값
```

- 상위 5행만 검사 (성능 최적화)
- IBK를 먼저 검사 (KB보다 구체적인 키워드)
- 판별 불가 시 KB 반환

### 헤더 행 자동 탐지
**파일:** `app/parsers/common.py: find_header_row()`

```python
def find_header_row(df, target_columns, max_rows=10):
    for idx in range(min(max_rows, len(df))):
        row_str = " ".join(df.iloc[idx].astype(str).tolist())
        matches = sum(1 for col in target_columns if col in row_str)
        if matches >= len(target_columns) // 2:  # 절반 이상 매칭
            return idx
    return 0  # 기본 0행
```

- 상위 10행에서 타겟 컬럼명 중 절반 이상 매칭하는 행을 헤더로 인식
- 엑셀 파일 상단에 타이틀/주석 행이 있어도 자동 처리

### 컬럼 alias 매핑
**파일:** `app/parsers/common.py: match_column()`

```python
KB_COLUMN_ALIASES = {
    "approval_date": ["승인일", "거래일", "이용일"],
    "card_number":   ["카드번호"],
    "merchant_name": ["가맹점명", "가맹점", "이용가맹점"],
    ...
}

# 실제 컬럼명과 alias 목록 비교 (포함 관계)
for alias in aliases:
    for col in actual_columns:
        if alias in str(col):  # 부분 일치
            return col
```

- 은행별로 별도 alias 딕셔너리 정의
- 부분 문자열 매칭 → 컬럼명에 공백/특수문자 포함해도 처리 가능

---

## 5. 데이터 정규화 규칙

### 날짜 정규화 (`normalize_date()`)
```
입력                 출력
2026.01.30      →   2026-01-30
2026-01-30      →   2026-01-30
20260130        →   2026-01-30
```

### 시간 정규화 (`normalize_time()`)
```
입력         출력
14:32:00  →  14:32:00
143200    →  14:32:00
```

### 카드번호 정규화 (`normalize_card_number()`)
```
입력                      출력
9234-1234-5678-1234  →   9234123456781234
9234 1234 5678 1234  →   9234123456781234
9234****56781234     →   9234123456781234 (※ 잘못된 번호가 될 수 있음)
```
> 숫자만 추출. `*`도 제거됨 → 전체번호로 판별 시 별도 `is_full_card_number()` 사용

### 끝4자리 추출 (`extract_last4()`)
```
9234-1234-5678-1234  →  1234
9234-****-****-1234  →  1234 (마스킹 처리)
```

### 마스킹 여부 판별 (`is_full_card_number()`)
```python
def is_full_card_number(card_raw):
    return "*" not in str(card_raw)  # * 없으면 전체번호
```

### 금액 정규화 (`safe_float()`)
```
"15,000"   →  15000.0
"15,000원" →  15000.0
NaN        →  None
```

---

## 6. 카드 사용자 매핑 로직

**파일:** `app/services/transaction_service.py`

### 매핑 전략 (2단계 폴백)

```
1단계: 전체 카드번호 매칭
  - card_number_raw에 '*' 없음 (is_full_card_number 확인)
  - normalize_card_number(card_raw) → 정규화
  - full_lookup[(normalized, bank_type)] 조회
  ↓ 실패 시
2단계: 끝 4자리 매칭
  - card_last4가 있으면
  - last4_lookup[(card_last4, bank_type)] 조회
  ↓ 실패 시
→ mapping_status = 'unmapped'
```

### N+1 방지 설계

```python
# 업로드 처리 전 1회만 DB 조회
full_lookup, last4_lookup = _build_card_lookups(db)

# 각 레코드 처리: DB 조회 없이 딕셔너리 룩업만 수행
for rec in records:
    user = full_lookup.get((normalized, bank_type))
    if not user:
        user = last4_lookup.get((last4, bank_type))
```

수백 건의 레코드를 처리할 때도 CARD_USERS 조회는 단 1회.

### 은행 코드를 매핑 키에 포함하는 이유

```python
key = (card_last4, bank_type)   # ('1234', 'KB') vs ('1234', 'IBK')
```

서로 다른 은행의 끝4자리가 우연히 같을 수 있음.  
은행 코드를 함께 키로 사용해 충돌 방지.

---

## 7. 오류 처리 방식

### 파싱 단계 오류

| 상황 | 처리 |
|------|------|
| 파일 읽기 실패 | `{"records": [], "errors": [{"row": 0, "message": "파일 읽기 실패: ..."}]}` |
| 필수 컬럼 없음 | `{"records": [], "errors": [{"row": 0, "message": "필수 컬럼 없음: ..."}]}` |
| 개별 행 파싱 오류 | `errors.append({"row": row_no, "message": str(e)})`, 해당 행만 건너뜀 |
| 빈 행 | `continue` (카드번호 없는 행 자동 스킵) |

### 저장 단계 오류

| 상황 | 처리 |
|------|------|
| 중복 거래 (UniqueViolation) | `savepoint.rollback()`, `skipped += 1` |
| 기타 DB 오류 | `savepoint.rollback()`, `errors.append(...)` |
| 알 수 없는 은행 타입 | 즉시 에러 반환 `{"success": 0, ...}` |

---

## 8. KB vs IBK 파서 차이점 정리

| 항목 | KB 파서 | IBK 파서 |
|------|---------|---------|
| 파일: `kb_parser.py` | `ibk_parser.py` | |
| 날짜/시간 컬럼 | 각각 별도 컬럼 | 하나의 "승인일시" 컬럼에 합쳐서 제공 |
| 날짜/시간 분리 | 불필요 | `_split_datetime()` 함수로 분리 |
| 이용자명 | 컬럼 있음 (매핑 보강에 사용) | 없음 (마스터에서 보강) |
| 헤더 탐지 키워드 | `["승인일", "카드번호", "가맹점명"]` | `["승인일시", "카드번호", "이용가맹점명"]` |
| 기본 source_bank | `"KB"` | `"IBK"` |

---

## 9. 새 은행/양식 추가 시 수정 포인트

새 은행(예: 신한카드)을 추가하려면 다음 파일을 수정/추가해야 합니다:

1. **`app/parsers/shinhan_parser.py`** 신규 생성
   - alias 딕셔너리 정의
   - `parse_shinhan_file()` 함수 구현

2. **`app/parsers/common.py: detect_bank_type_from_file()`**
   - 신한 파일 헤더 키워드 추가

3. **`app/services/transaction_service.py: upload_and_save()`**
   - `elif bank_type == "SHINHAN": result = parse_shinhan_file(...)` 추가

> **API 변경 불필요:** `POST /api/uploads`는 변경 없음. 프론트엔드 변경도 최소화.

---

## 10. 이 로직이 실무적으로 왜 중요한가

### 1. 업무 자동화의 핵심
수작업으로 수백 건의 카드 내역을 담당자에게 맞게 분류하는 작업을 자동화.  
매월 반복되는 업무이므로 파싱 정확도가 직접적인 업무 효율에 영향.

### 2. 은행 파일 형식 변경에 취약
KB/IBK가 엑셀 파일 형식을 변경하면 파싱 실패.  
`find_header_row()`와 alias 매핑으로 어느 정도 유연성을 갖추었으나, 컬럼명이 완전히 바뀌면 수동 수정 필요.

### 3. 카드번호 매칭 정확도
마스킹 카드번호(9234-****-****-1234)는 끝4자리로만 매칭 → 같은 은행 내 끝4자리 충돌 가능성.  
전체번호 등록을 권장하는 이유.

### 4. 중복 방지 설계
같은 파일을 실수로 두 번 업로드해도 유니크 제약으로 중복 저장 차단.  
운영상 안전망 역할.

---

## 11. 질문받기 쉬운 포인트

- **Q: 왜 은행 파일마다 파서가 다른가요?**  
  → KB와 IBK의 엑셀 컬럼 구조(특히 날짜/시간)가 다르기 때문.

- **Q: 은행 파일 형식이 바뀌면 어떻게 되나요?**  
  → 파서가 오류를 반환하거나 컬럼 매핑이 실패. 개발자가 alias 추가/수정 필요.

- **Q: 동일인이 KB와 IBK 카드를 모두 쓰면?**  
  → 두 개의 CARD_USERS 레코드 (bank_type='KB', bank_type='IBK')를 각각 등록하면 됨.

- **Q: 카드번호 마스킹된 파일도 처리 가능한가요?**  
  → 가능. 끝4자리(+ 은행)로 매칭. 단, 같은 은행에서 끝4자리 중복 시 첫 번째 결과로 매핑.

---

## 12. 확인 필요 사항

- IBK 파서에서 날짜/시간 정규식 `r"(\d{4}[-./]\d{2}[-./]\d{2})\s+(\d{2}:\d{2}:\d{2})"` → 다른 날짜 형식(예: `2026년 1월 30일`) 불가
- `detect_bank_type_from_file()`: "승인일" 키워드가 IBK 파일에도 있을 경우 오판 가능 (IBK 먼저 체크로 방어 중)
- KB 파서에서 이용자명 컬럼을 `card_owner_name`에 임시 저장하나, 이후 마스터 매핑에서 덮어써짐 → 원본 파일의 이용자명이 최종 결과에 반영되지 않음
