# 03. 백엔드 파일/함수 단위 역할 (Backend Files & Functions)

## 1. 문서 목적
백엔드 주요 파일과 함수를 단위별로 설명합니다.  
"이 파일이 왜 존재하는지", "어떤 흐름에서 호출되는지"를 중심으로 기술합니다.

---

## 2. 파일별 역할 표

| 파일 | 역할 | 주요 함수/클래스 | 호출 주체 | 비고 |
|------|------|------------------|-----------|------|
| `app/main.py` | 앱 진입점, 라우터 등록 | `app = FastAPI(...)` | uvicorn | 6개 라우터 include |
| `app/core/config.py` | 전역 설정, 경로 관리 | 상수 (변수) | 모든 모듈 | .env 로드 |
| `app/core/database.py` | SQLAlchemy 세션 관리 | `get_db()`, `Base` | 라우터 DI | ORM용 |
| `app/models/transaction.py` | CARD_TRANSACTIONS ORM 모델 | `Transaction` | transaction_service | SQLAlchemy |
| `app/routers/pages.py` | HTML 페이지 렌더링 | 7개 GET 엔드포인트 | 브라우저 | Jinja2 |
| `app/routers/api_uploads.py` | 파일 업로드 처리 | `upload_files()` | upload.html JS | 파일 임시 저장 |
| `app/routers/api_transactions.py` | 거래내역 API | `list_transactions()`, `remap()`, `delete_all()` | transactions.html JS | |
| `app/routers/api_lookups.py` | 마스터 CRUD API | CARD_USERS/PROJECTS/SOLUTIONS/ACCOUNTS | lookups HTML | 4종 마스터 |
| `app/routers/api_exports.py` | 엑셀 생성/다운로드 API | `generate_export()`, `download_file()`, `download_all_as_zip()` | exports.html JS | |
| `app/routers/api_mail.py` | 메일 발송 API | `auth_status()`, `auth_start()`, `send_mails()` | exports.html JS | |
| `app/services/transaction_service.py` | **핵심 서비스** - 업로드/매핑/조회 | `upload_and_save()`, `get_transactions()`, `remap_transactions()`, `get_cards_for_export()` | 라우터 | 가장 복잡한 파일 |
| `app/services/card_user_service.py` | CARD_USERS CRUD | `get_all_card_users()`, `create/update/delete_card_user()` | lookup_service | psycopg2 |
| `app/services/lookup_service.py` | 마스터 서비스 Facade | 모든 마스터 get/create/update/delete | api_lookups.py | Repository 위임 |
| `app/services/excel_export_service.py` | 엑셀 파일 생성 | `generate_card_excel()` | api_exports, mail_service | openpyxl |
| `app/services/mail_service.py` | Outlook 메일 발송 | `start_device_code_auth()`, `is_authenticated()`, `send_card_mails()` | api_mail.py | MSAL |
| `app/parsers/common.py` | 파싱 공통 유틸 | `detect_bank_type_from_file()`, `normalize_date()`, `normalize_card_number()`, `extract_last4()` | kb/ibk_parser, transaction_service | |
| `app/parsers/kb_parser.py` | KB 엑셀 파서 | `parse_kb_file()` | transaction_service | pandas |
| `app/parsers/ibk_parser.py` | IBK 엑셀 파서 | `parse_ibk_file()` | transaction_service | pandas |
| `app/db/connection.py` | psycopg2 연결 관리 | `get_pg_conn()` | PgRepository | 컨텍스트 매니저 |
| `app/db/base.py` | Repository 베이스 | `PgRepository` (fetch_all/fetch_one/execute) | card/lookup_repository | |
| `app/db/bootstrap.py` | 테이블 DDL + 시드 | `init_card_users_table()`, `init_lookup_tables()`, `seed_default_lookups()` | 초기화 스크립트 | 최초 1회 실행 |
| `app/db/repositories/card_repository.py` | CARD_USERS SQL | `CardRepository` | card_user_service | find_by_card_number/last4 포함 |
| `app/db/repositories/lookup_repository.py` | 마스터 테이블 SQL | `ProjectRepository`, `SolutionRepository`, `AccountSubjectRepository` | lookup_service | BaseLookupRepository 공통화 |

