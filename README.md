# Card Auto - 법인카드 승인내역 자동 처리 시스템

KB국민은행 / IBK기업은행 법인카드 승인내역 엑셀을 업로드하고,
카드번호(끝 4자리 또는 전체) 기준으로 사용자를 매핑하여 카드별 결과 엑셀을 생성합니다.

## 핵심 기능

- **KB/IBK 지원**: 엑셀 헤더 자동 감지로 은행 타입 판별, 각 은행 포맷에 맞는 파싱
- **전체 카드번호 기반 그룹화**: 동일 끝 4자리를 가진 여러 카드를 전체 번호로 구분하여 카드별 엑셀 생성
- **마스킹 → 전체번호 변환**: 거래 데이터가 마스킹(****)된 경우, card_master에서 전체 번호를 조회해 결과 엑셀에 표시
- **N+1 방지**: 카드 마스터 1회 조회 후 메모리 룩업으로 매핑 (업로드, 재매핑, 엑셀 생성 공통)

---

## 빠른 시작

### 1. 의존성 설치

```bash
pip install -r requirements.txt
```

### 2. DB 설정

- **PostgreSQL**: 모든 테이블 (거래내역 + 카드/프로젝트/솔루션/계정과목 마스터)

**테이블 생성**: DBeaver에서 PostgreSQL 연결 후 `scripts/sql/init_pg_masters.sql` 전체 실행.  
(또는 `init_pg_transactions.sql`만 실행해 거래내역 테이블만 생성)  
**테이블이 생성되어야만** 거래내역 관리 화면에 데이터가 표시됨.

> 이전에는 SQLite(card_auto.db)를 사용해, 로컬 .db 파일이 있으면 테이블 없이도 화면이 나왔을 수 있음.  
> 현재는 PostgreSQL만 사용하며, DBeaver에서 SQL 실행으로 테이블을 생성한 뒤에만 화면이 정상 동작함.

### 3. 서버 실행

```bash
cd C:\Users\이승현\Card_Auto
python -m uvicorn app.main:app --reload --port 8000
```

> **포트 충돌 시** (WinError 10013): 8000 포트가 사용 중이면 `--port 8001` 등 다른 포트 사용.  
> 또는 기존 프로세스 종료: `netstat -ano | findstr :8000` 후 해당 PID `taskkill /PID <pid> /F`

### 4. 브라우저 접속

```
http://localhost:8000
```

---

## 기능 설명

### 업무 흐름

1. **마스터 관리** → 카드 사용자 등록 (카드번호 끝 4자리 + 사용자명)
2. **파일 업로드** → KB/IBK 승인내역 엑셀 업로드
3. **거래내역 관리** → 조회/재매핑 (카드 사용자가 결과 엑셀에서 프로젝트 등 입력)
4. **결과 파일 생성** → 카드별 엑셀 다운로드

### 화면 구성

| 화면 | URL | 설명 |
|------|-----|------|
| 업로드 | `/upload` | KB/IBK 파일 업로드 및 파싱 |
| 거래내역 | `/transactions` | 거래 목록 조회/재매핑 |
| 결과 생성 | `/exports` | 카드별 엑셀 생성 및 다운로드 |
| 카드 사용자 | `/masters/cards` | 카드-사용자 매핑 마스터 |
| 프로젝트 | `/masters/projects` | 프로젝트 마스터 |
| 솔루션 | `/masters/solutions` | 솔루션 마스터 |
| 계정과목 | `/masters/accounts` | 계정과목/지출내역 마스터 |

---

## 결과 엑셀 사양

- **시트명**: `내역`
- **컬럼**: 승인일 / 승인시간 / 카드번호 / 이용자명 / 가맹점명 / 승인금액 / 프로젝트명 / 솔루션 / 계정과목/지출내역 / 회식비/접대비/회의비 Flex 사전승인 유무 / 참석자이름(모두기재) / 구매내역 / 기타사항
- **드롭다운**: 프로젝트명, 솔루션, 계정과목, Flex 사전승인 유무 (openpyxl DataValidation 적용)
- **파일명 형식**: `{사용자명} {YYYYMM}({은행코드}).xlsx`
  - 예: `윤이현 202512(KB).xlsx`

---

## 폴더 구조

