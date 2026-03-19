# Card Auto - 법인카드 승인내역 자동 처리 시스템

KB국민은행 / IBK기업은행 법인카드 승인내역 엑셀을 업로드하고,
카드번호(끝 4자리 또는 전체) 기준으로 사용자를 매핑하여 카드별 결과 엑셀을 생성합니다.
생성된 엑셀을 각 카드 사용자 이메일로 Outlook 메일로 자동 발송할 수 있습니다.

## 핵심 기능

- **KB/IBK 지원**: 엑셀 헤더 자동 감지로 은행 타입 판별, 각 은행 포맷에 맞는 파싱
- **전체 카드번호 기반 그룹화**: 동일 끝 4자리를 가진 여러 카드를 전체 번호로 구분하여 카드별 엑셀 생성
- **마스킹 → 전체번호 변환**: 거래 데이터가 마스킹(****)된 경우, CARD_USERS에서 전체 번호를 조회해 결과 엑셀에 표시
- **N+1 방지**: 카드 마스터 1회 조회 후 메모리 룩업으로 매핑 (업로드, 재매핑, 엑셀 생성 공통)
- **이메일 발송**: 카드별 엑셀을 각 사용자 이메일로 Outlook(Graph API) 자동 발송

---

## 빠른 시작

### 1. 의존성 설치

```bash
pip install -r requirements.txt
```

### 2. DB 설정

- **PostgreSQL**: 모든 테이블 (거래내역 + 카드 사용자/프로젝트/솔루션/계정과목)

**테이블 생성** (둘 중 하나 선택):

- DBeaver: `scripts/sql/init_schema.sql` 전체 실행
- 또는: `python scripts/db_cleanup/drop_and_recreate_schema.py` 실행

> 테이블이 생성되어야만 거래내역 관리 화면에 데이터가 표시됩니다.

### 3. 환경변수 (.env)

```env
# PostgreSQL
PG_HOST=localhost
PG_PORT=5432
PG_DATABASE=postgres
PG_USER=postgres
PG_PASSWORD=your_password

# Outlook 메일 발송 (선택)
EMAIL_SENDER=발신자이메일@회사도메인.com
AZURE_CLIENT_ID=your_client_id
AZURE_TENANT_ID=your_tenant_id
```

### 4. 서버 실행

```bash
python -m uvicorn app.main:app --reload --port 8000
```

### 5. 브라우저 접속

```
http://localhost:8000
```

---

## 기능 설명

### 업무 흐름

1. **마스터 관리** → 카드 사용자 등록 (카드번호 + 사용자명 + 이메일)
2. **파일 업로드** → KB/IBK 승인내역 엑셀 업로드
3. **거래내역 관리** → 조회/재매핑 (카드 사용자가 결과 엑셀에서 프로젝트 등 입력)
4. **결과 파일 생성** → 카드별 엑셀 다운로드 또는 **메일 발송**

### 화면 구성

| 화면 | URL | 설명 |
|------|-----|------|
| 업로드 | `/upload` | KB/IBK 파일 업로드 및 파싱 |
| 거래내역 | `/transactions` | 거래 목록 조회/재매핑 |
| 결과 생성 | `/exports` | 카드별 엑셀 생성, 다운로드, **메일 발송** |
| 카드 사용자 | `/lookups/cards` | 카드-사용자-이메일 매핑 |
| 프로젝트 | `/lookups/projects` | 프로젝트 |
| 솔루션 | `/lookups/solutions` | 솔루션 |
| 계정과목 | `/lookups/accounts` | 계정과목/지출내역 |

---

## 이메일 발송 (Outlook)

카드별 엑셀을 각 사용자 이메일로 발송합니다. **발신자는 .env의 EMAIL_SENDER(인사팀장님 계정)** 입니다.

- **최초 1회**: 결과 생성 화면에서 "전체 메일 발송" → "Outlook 인증 시작" → 브라우저에서 코드 입력 및 로그인
- **이후**: 인증 토큰이 `data/card_auto_mail_token.json`에 저장되어 자동 발송
- **상세 가이드**: [docs/outlook_email_guide.md](docs/outlook_email_guide.md)

