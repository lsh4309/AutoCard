# Card Auto - 기술 명세서 (Technical Specification)

## 1. 전체 시스템 아키텍처

### 1.1 프로세스 흐름도

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                        Card Auto - 법인카드 승인내역 처리 흐름                      │
└─────────────────────────────────────────────────────────────────────────────────┘

  [1] 파일 업로드              [2] 파싱                    [3] 카드 마스터 매핑
  ┌──────────────┐           ┌──────────────┐            ┌──────────────────────┐
  │ KB/IBK       │           │ detect_bank   │            │ _build_card_lookups  │
  │ 엑셀 업로드   │ ────────► │ parse_kb/    │ ────────►  │ full_lookup:         │
  │ (.xlsx/.xls) │           │ parse_ibk    │            │   (전체번호, bank)    │
  └──────────────┘           └──────────────┘            │ last4_lookup:        │
         │                            │                  │   (끝4자리, bank)     │
         │                            │                  └──────────┬───────────┘
         │                            │                           │
         │                            ▼                           ▼
         │                   ┌─────────────────┐           ┌──────────────────────┐
         │                   │ 정규화 레코드    │           │ 마스킹 → 전체번호    │
         │                   │ - card_last4    │           │ 변환: card_master    │
         │                   │ - card_number_  │           │ (PostgreSQL) 조회   │
         │                   │   raw           │           └──────────┬───────────┘
         │                   └────────┬────────┘                     │
         │                            │                             │
         │                            ▼                             │
         │                   ┌─────────────────────────────────────────────┐
         │                   │ [4] DB 저장 (SQLite transactions)            │
         │                   │ - card_owner_name, mapping_status 보강      │
         │                   └─────────────────────┬─────────────────────┘
         │                                         │
         │                                         ▼
         │                   ┌─────────────────────────────────────────────┐
         │                   │ [5] 결과 파일 생성 (exports)                  │
         │                   │ - get_cards_for_export (전체번호 기반 그룹)  │
         │                   │ - generate_card_excel (openpyxl)              │
         │                   │ - 파일명: {사용자명} {YYYYMM}({은행}).xlsx   │
         │                   └─────────────────────────────────────────────┘
         │
         └──► POST /api/uploads  (api_uploads.py)
```

### 1.2 데이터베이스 구성

| DB | 용도 | 테이블 |
|----|------|--------|
| **PostgreSQL** | 전체 | `transactions`, `card_master`, `project_master`, `solution_master`, `account_subject_master` |

모든 테이블이 PostgreSQL에서 관리됨. DBeaver에서 `init_pg_masters.sql` 실행 후 화면 사용 가능.

---

## 2. 파일 및 함수별 상세 설명

### 2.1 parsers/ - 파서 모듈

#### 2.1.1 common.py - 공통 유틸리티

| 함수 | 설명 |
|------|------|
| `extract_last4(card_number)` | 카드번호에서 끝 4자리 추출. 숫자만 추출 후 마지막 4자리 반환 |
| `normalize_date(value)` | 다양한 날짜 형식(2026.01.30, 2026-01-30, 20260130) → YYYY-MM-DD |
| `normalize_time(value)` | HH:MM:SS 또는 HHMMSS → HH:MM:SS |
| `safe_float(value)` | 금액 문자열(쉼표, 원 등 포함) → float |
| `find_header_row(df, target_columns)` | 엑셀 헤더 행 자동 탐지 (최대 10행 스캔) |
| `match_column(columns, aliases)` | 컬럼명 alias 유연 매칭 |
| `detect_bank_type_from_file(file_path)` | 엑셀 헤더로 KB/IBK 자동 판별 ("승인일시"+ "이용가맹점명" → IBK, "승인일"+ "가맹점명" → KB) |
| `extract_yyyymm_from_date(date_str)` | 날짜 문자열에서 YYYYMM 추출 |
| `normalize_card_number(card_number)` | 카드번호 정규화 (숫자만 추출, 비교용) |
| `is_full_card_number(card_raw)` | 전체 카드번호 여부 (* 마스킹 없음) |

#### 2.1.2 kb_parser.py - KB 국민은행 파서

**작동 원리:**
1. `find_header_row`로 "승인일", "카드번호", "가맹점명" 포함 행 탐지
2. `KB_COLUMN_ALIASES`로 컬럼 유연 매핑 (승인일/거래일/이용일 등)
3. 행별로 `normalize_date`, `normalize_time`, `extract_last4`, `safe_float` 적용
4. 공통 레코드 형식으로 반환

**정규화 로직:**
- 날짜: `2026.01.30` → `2026-01-30`
- 시간: `180652` → `18:06:52`
- 카드번호: `4265-****-****-0830` → `card_last4="0830"`, `card_number_raw` 원본 유지

#### 2.1.3 ibk_parser.py - IBK 기업은행 파서

**작동 원리:**
1. `find_header_row`로 "승인일시", "카드번호", "이용가맹점명" 포함 행 탐지
2. IBK는 **승인일시** 단일 컬럼 사용 → `_split_datetime`으로 날짜/시간 분리
3. 나머지는 KB와 동일한 정규화 적용

**정규화 로직:**
- `_split_datetime("2026-01-30 18:06:52")` → `("2026-01-30", "18:06:52")`
- IBK는 `card_owner_name`이 없음 → 마스터 매핑 시 보강

---

### 2.2 services/ - 서비스 모듈

#### 2.2.1 transaction_service.py - 거래 내역 서비스

| 함수 | 설명 |
|------|------|
| `_build_card_lookups(db)` | 카드 마스터 1회 조회 후 `full_lookup`, `last4_lookup` 딕셔너리 반환. **N+1 방지** |
| `upload_and_save(db, file_path, bank_type)` | 파일 파싱 → 룩업 매핑 → DB 저장 |
| `delete_all_transactions(db)` | 거래내역 전체 삭제 |
| `get_transactions(db, ...)` | 거래 목록 조회 (필터: bank, user_name, card_number, year_month, mapping_status) |
| `remap_transactions(db)` | 미매핑 거래를 카드 마스터 기준으로 재매핑 |
| `get_cards_for_export(db, year_month)` | 결과 파일 생성 대상 카드 목록 (전체번호 기반 그룹화) |

**전체 카드번호 기반 매칭 로직 (핵심):**

```
1. full_lookup: (정규화된 전체번호 16자리, bank_type) → user
2. last4_lookup: (끝4자리, bank_type) → user