---

## 3. 중요 함수 상세 설명

---

### `transaction_service.upload_and_save()`
**파일:** `app/services/transaction_service.py`

- **목적:** 업로드된 파일을 파싱하고 사용자를 매핑한 뒤 DB에 저장
- **호출 위치:** `api_uploads.py: upload_files()`
- **처리 순서:**
  1. `bank_type`에 따라 `parse_kb_file()` 또는 `parse_ibk_file()` 호출
  2. `_build_card_lookups()` → CARD_USERS 1회 조회, 메모리 딕셔너리 생성
  3. 각 레코드에 대해:
     - 전체 카드번호 → `full_lookup[(card_no_normalized, bank)]` 매칭
     - 실패 시 끝4자리 → `last4_lookup[(card_last4, bank)]` 매칭
     - 매핑 성공: `mapping_status='mapped'`, `card_owner_name` 설정
     - 매핑 실패: `mapping_status='unmapped'`
  4. `Transaction` 모델로 INSERT, `savepoint` 트랜잭션
  5. 최종 `db.commit()`
- **반환:** `{ batch_id, success, skipped, total, errors }`
- **예외:** IntegrityError(중복) → skipped, 그 외 → errors 추가
- **리뷰 포인트:** N+1 방지 설계, savepoint 패턴, 중복 처리 방식

---

### `transaction_service._build_card_lookups()`
**파일:** `app/services/transaction_service.py`

- **목적:** CARD_USERS를 1회 조회해 빠른 매핑용 딕셔너리 생성
- **호출 위치:** `upload_and_save()`, `remap_transactions()`, `get_cards_for_export()`
- **처리 순서:**
  1. `get_all_card_users(db)` → 전체 카드 사용자 조회
  2. 각 사용자의 전체 카드번호 정규화 → `full_lookup[(normalized, bank)]`
  3. 끝4자리 추출 → `last4_lookup[(last4, bank)]`
- **반환:** `(full_lookup, last4_lookup)` 튜플
- **리뷰 포인트:** 키가 `(카드번호, 은행)` 튜플 → 은행 다른 동일 끝4자리 구분 가능

---

### `transaction_service.get_transactions()`
**파일:** `app/services/transaction_service.py`

- **목적:** 필터 조건으로 거래내역 페이지네이션 조회
- **호출 위치:** `api_transactions.py`, `pages.py`
- **입력:** bank, user_name, card_number, year_month, mapping_status, page, page_size
- **처리 순서:**
  1. SQLAlchemy 쿼리 빌드 (동적 filter 체이닝)
  2. card_number가 전체번호(16자리)인 경우: last4로 후보 축소 후 메모리 필터
  3. card_number가 끝4자리인 경우: `card_last4 =` 필터
  4. `approval_datetime` 내림차순 정렬, 페이지네이션
- **반환:** `(items: list[Transaction], total: int)`
- **리뷰 포인트:** 전체번호 검색 시 2단계 필터(DB+메모리) 사용 이유 확인 필요

---

### `transaction_service.get_cards_for_export()`
**파일:** `app/services/transaction_service.py`

- **목적:** 결과 파일 생성 대상 카드 목록 집계
- **호출 위치:** `api_exports.py`, `api_mail.py`, `pages.py`
- **처리 순서:**
  1. CARD_USERS 룩업 생성
  2. 전체 거래내역 조회 (year_month 필터 선택)
  3. 카드번호/은행 조합 기준으로 중복 제거 (seen dict)
  4. 각 카드별 거래 건수 집계
  5. 마스터에서 이메일 보강
- **반환:** `[{ bank, card_number, user_name, user_email, year_month, total }]`

