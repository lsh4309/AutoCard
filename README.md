# Card Auto - 법인카드 승인내역 자동 처리 시스템

KB국민은행 / IBK기업은행 법인카드 승인내역 엑셀을 업로드하고,
카드번호 끝 4자리 기준으로 사용자를 매핑하여 카드별 결과 엑셀을 생성합니다.

---

## 빠른 시작

### 1. 의존성 설치

```bash
pip install -r requirements.txt
```

### 2. DB 설정

- **PostgreSQL**: 카드 사용자, 프로젝트, 솔루션, 계정과목 마스터 (.env의 PG_* 환경변수)
- **SQLite**: 거래내역 (card_auto.db)

DB 테이블 및 데이터는 DBeaver 등으로 직접 관리. 앱 실행 시 자동 초기화 없음.

### 3. 서버 실행

```bash
cd C:\Users\이승현\Card_Auto
python -m uvicorn app.main:app --reload --port 8000
```

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
CARD_AUTO/
  app/
    main.py              # FastAPI 앱 진입점
    db.py                # SQLAlchemy 설정
    models.py            # DB 모델
    config.py            # 경로/설정
    parsers/
      common.py          # 공통 파싱 유틸
      kb_parser.py       # KB 파일 파서
      ibk_parser.py      # IBK 파일 파서
    services/
      transaction_service.py   # 거래 저장/조회/수정
      master_service.py        # 마스터 CRUD
      excel_export_service.py  # 엑셀 생성
    routers/
      pages.py           # 페이지 라우터
      api_uploads.py     # 업로드 API
      api_transactions.py # 거래 API
      api_masters.py     # 마스터 API
      api_exports.py     # 엑셀 생성/다운로드 API
    templates/           # Jinja2 HTML 템플릿
    static/              # CSS/JS 정적 파일
  uploads/               # 업로드 임시 파일
  exports/               # 생성된 결과 엑셀
  card_auto.db           # SQLite DB (거래내역, 자동 생성)
  scripts/sql/
    init_pg_masters.sql   # PostgreSQL 마스터 테이블 DDL 및 초기 데이터
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
| PostgreSQL 연동 | `pg_card_master`, `pg_master_tables` | 호출마다 새 연결 생성 (풀링 없음) | 거래량 급증 시 연결 풀 도입 검토 |

---

## 초기 기본 데이터

서버 최초 실행 시 자동으로 아래 데이터가 등록됩니다.

**솔루션**: DataRobot / Github / Presales - 솔루션 / 해당사항 없음

**계정과목**: 식대 / 교통비 / 접대비 / 회의비 / 소모품비 / 도서인쇄비 / 교육훈련비 / 기타경비
