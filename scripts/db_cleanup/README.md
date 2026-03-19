# DB 클린 작업 스크립트

DB 스키마 전면 재구축 및 데이터 마이그레이션에 사용된 스크립트 모음입니다.

## 실행 순서

1. **backup_db_to_csv.py** - 기존 테이블 데이터를 `backups/` 폴더에 CSV로 백업
2. **drop_and_recreate_schema.py** - 기존 테이블 삭제 후 신규 대문자 스키마 생성
3. **restore_from_csv.py** - 백업 CSV를 신규 테이블에 복구
4. **verify_schema.py** - 테이블 목록 및 행 수 확인

## 실행 방법

프로젝트 루트에서:

```bash
python scripts/db_cleanup/backup_db_to_csv.py
python scripts/db_cleanup/drop_and_recreate_schema.py
python scripts/db_cleanup/restore_from_csv.py
python scripts/db_cleanup/verify_schema.py
```

## 신규 테이블명 (대문자, Master 명칭 제거)

| 기존 | 신규 |
|------|------|
| card_master | CARD_USERS |
| project_master | PROJECTS |
| solution_master | SOLUTIONS |
| account_subject_master | EXPENSE_CATEGORIES |
| transactions | CARD_TRANSACTIONS |

## 관련 파일

- `init_schema.sql` - DBeaver 등에서 직접 실행용 DDL (본 폴더 내)
- `../backups/` - 백업 CSV 저장 위치 (프로젝트 루트의 backups 폴더)