---

## 폴더 구조

```
Card_Auto/
  app/
    main.py              # FastAPI 앱 진입점
    core/                # 핵심 설정 및 ORM
      config.py          # 경로/DB/메일 설정
      database.py        # SQLAlchemy 엔진 및 세션 (ORM)
    models/              # SQLAlchemy 모델
      transaction.py     # CARD_TRANSACTIONS 모델
    db/                  # PostgreSQL 직접 쿼리 (psycopg2)
      connection.py      # DB 연결 및 트랜잭션
      base.py            # PgRepository 베이스
      bootstrap.py       # 테이블 생성/시드
      repositories/      # card, project, solution, expense_categories
    parsers/             # KB/IBK 엑셀 파서
    services/            # 비즈니스 로직
    routers/             # API 및 페이지 라우터
    templates/           # Jinja2 HTML 템플릿
    static/              # CSS/JS 정적 파일
  scripts/
    db_cleanup/          # DB 백업/재구축/복구 스크립트
      backup_db_to_csv.py
      drop_and_recreate_schema.py
      restore_from_csv.py
      verify_schema.py
      init_schema.sql
    sql/
      init_schema.sql    # 신규 스키마 DDL (대문자 테이블명)
      deprecated/        # 구 스키마 SQL (참고용)
  docs/
    technical_spec.md
    outlook_email_guide.md   # 이메일/Outlook 인증 가이드
  uploads/               # 업로드 임시 파일
  exports/               # 생성된 결과 엑셀
  data/                  # 런타임 데이터 (메일 토큰 등)
  backups/               # DB 백업 CSV (gitignore)
```

---

## DB 테이블 (대문자, Master 명칭 제거)

| 테이블 | 설명 |
|--------|------|
| CARD_USERS | 카드 사용자 (카드번호, 사용자명, 이메일) |
| PROJECTS | 프로젝트 |
| SOLUTIONS | 솔루션 |
| EXPENSE_CATEGORIES | 계정과목 |
| CARD_TRANSACTIONS | 거래내역 |

---

## API 엔드포인트

| Method | URL | 설명 |
|--------|-----|------|
| POST | `/api/uploads` | 파일 업로드 및 파싱 |
| GET | `/api/transactions` | 거래 목록 조회 |
| POST | `/api/transactions/remap` | 사용자 재매핑 |
| DELETE | `/api/transactions` | 거래내역 전체 삭제 |
| GET/POST/PUT/DELETE | `/api/lookups/cards` | 카드 사용자 CRUD |
| GET/POST/PUT/DELETE | `/api/lookups/projects` | 프로젝트 CRUD |
| GET/POST/PUT/DELETE | `/api/lookups/solutions` | 솔루션 CRUD |
| GET/POST/PUT/DELETE | `/api/lookups/accounts` | 계정과목 CRUD |
| POST | `/api/exports/generate` | 엑셀 생성 |
| GET | `/api/exports/download/{filename}` | 엑셀 다운로드 |
| GET | `/api/exports/cards` | 발송 대상 카드 목록 |
| GET | `/api/mail/auth/status` | Outlook 인증 상태 |
| POST | `/api/mail/auth/start` | Outlook 인증 시작 |
| POST | `/api/mail/send` | 메일 발송 |

---

## 결과 엑셀 사양

- **시트명**: `내역`
- **컬럼**: 승인일 / 승인시간 / 카드번호 / 이용자명 / 가맹점명 / 승인금액 / 프로젝트명 / 솔루션 / 계정과목/지출내역 / Flex 사전승인 유무 / 참석자이름 / 구매내역 / 기타사항
- **드롭다운**: 프로젝트명, 솔루션, 계정과목, Flex 사전승인 유무
- **파일명 형식**: `{사용자명} {YYYYMM}({은행코드}).xlsx`
