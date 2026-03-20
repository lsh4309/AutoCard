# 04. 백엔드 API 레퍼런스 (Backend API Reference)

## 1. 문서 목적
실제 코드 기준으로 모든 API 엔드포인트의 역할, 요청/응답 구조, 연결된 화면을 정리합니다.

> FastAPI 자동 문서: 서버 실행 후 `http://localhost:8000/docs` 접속 가능

---

## 2. API 그룹 전체 목록

| 그룹 | prefix | 파일 |
|------|--------|------|
| 페이지 (HTML) | `/` | `routers/pages.py` |
| 업로드 | `/api/uploads` | `routers/api_uploads.py` |
| 거래내역 | `/api/transactions` | `routers/api_transactions.py` |
| 마스터 데이터 | `/api/lookups` | `routers/api_lookups.py` |
| 엑셀 내보내기 | `/api/exports` | `routers/api_exports.py` |
| 메일 | `/api/mail` | `routers/api_mail.py` |

---

## 3. 페이지 API (HTML 렌더링)

| Method | Path | 설명 | 주요 서비스 함수 |
|--------|------|------|-----------------|
| GET | `/` | 업로드 페이지 (index) | - |
| GET | `/upload` | 파일 업로드 화면 | - |
| GET | `/transactions` | 거래내역 조회 화면 | `get_transactions()` |
| GET | `/lookups/cards` | 카드 사용자 관리 화면 | `get_all_card_users()` |
| GET | `/lookups/projects` | 프로젝트 관리 화면 | `get_all_projects()` |
| GET | `/lookups/solutions` | 솔루션 관리 화면 | `get_all_solutions()` |
| GET | `/lookups/accounts` | 계정과목 관리 화면 | `get_all_account_subjects()` |
| GET | `/exports` | 엑셀 생성/발송 화면 | `get_cards_for_export()` |

**쿼리 파라미터 (GET /transactions):**
```
bank=KB|IBK       은행 필터
user_name=홍길동  사용자명 포함 검색
card_number=1234  끝4자리 또는 전체번호
year_month=202601 YYYYMM 형식
mapping_status=mapped|unmapped
page=1            페이지 번호 (기본 1, 페이지당 50건)
```

---

## 4. 업로드 API

### `POST /api/uploads`
- **설명:** 엑셀 파일 업로드, 파싱, 저장 처리 (다중 파일 지원)
- **호출 화면:** `upload.html`
- **요청:** `multipart/form-data` - `files` (복수 파일)
- **응답:**
```json
{
  "status": "ok",
  "success": 42,
  "skipped": 3,
  "total": 45,
  "errors": [
    { "row": 12, "message": "[파일명] 오류 내용" }
  ],
  "files": [
    {
      "original_filename": "202601_KB.xlsx",
      "bank_type": "KB",
      "success": 42,
      "skipped": 3,
      "total": 45,
      "errors": []
    }
  ]
}
```
- **관련 서비스:** `transaction_service.upload_and_save()`
- **검증:** `.xlsx`, `.xls` 확장자만 허용
- **에러 처리:**
  - 비엑셀 파일: errors 배열에 추가 후 계속
  - 중복 데이터: skipped 카운터 증가 (에러로 처리 안 함)
  - DB 오류: `db.rollback()`, errors 배열에 추가

> **이 API는 왜 필요한가?** 엑셀 파일을 서버에서 파싱하여 정형화된 DB에 저장하는 핵심 입력 경로. 여러 파일을 한 번에 처리할 수 있어 KB/IBK 동시 업로드 지원.

---

## 5. 거래내역 API

### `GET /api/transactions`
- **설명:** 거래내역 목록 조회 (페이지네이션)
- **쿼리 파라미터:** `bank`, `user_name`, `card_number`, `year_month`, `mapping_status`, `page`, `page_size`
- **응답:**
```json
{
  "total": 156,
  "page": 1,
  "page_size": 50,
  "items": [
    {
      "id": 1,
      "source_bank": "KB",
      "use_year_month": "202601",
      "approval_date": "2026-01-15",
      "approval_time": "14:32:00",
      "card_number_raw": "9234-****-****-1234",
      "card_last4": "1234",
      "card_owner_name": "홍길동",
      "merchant_name": "스타벅스",
      "approval_amount": 15000.0,
      "project_name": null,
      "mapping_status": "mapped",
      ...
    }
  ]
}
```
- **관련 서비스:** `transaction_service.get_transactions()`

### `POST /api/transactions/remap`
- **설명:** 카드 사용자 마스터 기준으로 미매핑 거래 재매핑
- **요청:** 없음 (Body 불필요)
- **응답:** `{ "status": "ok", "remapped": 5 }`
- **관련 서비스:** `transaction_service.remap_transactions()`

