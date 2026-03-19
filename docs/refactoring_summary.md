# 폴더 구조 리팩토링 요약

## 수행된 작업

### 1. 파일 이동

| 원본 | 이동 후 |
|------|---------|
| `app/pg_card_master.py` | `app/database/pg_card_master.py` |
| `app/pg_master_tables.py` | `app/database/pg_master_tables.py` |
| `send_email_guide.md` (루트) | `docs/email_guide.md` |

### 2. 새로 생성된 폴더/파일

- `app/database/` - PostgreSQL 연동 모듈
- `app/database/__init__.py`
- `app/static/` - 정적 파일 (CSS/JS)
- `app/static/.gitkeep`
- `docs/` - 기술 문서
- `docs/technical_spec.md` - 상세 기술 명세
- `docs/email_guide.md` - 이메일 전송 기능 설계
- `docs/refactoring_summary.md` - 본 문서

### 3. import 수정

- `app/services/master_service.py`: `from app import pg_master_tables` → `from app.database import pg_master_tables`
- `app/services/card_master_service.py`: `from app import pg_card_master` → `from app.database import pg_card_master`

---

## 삭제/제외 제안 목록

### 삭제 권장 (사용 여부 확인 후)

| 파일 | 사유 |
|------|------|
| `temp_projects.csv` | 프로젝트 목록 임시 데이터. .gitignore(*.csv)에 의해 이미 제외됨. 필요 없으면 삭제 |
| `db.ipynb` | Jupyter 노트북. .gitignore(*.ipynb)에 의해 이미 제외됨. 개발용이면 scripts/ 등으로 이동 검토 |

### 제외 유지 (.gitignore)

- `__pycache__/`, `*.pyc`
- `*.db`, `card_auto.db`
- `*.ipynb`
- `tests/` (테스트 폴더 - 현재 제외됨)
- `.env`, `*.xlsx`, `*.csv`, `*.txt`, `*.log`

### tests/ 폴더 참고

- `tests/import_projects.py`: 프로젝트 일괄 등록 스크립트 (xlxs/참고항목.xlsx 경로 사용)
- `tests/test_flow.py`: 통합 테스트 (xlxs 폴더, card_last4 파라미터 등 구버전 API 사용)

tests/는 .gitignore로 제외되어 있으나, 필요 시 `tests/` 제외를 해제하고 스크립트 경로/API를 최신 구조에 맞게 수정 후 사용 가능.

---

## 터미널 명령어 (참고)

이미 수행된 작업이므로, 동일 구조를 다른 환경에 적용할 때 참고용:

```powershell
# docs 폴더 생성
New-Item -ItemType Directory -Force -Path "docs"

# app/database 폴더 생성 (Python 패키지)
New-Item -ItemType Directory -Force -Path "app\database"

# app/static 폴더 생성
New-Item -ItemType Directory -Force -Path "app\static"

# 임시 파일 삭제 (선택)
# Remove-Item "temp_projects.csv" -ErrorAction SilentlyContinue
# Remove-Item "db.ipynb" -ErrorAction SilentlyContinue
```