---

### `parsers/common.detect_bank_type_from_file()`
**파일:** `app/parsers/common.py`

- **목적:** 엑셀 파일 헤더로 KB/IBK 자동 판별
- **호출 위치:** `api_uploads.py: upload_files()`
- **처리 순서:**
  1. `pd.read_excel()` 상위 10행 읽기
  2. 각 행을 문자열로 변환
  3. "승인일시" + "이용가맹점명" → IBK
  4. "승인일" + "가맹점명" → KB
  5. 판별 불가 시 기본값 "KB"
- **리뷰 포인트:** 새 은행 추가 시 이 함수 수정 필요

---

### `parsers/kb_parser.parse_kb_file()`
**파일:** `app/parsers/kb_parser.py`

- **목적:** KB 엑셀 파일을 파싱해 레코드 리스트 반환
- **호출 위치:** `transaction_service.upload_and_save()`
- **처리 순서:**
  1. `pd.read_excel()` 전체 읽기
  2. `find_header_row()` → 헤더 행 위치 자동 탐지
  3. 컬럼 alias 매핑 (`KB_COLUMN_ALIASES` dict 사용)
  4. 필수 컬럼 누락 검증
  5. 각 행: 날짜/시간 정규화, 카드번호 추출, 금액 변환
  6. record dict 생성 (`source_bank='KB'`, `mapping_status='unmapped'`)
- **반환:** `{ records, errors, total, success }`
- **리뷰 포인트:** 헤더 자동 탐지로 파일 형식 변경에 어느 정도 유연 대응

---

### `parsers/ibk_parser.parse_ibk_file()`
**파일:** `app/parsers/ibk_parser.py`

- **목적:** IBK 엑셀 파일 파싱 (KB와 구조 유사하나 날짜 처리 다름)
- **KB 대비 차이점:**
  - IBK는 날짜+시간이 "승인일시" 한 컬럼에 합쳐서 제공 → `_split_datetime()`으로 분리
  - IBK는 이용자명 컬럼 없음 → `card_owner_name=None` (마스터에서 보강)
- **리뷰 포인트:** `_split_datetime()` 정규식이 포맷 변경에 취약할 수 있음

---

### `excel_export_service.generate_card_excel()`
**파일:** `app/services/excel_export_service.py`

- **목적:** 특정 카드의 거래내역을 담은 엑셀 파일 생성
- **호출 위치:** `api_exports.py`, `mail_service.send_card_mails()`
- **처리 순서:**
  1. 해당 카드의 거래내역 DB 조회
  2. 활성 프로젝트/솔루션/계정과목 목록 조회
  3. openpyxl 워크북 생성
  4. 숨김 시트 'meta'에 드롭다운 옵션 저장
  5. '내역' 시트에 헤더 작성 (파란색 배경, 흰색 글자)
  6. 각 행 데이터 작성 (입력 필요 컬럼 노란색 배경)
  7. 드롭다운 유효성 검사 추가 (프로젝트/솔루션/계정과목/Flex)
  8. 컬럼 너비 고정, 틀 고정
  9. `exports/{user_name} {yyyymm}({bank}).xlsx` 저장
- **반환:** `Path` 객체 (저장된 파일 경로)
- **리뷰 포인트:** 동일 파일 재생성 시 덮어쓰기 (별도 버전관리 없음)

---

### `mail_service.start_device_code_auth()`
**파일:** `app/services/mail_service.py`

- **목적:** Microsoft MSAL Device Code Flow 인증 시작
- **호출 위치:** `api_mail.py: auth_start()`
- **처리 순서:**
  1. `_auth_state['status'] == 'pending'` 체크 (중복 실행 방지)
  2. 백그라운드 스레드에서 MSAL 인증 실행
  3. `app.initiate_device_flow()` → user_code, verification_uri 획득
  4. `_auth_state` 업데이트 (스레드 간 공유, Lock 사용)
  5. `app.acquire_token_by_device_flow()` → 최대 15분 대기
  6. 성공 시 토큰 파일 저장, `status='done'`