> **이 API는 왜 필요한가?** 파일 업로드 후에 카드 사용자를 뒤늦게 등록한 경우, 이미 저장된 미매핑 거래를 일괄 재처리.

### `DELETE /api/transactions`
- **설명:** 거래내역 전체 삭제 (주의: 되돌릴 수 없음)
- **응답:** `{ "status": "ok", "deleted": 200 }`
- **관련 서비스:** `transaction_service.delete_all_transactions()`

---

## 6. 마스터 데이터 API (Lookups)

### 카드 사용자 (CARD_USERS)

| Method | Path | 설명 |
|--------|------|------|
| GET | `/api/lookups/cards` | 전체 조회 |
| POST | `/api/lookups/cards` | 신규 등록 |
| PUT | `/api/lookups/cards/{card_no}` | 수정 |
| DELETE | `/api/lookups/cards/{card_no}` | 삭제 |

**POST 요청 바디:**
```json
{
  "bank_type": "KB",
  "card_last4": "1234",
  "card_number_full": "9234-1234-5678-1234",
  "user_name": "홍길동",
  "user_email": "hong@company.com",
  "active_yn": true,
  "note": null
}
```

**응답:**
```json
{
  "id": "9234-1234-5678-1234",
  "bank_type": "KB",
  "card_last4": "1234",
  "card_number_full": "9234-1234-5678-1234",
  "user_name": "홍길동",
  "user_email": "hong@company.com",
  "active_yn": true,
  "note": null
}
```

**검증 규칙:**
- 동일 카드번호 중복 등록 시 → HTTP 409 Conflict
- 동일 은행+끝4자리 중복 시 → HTTP 409 Conflict
- 카드번호 4자리 미만 → HTTP 400

---

### 프로젝트 (PROJECTS)

| Method | Path | 설명 |
|--------|------|------|
| GET | `/api/lookups/projects` | 전체 조회 |
| POST | `/api/lookups/projects` | 등록 |
| PUT | `/api/lookups/projects/{name}` | 수정 |
| DELETE | `/api/lookups/projects/{name}` | 삭제 |
| POST | `/api/lookups/projects/reorder` | 순서 변경 |

**reorder 요청:**
```json
{ "ordered_ids": ["프로젝트A", "프로젝트C", "프로젝트B"] }
```

---

### 솔루션 (SOLUTIONS)

| Method | Path | 설명 |
|--------|------|------|
| GET | `/api/lookups/solutions` | 전체 조회 |
| POST | `/api/lookups/solutions` | 등록 |
| PUT | `/api/lookups/solutions/{sid}` | 수정 (id=int) |
| DELETE | `/api/lookups/solutions/{sid}` | 삭제 |
| POST | `/api/lookups/solutions/reorder` | 순서 변경 |

---

### 계정과목 (EXPENSE_CATEGORIES)

| Method | Path | 설명 |
|--------|------|------|
| GET | `/api/lookups/accounts` | 전체 조회 |
| POST | `/api/lookups/accounts` | 등록 |
| PUT | `/api/lookups/accounts/{name}` | 수정 |
| DELETE | `/api/lookups/accounts/{name}` | 삭제 |
| POST | `/api/lookups/accounts/reorder` | 순서 변경 |

> **이 API들은 왜 필요한가?** 결과 엑셀 파일의 드롭다운 목록 데이터 소스 관리. 마스터 데이터를 화면에서 직접 관리하므로 코드 수정 없이 목록 변경 가능.

---

## 7. 엑셀 내보내기 API

### `POST /api/exports/generate`
- **설명:** 카드 단건 엑셀 파일 생성
- **호출 화면:** `exports.html` - "엑셀 다운" 버튼
- **요청:**
```json
{
  "card_number": "9234-1234-5678-1234",
  "bank": "KB",
  "year_month": "202601",
  "user_name": "홍길동"
}
```
- **응답:** `{ "status": "ok", "file_name": "홍길동 202601(KB).xlsx" }`
- **관련 서비스:** `excel_export_service.generate_card_excel()`

### `GET /api/exports/download/{file_name}`
- **설명:** 생성된 엑셀 파일 다운로드
- **응답:** 파일 스트림 (application/xlsx)
- **에러:** 파일 없음 → HTTP 404

### `POST /api/exports/download-all-zip`
- **설명:** 여러 카드 엑셀을 한 번에 ZIP으로 다운로드
- **요청:**
```json
{
  "cards": [
    { "card_number": "...", "bank": "KB", "year_month": "202601", "user_name": "홍길동" },
    { "card_number": "...", "bank": "IBK", "year_month": "202601", "user_name": "김철수" }
  ]
}
```
- **응답:** ZIP 파일 스트림 (`card_exports_{year_month}.zip`)
- **파일명 중복 처리:** 동일 파일명 발생 시 `_1`, `_2` 접미사 추가

