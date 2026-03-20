# 10. 임원/상무님 질문 대응 가이드 (Executive Q&A Guide)

## 1. 문서 목적
임원 또는 비개발자 보고 시 자주 받는 질문에 대한 답변을 준비합니다.  
"짧은 답변" + "기술적으로는" 구분으로 상황에 맞게 활용하세요.

---

## 전체 시스템 이해

---

### Q1. 이 프로그램은 전체적으로 어떤 역할을 하나요?

**짧은 답변:**  
KB와 IBK 법인카드 승인내역 엑셀을 올리면, 담당자별로 자동 분류해서 엑셀 파일로 만들고 Outlook으로 자동 발송해주는 사내 관리 도구입니다.

**기술적으로는:**  
FastAPI(Python) 기반 웹 애플리케이션. pandas로 엑셀 파싱, PostgreSQL에 저장, openpyxl로 결과 엑셀 생성, Microsoft Graph API로 Outlook 발송.

**관련 파일:** `app/main.py`, `app/core/config.py`

---

### Q2. 이 프로그램을 만든 이유가 뭔가요?

**짧은 답변:**  
매월 반복되는 법인카드 내역 정리 작업(수작업 분류 → 개인별 파일 → 이메일 발송)을 자동화해서 업무 시간을 절감하기 위해 만들었습니다.

**기술적으로는:**  
수작업 대비 파일 분류 정확도 향상, 인적 오류 감소, 월별 반복 업무 자동화.

---

### Q3. 누가 이 프로그램을 사용하나요?

**짧은 답변:**  
법인카드 관리 업무를 담당하는 경영지원 담당자.

**기술적으로는:**  
별도 로그인 없음. 사내 네트워크에서 브라우저로 접속. 관리자 기능(업로드, 마스터 관리, 메일 발송)만 존재.

---

### Q4. 어떻게 실행하나요? 설치가 필요한가요?

**짧은 답변:**  
서버에서 프로그램을 실행해두면, 사용자는 브라우저 주소만 입력하면 됩니다.

**기술적으로는:**  
`uvicorn app.main:app` 명령으로 서버 실행. 사용자는 `http://서버주소:8000`으로 접속. Python 패키지 설치는 서버에 한 번만 필요.

---

## 업무 흐름

---

### Q5. 파일 업로드 후 어떤 처리가 이루어지나요?

**짧은 답변:**  
엑셀을 올리면 ① 은행 자동 판별 ② 거래내역 읽기 ③ 카드번호로 담당자 자동 연결 ④ DB 저장 순으로 처리됩니다.

**기술적으로는:**  
파일 헤더 키워드로 KB/IBK 판별 → pandas로 파싱 → 카드 마스터 1회 조회 후 메모리 매핑 → SQLAlchemy로 INSERT (중복 시 자동 스킵).

**관련 파일:** `app/routers/api_uploads.py`, `app/services/transaction_service.py`, `app/parsers/kb_parser.py`, `app/parsers/ibk_parser.py`

---

### Q6. KB와 IBK 파일을 어떻게 구분하나요?

**짧은 답변:**  
파일을 자동으로 읽어서 안에 있는 컬럼명을 보고 판단합니다. 사용자가 직접 선택할 필요 없습니다.

**기술적으로는:**  
엑셀 상위 5행에서 "승인일시 + 이용가맹점명" 있으면 IBK, "승인일 + 가맹점명" 있으면 KB로 판별. 기본값은 KB.

**관련 파일:** `app/parsers/common.py: detect_bank_type_from_file()`

---

### Q7. 카드번호와 담당자 이름은 어떻게 연결되나요?

**짧은 답변:**  
"카드 사용자" 메뉴에서 미리 카드번호와 담당자 이름을 등록해두면, 업로드 시 자동으로 연결됩니다.

**기술적으로는:**  
CARD_USERS 테이블에 `card_no`, `user_name`, `bank_type` 저장. 업로드 시 거래내역의 카드번호를 전체번호→끝4자리 순으로 대조 매핑.

**관련 파일:** `app/services/transaction_service.py: _build_card_lookups()`

---

### Q8. 같은 파일을 두 번 올리면 어떻게 되나요?

**짧은 답변:**  
중복된 내역은 자동으로 걸러지고, 화면에 "중복 스킵" 건수로 표시됩니다. 데이터가 2번 들어가지 않습니다.

**기술적으로는:**  
DB에 유니크 제약 `(source_bank, approval_datetime, card_number_raw, merchant_name, approval_amount)` 설정. 중복 시 IntegrityError → skipped 카운터 증가.

**관련 파일:** `scripts/sql/init_schema.sql`, `app/services/transaction_service.py`

---

### Q9. 결과 파일은 어떻게 생성되나요?

**짧은 답변:**  
"결과 파일 생성" 메뉴에서 버튼을 누르면, 해당 담당자의 거래내역이 담긴 엑셀 파일이 바로 생성되어 다운로드됩니다.

**기술적으로는:**  
openpyxl로 엑셀 생성. 헤더는 파란색, 입력 필요 컬럼은 노란색. 프로젝트/솔루션/계정과목 드롭다운 포함. 파일명: `{사용자명} {YYYYMM}({은행}).xlsx`