매칭 우선순위:
  - card_number_raw에 * 없음 + 16자리 이상 → full_lookup 먼저 시도
  - 매칭 실패 시 → last4_lookup으로 fallback

get_transactions / _get_transactions_for_card (엑셀 생성 시):
  - card_number가 전체번호(16자리)이면: DB에서 card_last4로 필터 후, 메모리에서 normalize_card_number(tx.card_number_raw) == norm 비교
  - 동일 card_last4를 가진 다른 카드(마스킹 vs 전체번호) 구분 가능
```

#### 2.2.2 master_service.py - 마스터 CRUD

카드 사용자, 프로젝트, 솔루션, 계정과목에 대한 CRUD를 `card_master_service` 및 `repositories`에 위임.

#### 2.2.3 card_master_service.py - 카드 사용자 마스터

PostgreSQL `card_master` 테이블 연동. `CardRepository` 래퍼.

#### 2.2.4 excel_export_service.py - 엑셀 내보내기

| 함수 | 설명 |
|------|------|
| `_get_transactions_for_card(db, card_number, bank, year_month)` | 카드별 거래 목록 (전체번호 기반 필터링) |
| `_build_options_sheet(wb, ...)` | 숨김 시트(meta)에 드롭다운 옵션 저장 |
| `_add_data_validations(ws, ...)` | 프로젝트/솔루션/계정과목/Flex 드롭다운 적용 |
| `generate_card_excel(db, card_number, bank, year_month, user_name)` | 카드 단건 엑셀 생성, 파일 경로 반환 |

**전체번호 기반 그룹화:**
- `card_number`가 16자리 이상이면 `card_last4`로 DB 필터 후, 메모리에서 `normalize_card_number(tx.card_number_raw) == norm` 비교
- 마스킹된 거래는 `last4_lookup`에서 card_master의 `card_no`(전체번호)를 가져와 엑셀에 표시

---

### 2.3 models/ - SQLAlchemy 모델

현재 `app/models/transaction.py`에 Transaction 모델 정의.

#### Transaction (SQLite transactions 테이블)

| 컬럼 | 타입 | 설명 |
|------|------|------|
| id | Integer | PK |
| source_bank | String(10) | KB / IBK |
| use_year_month | String(6) | YYYYMM |
| approval_date | String(10) | YYYY-MM-DD |
| approval_time | String(8) | HH:MM:SS |
| approval_datetime | String(20) | 통합 날짜시간 |
| card_number_raw | String(50) | 원본 카드번호 (마스킹 포함 가능) |
| card_last4 | String(4) | 끝 4자리 (인덱스) |
| card_owner_name | String(50) | 카드 사용자명 (마스터 매핑) |
| card_owner_email | String(100) | 이메일 |
| merchant_name | String(200) | 가맹점명 |
| approval_amount | Float | 승인금액 |
| project_name, solution_name, account_subject | String | 관리자 입력 |
| flex_pre_approved | String(1) | O / X |
| attendees, purchase_detail, remarks | Text | 관리자 입력 |
| mapping_status | String(20) | mapped / unmapped |
| validation_status | String(20) | ok / warning / error |
| upload_batch_id | String(50) | 업로드 배치 식별 |
| created_at, updated_at | DateTime | 자동 |

---

### 2.4 db/ - PostgreSQL 연동 (psycopg2 직접 쿼리)

#### connection.py
- `create_connection()`, `get_pg_conn()`: 연결 생성, 트랜잭션(commit/rollback) 자동 처리

#### base.py
- `PgRepository`: `fetch_all`, `fetch_one`, `execute` 공통화

#### bootstrap.py
- `init_card_master_table()`, `init_master_tables()`, `seed_default_masters()`

#### repositories/card_repository.py
- `CardRepository`: card_master CRUD
- `find_by_card_number`: SQL `WHERE card_no_normalized = %s` (전체 스캔 제거)
- `find_by_last4`: SQL `WHERE card_last4 = %s`
- `card_no_normalized`, `card_last4` 컬럼 및 인덱스 사용

#### repositories/master_repository.py
- `BaseMasterRepository`: 마스터 공통 CRUD
- `ProjectRepository`, `SolutionRepository`, `AccountSubjectRepository`

---

## 3. 주요 데이터 흐름

### 3.1 마스킹된 번호 → 카드 마스터 조회 → 전체 번호 변환

```
[엑셀 원본]
card_number_raw: "4265-****-****-0830"
card_last4: "0830"