### `GET /api/exports/cards`
- **설명:** 내보내기 대상 카드 목록 조회 (year_month 필터)
- **응답:** 카드 목록 배열

> **이 API들은 왜 필요한가?** 결과 엑셀 파일은 DB 데이터 + 마스터 목록을 조합해 서버에서 동적 생성. 드롭다운 포함, 서식 지정 등 복잡한 엑셀 구성을 서버에서 처리.

---

## 8. 메일 API

### `GET /api/mail/auth/status`
- **설명:** Outlook 인증 상태 확인 (프론트엔드 폴링용)
- **응답:**
```json
{
  "status": "idle|pending|done|error",
  "message": "인증 대기 중...",
  "verification_url": "https://microsoft.com/devicelogin",
  "user_code": "ABCD1234",
  "has_token": false
}
```

### `POST /api/mail/auth/start`
- **설명:** Device Code 인증 시작
- **응답:** 위와 동일 (status='pending', user_code, verification_url 포함)
- **이미 인증된 경우:** `{ "status": "done", "has_token": true }`

### `POST /api/mail/send`
- **설명:** 카드 목록에 대해 메일 일괄 발송
- **요청:**
```json
{
  "year_month": "202601",
  "cards": null
}
```
> `cards`가 `null`이면 `year_month` 기준 전체 발송 대상 조회

또는 특정 카드만 발송:
```json
{
  "year_month": null,
  "cards": [
    {
      "card_number": "...",
      "bank": "KB",
      "year_month": "202601",
      "user_name": "홍길동",
      "user_email": "hong@company.com"
    }
  ]
}
```
- **응답:**
```json
{
  "status": "ok",
  "sent": 8,
  "failed": 1,
  "skipped": 2,
  "details": [
    {
      "user_name": "홍길동",
      "to": "hong@company.com",
      "file_name": "홍길동 202601(KB).xlsx",
      "status": "sent",
      "error": ""
    },
    {
      "user_name": "박민지",
      "to": "",
      "file_name": "",
      "status": "skipped",
      "error": "이메일 주소 없음"
    }
  ]
}
```
- **에러:**
  - 미인증: HTTP 401
  - 발송 대상 없음: HTTP 404

> **이 API는 왜 필요한가?** 관리자가 버튼 하나로 전체 카드 사용자에게 Outlook 이메일 자동 발송. Microsoft Graph API를 백엔드에서 처리하여 토큰 관리 복잡성을 숨김.

---

## 9. 화면과 API 연결 관계

| 화면 (URL) | 사용하는 API |
|------------|-------------|
| `/upload` | POST `/api/uploads` |
| `/transactions` | GET `/api/transactions/remap`, DELETE `/api/transactions` |
| `/exports` | POST `/api/exports/generate`, GET `/api/exports/download/{file}`, POST `/api/exports/download-all-zip`, GET `/api/mail/auth/status`, POST `/api/mail/auth/start`, POST `/api/mail/send` |
| `/lookups/cards` | GET/POST/PUT/DELETE `/api/lookups/cards` |
| `/lookups/projects` | GET/POST/PUT/DELETE/POST(reorder) `/api/lookups/projects` |
| `/lookups/solutions` | GET/POST/PUT/DELETE/POST(reorder) `/api/lookups/solutions` |
| `/lookups/accounts` | GET/POST/PUT/DELETE/POST(reorder) `/api/lookups/accounts` |

---

## 10. 인증/권한/검증

| API | 인증/검증 |
|-----|-----------|
| 모든 API | 별도 로그인 인증 없음 (사내 내부 도구) |
| POST `/api/uploads` | 파일 확장자 검증 (.xlsx/.xls) |
| POST `/api/lookups/cards` | 중복 카드번호 사전 조회 후 409 |
| POST `/api/mail/send` | Outlook 토큰 존재 여부 확인 (401) |
| GET `/api/exports/download/{file}` | 파일 존재 여부 확인 (404) |

> **주의:** 현재 사용자 인증(로그인) 기능이 없습니다. 사내 네트워크 내부 용도로만 사용 가정.

---

## 11. 질문받기 쉬운 포인트

- **Q: API 문서는 어디서 볼 수 있나요?**  
  → FastAPI 자동 생성 문서: `http://localhost:8000/docs` (Swagger UI)

- **Q: 외부에서 접근 가능한가요?**  
  → 현재 코드상 별도 인증 없음. 배포 시 네트워크 접근 제어 필요.

- **Q: 새 은행을 추가하려면 어떤 API가 바뀌나요?**  
  → `POST /api/uploads`에서 호출하는 `detect_bank_type_from_file()`과 신규 parser 파일 추가 필요. API 자체 변경은 불필요.