**관련 파일:** `app/services/excel_export_service.py: generate_card_excel()`

---

### Q10. 이메일 발송은 어떻게 작동하나요?

**짧은 답변:**  
버튼 하나로 전체 담당자에게 각자의 카드 내역 파일을 Outlook으로 자동 발송합니다. 처음 1회만 로그인하면 이후엔 자동입니다.

**기술적으로는:**  
Microsoft Graph API (Device Code Flow). 서버에서 user_code 발급 → 사용자가 브라우저에서 코드 입력 → 토큰 파일로 저장 → 이후 자동 갱신.

**관련 파일:** `app/services/mail_service.py`, `app/routers/api_mail.py`

---

## 데이터 및 저장

---

### Q11. 데이터는 어디에 저장되나요?

**짧은 답변:**  
거래내역과 담당자 정보는 PostgreSQL 데이터베이스에 저장됩니다. 생성된 엑셀 파일은 서버의 exports 폴더에 저장됩니다.

**기술적으로는:**  
PostgreSQL 5개 테이블 (CARD_TRANSACTIONS, CARD_USERS, PROJECTS, SOLUTIONS, EXPENSE_CATEGORIES). 엑셀: `exports/{파일명}.xlsx`.

---

### Q12. 데이터가 얼마나 쌓이나요?

**짧은 답변:**  
월별 거래내역 수백~수천 건이 DB에 누적됩니다. 삭제하지 않으면 계속 쌓입니다.

**기술적으로는:**  
`DELETE /api/transactions`로 전체 삭제 가능. 현재 월별 자동 정리 기능 없음.

---

### Q13. 백업은 어떻게 하나요?

**짧은 답변:**  
제공된 백업 스크립트로 CSV 파일로 내보낼 수 있습니다.

**기술적으로는:**  
`scripts/db_cleanup/backup_db_to_csv.py` 실행 → `backups/` 폴더에 CSV 저장. 정기 백업 자동화는 별도 설정 필요.

---

## 운영 및 장애

---

### Q14. 장애가 나면 어디를 먼저 봐야 하나요?

**짧은 답변:**  
서버 로그를 먼저 확인하고, DB 연결 상태, 파일 경로 설정 순으로 확인합니다.

**기술적으로는:**  
1. uvicorn 로그 (logging.INFO 레벨)  
2. `.env` 파일 DB 접속 정보 확인  
3. PostgreSQL 서버 동작 여부  
4. `uploads/`, `exports/`, `data/` 폴더 권한  
5. Microsoft Graph 토큰 만료 여부 (`data/card_auto_mail_token.json`)

**관련 파일:** `app/core/config.py` (경로 설정), `app/main.py` (로깅 설정)

---

### Q15. 메일이 안 발송될 때 원인은?

**짧은 답변:**  
대부분 Outlook 인증 만료가 원인입니다. 인증 화면에서 재인증하면 해결됩니다.

**기술적으로는:**  
1. `GET /api/mail/auth/status` → `has_token: false` 확인  
2. `POST /api/mail/auth/start` → Device Code 재인증  
3. 토큰 캐시 파일 (`data/card_auto_mail_token.json`) 삭제 후 재인증  
4. Azure 앱 권한 만료 또는 정책 변경 여부 확인

**관련 파일:** `app/services/mail_service.py`

---

### Q16. 업로드 후 담당자가 매핑이 안 되면?

**짧은 답변:**  
카드 사용자 메뉴에서 해당 카드번호를 등록하고, 거래내역 화면의 "사용자 재매핑" 버튼을 누르면 됩니다.

**기술적으로는:**  
`POST /api/transactions/remap` → `mapping_status='unmapped'` 거래 전체 재처리.

---

### Q17. 새 담당자 카드를 추가하려면?

**짧은 답변:**  
"카드 사용자" 메뉴에서 신규 등록 버튼을 눌러 은행, 카드번호, 이름, 이메일을 입력합니다.

**기술적으로는:**  
`POST /api/lookups/cards`. 전체 카드번호(16자리) 입력 권장. 끝4자리만 입력 가능하나 충돌 위험.

---

## 구조 및 기술

---

### Q18. 프론트와 백엔드는 어떻게 연결되나요?

**짧은 답변:**  
화면에서 버튼을 누르면 백엔드 API를 호출하고, 결과를 받아 화면에 표시합니다. 모두 같은 서버에서 동작합니다.

**기술적으로는:**  
같은 FastAPI 서버에서 HTML 렌더링(Jinja2)과 JSON API 모두 제공. 프론트는 `fetch()` API로 비동기 호출.

---

### Q19. 왜 Python을 사용했나요?

**짧은 답변:**  
엑셀 처리(pandas, openpyxl)와 웹 서버(FastAPI)를 Python 하나로 모두 구현 가능해 선택했습니다.

**기술적으로는:**  
pandas(엑셀 파싱), openpyxl(엑셀 생성), FastAPI(웹 프레임워크), MSAL(Microsoft 인증) 모두 Python 생태계.

---

### Q20. DB는 왜 PostgreSQL인가요?

