# Card Auto - 법인카드 승인내역 자동 처리 시스템

KB국민은행 / IBK기업은행 법인카드 승인내역 엑셀을 업로드하고,
카드번호 끝 4자리 기준으로 사용자를 매핑하여 카드별 결과 엑셀을 생성합니다.

---

## 빠른 시작

### 1. 의존성 설치

```bash
pip install -r requirements.txt
```

### 2. 서버 실행

```bash
cd C:\Users\이승현\Card_Auto
python -m uvicorn app.main:app --reload --port 8000
```

### 3. 브라우저 접속

```
http://localhost:8000
```

---

## 기능 설명

### 업무 흐름

1. **마스터 관리** → 카드 사용자 등록 (카드번호 끝 4자리 + 사용자명)
2. **파일 업로드** → KB/IBK 승인내역 엑셀 업로드
3. **거래내역 관리** → 프로젝트/솔루션/계정과목 입력 (화면에서 일괄 수정 가능)
4. **결과 파일 생성** → 카드별 엑셀 다운로드

### 화면 구성

| 화면 | URL | 설명 |
|------|-----|------|
| 업로드 | `/upload` | KB/IBK 파일 업로드 및 파싱 |
| 거래내역 | `/transactions` | 거래 목록 조회/수정/일괄수정 |
| 결과 생성 | `/exports` | 카드별 엑셀 생성 및 다운로드 |
| 카드 사용자 | `/masters/cards` | 카드-사용자 매핑 마스터 |
| 프로젝트 | `/masters/projects` | 프로젝트 마스터 |
| 솔루션 | `/masters/solutions` | 솔루션 마스터 |
| 계정과목 | `/masters/accounts` | 계정과목/지출내역 마스터 |

---

## 결과 엑셀 사양

- **시트명**: `내역`
- **컬럼**: 승인일 / 승인시간 / 카드번호 / 이용자명 / 가맹점명 / 업종명 / 승인금액 / 프로젝트명 / 솔루션 / 계정과목/지출내역 / 회식비/접대비/회의비 Flex 사전승인 유무 / 참석자이름(모두기재) / 구매내역 / 기타사항
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
      validation_service.py    # 검증 로직
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
  card_auto.db           # SQLite DB (자동 생성)
  requirements.txt
  README.md
```

---

## API 엔드포인트

| Method | URL | 설명 |
|--------|-----|------|
| POST | `/api/uploads` | 파일 업로드 및 파싱 |
| GET | `/api/transactions` | 거래 목록 조회 |
| PATCH | `/api/transactions/{id}` | 단건 수정 |
| POST | `/api/transactions/bulk-update` | 다건 일괄 수정 |
| GET/POST/PUT/DELETE | `/api/masters/cards` | 카드 사용자 CRUD |
| GET/POST/PUT/DELETE | `/api/masters/projects` | 프로젝트 CRUD |
| GET/POST/PUT/DELETE | `/api/masters/solutions` | 솔루션 CRUD |
| GET/POST/PUT/DELETE | `/api/masters/accounts` | 계정과목 CRUD |
| POST | `/api/exports/generate` | 엑셀 생성 |
| GET | `/api/exports/download/{filename}` | 엑셀 다운로드 |

---

## 초기 기본 데이터

서버 최초 실행 시 자동으로 아래 데이터가 등록됩니다.

**솔루션**: DataRobot / Github / Presales - 솔루션 / 해당사항 없음

**계정과목**: 식대 / 교통비 / 접대비 / 회의비 / 소모품비 / 도서인쇄비 / 교육훈련비 / 기타경비