- **반환:** `{ status, verification_url, user_code, message }`
- **리뷰 포인트:** `_auth_state`가 모듈 수준 전역 변수 → 단일 프로세스 가정

---

### `mail_service.send_card_mails()`
**파일:** `app/services/mail_service.py`

- **목적:** 카드 목록에 대해 엑셀 생성 + 메일 발송
- **호출 위치:** `api_mail.py: send_mails()`
- **처리 순서:**
  1. `_get_token_silent()` → 저장 토큰으로 자동 갱신
  2. 토큰 없으면 `PermissionError`
  3. 각 카드에 대해:
     - `user_email` 없으면 skipped
     - `generate_card_excel()` 호출
     - `_build_mail_body()` HTML 메일 본문 생성
     - `_send_graph_mail()` → Microsoft Graph API로 발송
- **반환:** `[{ user_name, to, file_name, status, error }]`
- **예외:** 개별 발송 실패는 `status='failed'`로 기록, 전체 진행 계속

---

### `db/base.PgRepository`
**파일:** `app/db/base.py`

- **목적:** psycopg2 SQL 실행 공통화 (베이스 클래스)
- **주요 메서드:**
  - `fetch_all(sql, params)` → 전체 결과 `list[dict]` 반환
  - `fetch_one(sql, params)` → 단건 `dict | None` 반환
  - `execute(sql, params)` → INSERT/UPDATE/DELETE 실행, rowcount 반환
- **리뷰 포인트:** `conn_provider` 주입으로 테스트 시 mock 가능한 설계

---

### `db/repositories/lookup_repository.BaseLookupRepository`
**파일:** `app/db/repositories/lookup_repository.py`

- **목적:** PROJECTS, SOLUTIONS, EXPENSE_CATEGORIES 공통 CRUD 추상화
- **공통 기능:** get_all, create, update, delete, get_max_sort_order, reorder_keys
- **서브클래스:** `ProjectRepository`, `SolutionRepository`, `AccountSubjectRepository`
- **리뷰 포인트:** `table_name`, `key_field`, `select_fields`만 다르게 설정해 중복 코드 제거

---

## 4. 함수 호출 관계 요약

```
api_uploads.upload_files()
  └─ detect_bank_type_from_file()        [parsers/common.py]
  └─ transaction_service.upload_and_save()
       ├─ parse_kb_file() or parse_ibk_file()
       │    └─ find_header_row(), match_column(), normalize_date() ...
       ├─ _build_card_lookups()
       │    └─ get_all_card_users()
       └─ Transaction INSERT (SQLAlchemy)

api_exports.generate_export()
  └─ excel_export_service.generate_card_excel()
       ├─ _get_transactions_for_card()   [SQLAlchemy 조회]
       ├─ get_all_projects/solutions/accounts()
       └─ openpyxl 워크북 생성

api_mail.send_mails()
  └─ mail_service.send_card_mails()
       ├─ generate_card_excel()          [excel_export_service]
       └─ _send_graph_mail()             [MS Graph API]

api_lookups.create_card_user()
  └─ lookup_service.create_card_user()
       └─ card_user_service.create_card_user()
            └─ CardRepository.create()   [psycopg2]
```

---

## 5. 확인 필요 사항

- `app/db/repositories/master_repository.py`는 `lookup_repository.py`와 구조가 동일함 → 이름이 다른 두 파일이 같은 Repository 클래스를 정의 중. `lookup_service.py`는 `lookup_repository`를 import하지만 `master_repository`는 `lookup_service`에서 미사용 상태로 보임
- `Transaction` 모델에 `validation_status`, `validation_message` 컬럼이 없으나, 파서 레코드에는 해당 필드가 생성됨 → `Transaction.__table__.columns`로 필터링되어 저장 시 무시됨 (정상 동작이나 혼동 가능)
