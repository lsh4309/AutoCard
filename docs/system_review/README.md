# Card Auto - 기술 문서 세트 (System Review)

> 이 폴더는 Card Auto 프로젝트의 파트별 기술 문서 세트입니다.  
> 실제 코드 기준으로 작성되었으며, 임원 보고, 코드리뷰, 운영 대응에 활용합니다.

---

## 전체 문서 목록

| 번호 | 파일명 | 내용 |
|------|--------|------|
| 00 | [00_overview.md](./00_overview.md) | 프로젝트 전체 개요, 아키텍처 다이어그램 |
| 01 | [01_process_flow.md](./01_process_flow.md) | 업무 흐름 (업로드 → 매핑 → 엑셀 → 메일) |
| 02 | [02_backend_overview.md](./02_backend_overview.md) | 백엔드 기술스택, 레이어 구조, 예외 처리 |
| 03 | [03_backend_files_and_functions.md](./03_backend_files_and_functions.md) | 백엔드 파일/함수 단위 역할 |
| 04 | [04_backend_api_reference.md](./04_backend_api_reference.md) | 전체 API 엔드포인트 레퍼런스 |
| 05 | [05_frontend_overview.md](./05_frontend_overview.md) | 프론트엔드 기술스택, 화면 구성 |
| 06 | [06_frontend_files_and_functions.md](./06_frontend_files_and_functions.md) | 프론트 파일/JS 함수 단위 역할 |
| 07 | [07_data_model_and_storage.md](./07_data_model_and_storage.md) | DB 테이블 스키마, 파일 저장 구조 |
| 08 | [08_batch_parsing_and_mapping.md](./08_batch_parsing_and_mapping.md) | 파일 파싱, 은행 판별, 사용자 매핑 로직 |
| 09 | [09_code_review_points.md](./09_code_review_points.md) | 코드리뷰 핵심 포인트, 리스크 정리 |
| 10 | [10_executive_qna_guide.md](./10_executive_qna_guide.md) | 임원/상무님 질문 27개 Q&A |

---

## 추천 읽기 순서

### 1. 빠르게 전체 이해하는 루트 (30분)

```
00_overview.md          → 프로젝트 전체 그림 파악
01_process_flow.md      → 실제 업무 흐름 이해
07_data_model_and_storage.md → 어떤 데이터를 저장하는지
```

### 2. 상무님 보고 전 준비 루트 (20분)

```
10_executive_qna_guide.md   → 예상 질문 27개 숙지
00_overview.md              → "1분 설명" 섹션 암기
01_process_flow.md          → "질문받기 쉬운 포인트" 확인
```

### 3. 코드리뷰 전 준비 루트 (40분)

```
02_backend_overview.md              → 레이어 구조 파악
03_backend_files_and_functions.md   → 파일/함수별 역할
09_code_review_points.md            → 리뷰 포인트 + 리스크
08_batch_parsing_and_mapping.md     → 핵심 파싱/매핑 로직
```

### 4. 기능 수정/확장 시 루트

```
04_backend_api_reference.md     → 관련 API 파악
03_backend_files_and_functions.md → 수정할 파일/함수 위치
08_batch_parsing_and_mapping.md → 새 은행 추가 가이드
09_code_review_points.md        → 영향도 확인
```

---

## 상무님 질문 대응 추천 문서 순서

1. **[10_executive_qna_guide.md](./10_executive_qna_guide.md)** - 예상 질문 27개 + 답변
2. **[00_overview.md](./00_overview.md)** - 전체 그림 (아키텍처 다이어그램 포함)
3. **[01_process_flow.md](./01_process_flow.md)** - 업무 흐름 순서도
4. **[07_data_model_and_storage.md](./07_data_model_and_storage.md)** - 데이터 저장 질문 대응

---

## 코드리뷰 전에 꼭 읽을 문서

1. **[09_code_review_points.md](./09_code_review_points.md)** - 잘된 점 / 개선 포인트 / 리스크
2. **[02_backend_overview.md](./02_backend_overview.md)** - 레이어 구조와 이중 DB 접근 방식
3. **[08_batch_parsing_and_mapping.md](./08_batch_parsing_and_mapping.md)** - 핵심 파싱/매핑 로직
4. **[03_backend_files_and_functions.md](./03_backend_files_and_functions.md)** - 함수 호출 관계

---

## 핵심 포인트 3줄 요약

> 1. **Card Auto = KB/IBK 엑셀 자동 파싱 → 담당자별 엑셀 생성 → Outlook 자동 발송**  
> 2. **백엔드:** FastAPI + PostgreSQL + pandas/openpyxl + Microsoft Graph API  
> 3. **핵심 로직:** 은행 자동 판별, 카드번호 매핑(N+1 방지), savepoint 트랜잭션, Device Code 메일 인증

---

## 문서 생성 기준

- 작성 일자: 2026년 3월 20일
- 기준 코드: `app/` 전체 (routers, services, parsers, models, db, templates, static)
- 분석 방법: 실제 소스코드 직접 읽기 (추정 없음)
- 확인 필요 항목: 각 문서 하단 "확인 필요 사항" 섹션 참조