[1단계: 파싱]
→ extract_last4() → card_last4 = "0830"
→ card_number_raw 그대로 저장

[2단계: 업로드 시 매핑]
→ _build_card_lookups(db):
   - last4_lookup[("0830", "KB")] = { "card_no": "4265869432870830", "user_name": "윤이현", ... }
→ rec["card_owner_name"] = "윤이현", rec["mapping_status"] = "mapped"

[3단계: 결과 파일 생성 시]
→ get_cards_for_export():
   - tx.card_number_raw가 마스킹(*) 포함
   - last4_lookup.get(("0830", "KB")) → user["card_no"] = "4265869432870830"
   - seen[(bank, "4265869432870830")] = { card_number: "4265869432870830", user_name: "윤이현", ... }

→ generate_card_excel(card_number="4265869432870830", ...):
   - _get_transactions_for_card: card_last4="0830"로 DB 필터
   - 메모리에서 tx.card_last4 == "0830" 인 거래만 반환 (마스킹/전체번호 구분 없이 동일 카드)
   - 엑셀 카드번호 컬럼: card_number(전체번호) 사용 → "4265869432870830" 표시
```

### 3.2 전체 카드번호 기반 그룹화 (동일 끝4자리 여러 카드 구분)

동일 `card_last4`를 가진 카드가 여러 장일 수 있음 (예: 개인카드/법인카드).  
전체 카드번호로 그룹화하여 카드별로 별도 엑셀 생성.

```
거래 A: card_number_raw="4265-8694-3287-0830", card_last4="0830"  → 카드1
거래 B: card_number_raw="4265-****-****-0830", card_last4="0830"  → 카드1 (마스킹)
거래 C: card_number_raw="1234-5678-9012-0830", card_last4="0830"  → 카드2 (다른 카드)

get_cards_for_export 결과:
  - (KB, 4265869432870830): 윤이현, 2건
  - (KB, 1234567890120830): 홍길동, 1건
```

---

## 4. API 및 라우터 구조

| 라우터 | prefix | 주요 엔드포인트 |
|--------|--------|-----------------|
| pages | / | /, /upload, /transactions, /masters/*, /exports |
| api_uploads | /api/uploads | POST "" (파일 업로드) |
| api_transactions | /api/transactions | GET "", POST /remap, DELETE "" |
| api_masters | /api/masters | /cards, /projects, /solutions, /accounts (CRUD) |
| api_exports | /api/exports | POST /generate, GET /download/{fn}, GET /cards |

---

## 5. 설정 및 환경

- `app/core/config.py`: `DATABASE_URL` (PostgreSQL), `UPLOAD_DIR`, `EXPORT_DIR`, `PG_*` 환경변수
- `.env`: PostgreSQL 연결 정보 (PG_HOST, PG_PORT, PG_DATABASE, PG_USER, PG_PASSWORD)