```
Card_Auto/
  app/
    main.py              # FastAPI 앱 진입점
    config.py            # 경로/DB 설정
    db.py                # SQLAlchemy 엔진 (SQLite)
    models.py            # Transaction 모델
    parsers/             # KB/IBK 엑셀 파서
      common.py          # 공통 파싱 유틸 (날짜/시간/카드번호 정규화)
      kb_parser.py       # KB 국민은행 파서
      ibk_parser.py      # IBK 기업은행 파서
    services/            # 비즈니스 로직
      transaction_service.py   # 거래 저장/조회/재매핑
      master_service.py        # 마스터 CRUD 통합
      card_master_service.py   # 카드 사용자 마스터
      excel_export_service.py # 엑셀 결과 파일 생성
    database/            # PostgreSQL 연동 (연결/Repository 분리)
      connection.py     # DB 연결 및 트랜잭션
      base.py           # PgRepository 베이스
      bootstrap.py      # 테이블 생성/시드
      repositories/
        card_repository.py    # card_master
        master_repository.py  # project/solution/account 마스터
    routers/             # API 및 페이지 라우터
      pages.py           # 페이지 렌더링
      api_uploads.py     # 업로드 API
      api_transactions.py # 거래 API
      api_exports.py     # 엑셀 생성/다운로드 API
      api_masters.py     # 마스터 API
    templates/           # Jinja2 HTML 템플릿
    static/              # CSS/JS 정적 파일
  docs/                  # 기술 문서
    technical_spec.md    # 상세 기술 명세
    email_guide.md       # 이메일 전송 기능 설계
  scripts/sql/
    init_pg_masters.sql    # PostgreSQL 전체 DDL (마스터+거래내역)
    init_pg_transactions.sql # 거래내역만 생성 시
    migrate_card_master_columns.sql # card_no_normalized, card_last4 마이그레이션
  uploads/               # 업로드 임시 파일
  exports/               # 생성된 결과 엑셀
  requirements.txt
  README.md
```

---

## API 엔드포인트

| Method | URL | 설명 |
|--------|-----|------|
| POST | `/api/uploads` | 파일 업로드 및 파싱 |
| GET | `/api/transactions` | 거래 목록 조회 |
| POST | `/api/transactions/remap` | 사용자 재매핑 |
| DELETE | `/api/transactions` | 거래내역 전체 삭제 |
| GET/POST/PUT/DELETE | `/api/masters/cards` | 카드 사용자 CRUD |
| GET/POST/PUT/DELETE | `/api/masters/projects` | 프로젝트 CRUD |
| GET/POST/PUT/DELETE | `/api/masters/solutions` | 솔루션 CRUD |
| GET/POST/PUT/DELETE | `/api/masters/accounts` | 계정과목 CRUD |
| POST | `/api/exports/generate` | 엑셀 생성 |
| GET | `/api/exports/download/{filename}` | 엑셀 다운로드 |

---

## DB 성능 고려사항

### 적용된 개선 (N+1 방지)

- **결과 파일 생성 페이지** (`get_cards_for_export`): 카드 마스터 1회 조회 후 룩업 맵으로 매칭 (기존: 거래 건수만큼 PostgreSQL 쿼리)
- **파일 업로드** (`upload_and_save`): 동일 룩업 방식 적용
- **사용자 재매핑** (`remap_transactions`): 동일 룩업 방식 적용
- **거래 목록/엑셀 생성** (전체번호 필터): `card_last4`로 DB 필터 후 메모리에서 정규화 매칭 (전체 로드 대비 축소)

### 잠재적 성능 저하 지점

| 기능 | 위치 | 위험 요인 | 권장 |
|------|------|-----------|------|
| 결과 파일 페이지 | `get_cards_for_export` | `year_month` 미지정 시 전체 거래 로드 | 년월 필터 사용 권장 |
| 거래 목록 (전체번호 필터) | `get_transactions` | 동일 `card_last4` 거래 다수 시 메모리 필터 부담 | 거래량 적을 때 영향 적음 |
| 엑셀 생성 (전체번호) | `_get_transactions_for_card` | 위와 동일 | 카드당 거래 수 적으면 무난 |
| PostgreSQL 연동 | `app.database.connection`, `repositories` | 호출마다 새 연결 생성 (풀링 없음) | 거래량 급증 시 연결 풀 도입 검토 |

---

## 초기 기본 데이터

서버 최초 실행 시 자동으로 아래 데이터가 등록됩니다.

**솔루션**: DataRobot / Github / Presales - 솔루션 / 해당사항 없음

**계정과목**: 식대 / 교통비 / 접대비 / 회의비 / 소모품비 / 도서인쇄비 / 교육훈련비 / 기타경비
