# 09. 코드리뷰 포인트 (Code Review Points)

## 1. 문서 목적
코드리뷰 시 참고해야 할 핵심 포인트를 정리합니다.  
잘된 설계, 개선 가능한 포인트, 운영 리스크를 구분하여 제시합니다.  
> 리팩토링 코드는 제공하지 않으며, 문서로만 정리합니다.

---

## 2. 백엔드 리뷰 포인트

---

### 백엔드 포인트 1: N+1 방지 설계 ✅ 잘된 점
- **현재 상태:** `_build_card_lookups()`로 카드 마스터를 1회 조회 후 메모리 딕셔너리로 변환. 수백 건 처리 시에도 DB 조회 1회.
- **왜 중요함:** 개당 DB 조회 시 수백 건 = 수백 번 쿼리 → 성능 저하
- **확인할 파일:** `app/services/transaction_service.py: _build_card_lookups()`
- **질문 예시:** "업로드 시 DB 쿼리가 몇 번 발생하나요?"

---

### 백엔드 포인트 2: Savepoint 트랜잭션 패턴 ✅ 잘된 점
- **현재 상태:** 각 레코드 저장을 `db.begin_nested()` (savepoint)로 감싸, 개별 실패가 전체 롤백을 일으키지 않음
- **왜 중요함:** 100건 중 1건 중복이라도 전체 업로드 실패하면 사용성 매우 나쁨
- **확인할 파일:** `app/services/transaction_service.py: upload_and_save()`
- **질문 예시:** "파일 업로드 중 일부 오류 발생 시 어떻게 처리되나요?"

---

### 백엔드 포인트 3: 이중 DB 접근 방식 (ORM + Raw SQL) ⚠️ 주의 포인트
- **현재 상태:** CARD_TRANSACTIONS은 SQLAlchemy ORM, 마스터 테이블은 psycopg2 Raw SQL
- **왜 중요함:** 일관성 부재 → 새 개발자가 혼란스러울 수 있음. DB 세션 라이프사이클 관리 이원화.
- **확인할 파일:** `app/core/database.py` (ORM), `app/db/connection.py` (Raw SQL)
- **리스크:** ORM 세션과 psycopg2 연결이 같은 트랜잭션을 공유하지 않음 → 데이터 정합성 리스크 가능
- **질문 예시:** "왜 두 가지 DB 접근 방식을 혼용하나요?"

---

### 백엔드 포인트 4: 파서의 은행 파일 형식 의존성 ⚠️ 리스크
- **현재 상태:** `detect_bank_type_from_file()`과 각 파서가 특정 컬럼명 키워드에 의존
- **왜 중요함:** 은행이 엑셀 형식을 변경하면 즉시 파싱 실패 → 업무 중단
- **확인할 파일:** `app/parsers/common.py`, `app/parsers/kb_parser.py`, `app/parsers/ibk_parser.py`
- **리스크:** "승인일시" 키워드 변경, 컬럼 순서 변경 등에 취약
- **질문 예시:** "은행에서 파일 형식이 바뀌면 어떻게 되나요?"

---

### 백엔드 포인트 5: 메일 인증 상태 전역 변수 ⚠️ 주의 포인트
- **현재 상태:** `_auth_state`가 모듈 수준 전역 변수. 스레드 Lock으로 동시 접근 보호
- **왜 중요함:** 단일 프로세스 가정 → 멀티 프로세스 배포(gunicorn 등) 시 인증 상태 공유 불가
- **확인할 파일:** `app/services/mail_service.py`
- **리스크:** 프로세스 재시작 시 인증 상태 초기화 (단, 토큰 파일이 있으면 자동 복구)
- **질문 예시:** "메일 인증 상태는 어디에 저장되나요?"

---

### 백엔드 포인트 6: 임시 파일 정리 ✅ 잘된 점
- **현재 상태:** `finally` 블록에서 `save_path.unlink(missing_ok=True)` → 예외 발생 시에도 임시 파일 삭제 보장
- **확인할 파일:** `app/routers/api_uploads.py`
- **질문 예시:** "업로드 중 오류 발생 시 임시 파일이 남나요?"

---

### 백엔드 포인트 7: exports/ 폴더 파일 누적 ⚠️ 운영 리스크
- **현재 상태:** 엑셀 파일 생성 시 `EXPORT_DIR / file_name`으로 저장. 자동 삭제 로직 없음.
- **왜 중요함:** 장기 운영 시 디스크 공간 소모
- **확인할 파일:** `app/services/excel_export_service.py: generate_card_excel()`
- **리스크:** 동일 파일명은 덮어쓰기, 다른 월의 파일은 누적
- **질문 예시:** "생성된 엑셀 파일은 언제 삭제되나요?"

---

### 백엔드 포인트 8: 중복 Repository 파일 ⚠️ 개선 가능
- **현재 상태:** `lookup_repository.py`와 `master_repository.py`가 거의 동일한 코드 존재
- **왜 중요함:** 수정 시 두 파일 모두 변경해야 할 수 있음 → 누락 위험
- **확인할 파일:** `app/db/repositories/lookup_repository.py`, `app/db/repositories/master_repository.py`
- **현재 사용:** `lookup_service.py`는 `lookup_repository`를 import. `master_repository`는 사용 여부 확인 필요.

---

### 백엔드 포인트 9: 인증/권한 없음 ⚠️ 운영 리스크
- **현재 상태:** FastAPI에 별도 인증 미들웨어 없음. 모든 API 누구나 호출 가능.
- **왜 중요함:** 사내 네트워크 외부 노출 시 보안 위험 (전체 삭제 API, 메일 발송 API 포함)
- **확인할 파일:** `app/main.py` (미들웨어 없음), `app/routers/api_transactions.py: delete_all()`
- **질문 예시:** "이 시스템의 접근 제어는 어떻게 되어 있나요?"