**짧은 답변:**  
안정적이고 무료이며, 동시 접속과 데이터 무결성 제약 지원이 우수합니다.

**기술적으로는:**  
유니크 제약(중복 방지), SERIAL PK, 인덱스(card_last4, use_year_month) 활용.

---

### Q21. 수정 영향도가 큰 부분은 어디인가요?

**짧은 답변:**  
파일 파싱 로직과 카드 매핑 로직이 가장 영향도가 큽니다. 이 부분을 바꾸면 전체 업로드 기능에 영향을 미칩니다.

**기술적으로는:**  
`app/parsers/kb_parser.py`, `app/parsers/ibk_parser.py`, `app/services/transaction_service.py: upload_and_save()`.  
이 파일들이 바뀌면 파싱/매핑 정확도에 직접 영향.

---

### Q22. 새 카드사/새 양식을 추가하려면 어디를 수정해야 하나요?

**짧은 답변:**  
새 파서 파일을 만들고, 은행 판별 로직과 업로드 서비스 2곳만 추가하면 됩니다. API나 화면은 변경 불필요합니다.

**기술적으로는:**  
1. `app/parsers/shinhan_parser.py` 신규 생성  
2. `app/parsers/common.py: detect_bank_type_from_file()` 키워드 추가  
3. `app/services/transaction_service.py: upload_and_save()` elif 추가

---

### Q23. 프로젝트/솔루션/계정과목 목록을 변경하려면?

**짧은 답변:**  
웹 화면에서 직접 추가/수정/삭제하면 됩니다. 코드 수정 불필요합니다.

**기술적으로는:**  
각 마스터 관리 화면(`/lookups/projects`, `/lookups/solutions`, `/lookups/accounts`)에서 CRUD. 변경 즉시 다음 엑셀 생성 시 드롭다운에 반영.

---

### Q24. 이 시스템은 보안이 안전한가요?

**짧은 답변:**  
현재 사내 네트워크 전용 도구로 별도 로그인이 없습니다. 외부 인터넷에 노출하려면 접근 제어 추가가 필요합니다.

**기술적으로는:**  
FastAPI 인증 미들웨어 없음. 메일 발송은 Microsoft OAuth2 인증 (Device Code Flow). DB 연결 정보는 `.env` 파일 관리.

---

### Q25. 전체 삭제 버튼이 있는데 실수로 누르면 어떻게 되나요?

**짧은 답변:**  
현재는 확인 대화상자 하나만 있어서 실수로 전체 데이터가 삭제될 수 있습니다. 추가 방어 장치를 검토할 필요가 있습니다.

**기술적으로는:**  
`DELETE /api/transactions` → CARD_TRANSACTIONS 전체 삭제. 복구는 백업 CSV에서 수동 복원 필요.

**관련 파일:** `app/templates/transactions.html`, `app/routers/api_transactions.py`

---

### Q26. 이 시스템의 처리 한계는 어느 정도인가요?

**짧은 답변:**  
한 번에 수백~수천 건 처리가 가능합니다. 대규모 처리 시 메일 발송이 다소 오래 걸릴 수 있습니다.

**기술적으로는:**  
업로드: pandas 메모리 처리, 레코드당 DB savepoint → 수천 건 가능.  
메일 발송: 순차 처리 (병렬 없음), 1건당 엑셀 생성 + Graph API 호출 → 30명이면 약 1~2분 소요 예상.

---

### Q27. 이 시스템은 클라우드에 올릴 수 있나요?

**짧은 답변:**  
가능합니다. 현재는 로컬 실행 방식이지만, 설정만 바꾸면 클라우드 서버에도 배포할 수 있습니다.

**기술적으로는:**  
Docker 컨테이너화 또는 AWS/Azure VM에 배포 가능. `.env`의 DB 접속 정보만 클라우드 DB로 변경. 메일 인증 전역 변수는 싱글 프로세스 가정이므로 멀티 인스턴스 배포 시 설계 변경 필요.

---

## 빠른 답변 요약표

| 질문 핵심 | 한 줄 답변 |
|-----------|-----------|
| 무엇을 하는 프로그램? | KB/IBK 법인카드 내역 자동 분류 + 엑셀 생성 + Outlook 발송 |
| 기술 스택? | Python(FastAPI) + PostgreSQL + Jinja2 + Microsoft Graph API |
| 어떻게 은행 구분? | 파일 헤더 키워드 자동 판별 |
| 담당자 매핑 원리? | CARD_USERS에 카드번호 등록 → 업로드 시 자동 매칭 |
| 중복 업로드 시? | DB 유니크 제약으로 자동 차단, 스킵 건수 표시 |
| 메일 발송 방식? | Microsoft Graph API (Outlook), 처음 1회 인증 |
| 데이터 저장 위치? | PostgreSQL (거래/마스터), exports/ 폴더 (엑셀 파일) |
| 새 은행 추가? | 파서 파일 1개 + 2곳 코드 수정 |
| 장애 시 확인 순서? | 서버 로그 → DB 연결 → 메일 토큰 |
| 보안 수준? | 사내 전용, 별도 로그인 없음 |