---

### 백엔드 포인트 10: 카드번호 끝4자리 충돌 가능성 ⚠️ 설계 제약
- **현재 상태:** `last4_lookup[(last4, bank_type)]`에서 같은 은행의 동일 끝4자리는 첫 번째 매칭
- **왜 중요함:** 실제로 같은 은행에서 끝4자리 동일한 카드 두 명이 있으면 오매핑
- **확인할 파일:** `app/services/transaction_service.py: _build_card_lookups()`
- **미티게이션:** 전체 카드번호 등록 시 full_lookup 우선 매칭

---

## 3. 프론트엔드 리뷰 포인트

---

### 프론트 포인트 1: 메일 발송 다이얼로그 상태 관리 ✅ 잘된 점
- **현재 상태:** `_showPanel()` 함수로 3개 패널 전환 일관 관리. 타이머 정리도 `closeMailDialog()`에서 처리.
- **확인할 파일:** `app/templates/exports.html`

---

### 프론트 포인트 2: 전체 삭제 위험 작업 방어 부족 ⚠️ 리스크
- **현재 상태:** `deleteAllTransactions()`에서 `confirm()` 대화상자 하나만 사용
- **왜 중요함:** 실수로 확인을 클릭하면 모든 거래내역 영구 삭제
- **확인할 파일:** `app/templates/transactions.html`
- **개선 방향:** 텍스트 입력 재확인("DELETE" 입력 등)

---

### 프론트 포인트 3: DOM에서 직접 카드 목록 수집 ⚠️ 주의 포인트
- **현재 상태:** `_getTableCards()`가 DOM에서 `querySelectorAll`로 카드 정보를 직접 수집
- **왜 중요함:** 테이블에 없는 카드(필터로 숨겨진)는 발송 대상에서 제외될 수 있음
- **확인할 파일:** `app/templates/exports.html: _getTableCards()`
- **질문 예시:** "필터 적용 상태에서 전체 발송 클릭 시 어떻게 되나요?"

---

### 프론트 포인트 4: 외부 CDN 의존 ⚠️ 운영 리스크
- **현재 상태:** Tailwind CSS, Font Awesome을 CDN에서 로드
- **왜 중요함:** 인터넷 연결 불가 환경에서 UI 완전히 깨짐
- **확인할 파일:** `app/templates/base.html`
- **개선 방향:** 로컬 정적 파일로 번들링

---

### 프론트 포인트 5: 페이지네이션 버그 ⚠️ 버그
- **현재 상태:** `transactions.html`의 이전 페이지 링크에 `card_number` 파라미터가 `filter_card_number`로 잘못 참조될 수 있음 (실제 변수명 확인 필요)
- **확인할 파일:** `app/templates/transactions.html` (pagination 링크 부분)

---

### 프론트 포인트 6: 에러 피드백 패턴 ✅ 잘된 점
- **현재 상태:** 모든 fetch 호출에서 성공/실패 케이스별 `showToast()` 호출. 버튼 로딩 상태 관리.
- **확인할 파일:** `upload.html`, `exports.html` 전체 fetch 블록

---

### 프론트 포인트 7: XSS 방지 ✅ 잘된 점 (일부)
- **현재 상태:** `lookup_reorder.js`의 `escapeHtml()` 함수로 DOM 삽입 시 이스케이프
- **확인할 파일:** `app/static/js/lookup_reorder.js: escapeHtml()`
- **주의:** `innerHTML` 직접 사용 부분에서 일관성 확인 필요

---

## 4. 잘된 점 요약

| 항목 | 내용 |
|------|------|
| N+1 방지 | 업로드 시 DB 1회 조회로 전체 매핑 처리 |
| Savepoint 패턴 | 개별 실패가 전체 롤백 방지 |
| 임시 파일 정리 | finally 블록으로 항상 삭제 보장 |
| 에러 피드백 | 모든 액션에 토스트 알림 + 상세 결과 표시 |
| 드래그앤드롭 취소 | snapshot 패턴으로 되돌리기 지원 |
| 메일 인증 폴링 | clearInterval 정리로 메모리 누수 방지 |
| 중복 방지 | DB 유니크 제약 + 애플리케이션 레벨 중복 처리 이중화 |

---

## 5. 개선 가능 포인트 요약

| 항목 | 내용 | 우선순위 |
|------|------|---------|
| exports/ 파일 정리 | 자동 삭제 또는 정리 정책 미정의 | 낮음 |
| 중복 Repository | master_repository.py와 lookup_repository.py 통합 | 낮음 |
| CDN 의존 | 로컬 정적 파일 번들링 | 중간 |
| 전체삭제 방어 | 재확인 UI 강화 | 중간 |
| 인증 없음 | 사내 배포 시 기본 인증 추가 고려 | 상황에 따라 |

---

## 6. 리스크 포인트 요약

| 리스크 | 영향도 | 발생 조건 |
|--------|--------|-----------|
| 은행 파일 형식 변경 | 높음 | KB/IBK가 엑셀 헤더 변경 시 |
| 끝4자리 충돌 | 중간 | 같은 은행 끝4자리 동일 카드 2명 이상 |
| 멀티 프로세스 배포 | 중간 | gunicorn 멀티 워커 사용 시 인증 상태 불공유 |
| 인증 없는 API | 높음 | 외부 네트워크 노출 시 |
| exports 디스크 누적 | 낮음 | 장기 운영 시 |
