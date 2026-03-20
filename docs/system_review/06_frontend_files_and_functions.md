# 06. 프론트엔드 파일/컴포넌트/함수 단위 역할

## 1. 문서 목적
각 HTML 템플릿 파일과 JavaScript 함수 단위로 역할, 주요 이벤트, 연결 API를 설명합니다.

---

## 2. 파일별 역할 표

| 파일 | 역할 | 주요 함수/이벤트 | 연결된 API | 비고 |
|------|------|-----------------|-----------|------|
| `base.html` | 공통 레이아웃 | `showToast()` | - | 모든 페이지가 상속 |
| `upload.html` | 파일 업로드 화면 | drag/drop, `submit` 이벤트 | POST `/api/uploads` | 다중 파일 지원 |
| `transactions.html` | 거래내역 조회 | `remapAll()`, `deleteAllTransactions()` | POST remap, DELETE transactions | 필터는 GET form |
| `exports.html` | 엑셀 생성 + 메일 발송 | `generateFile()`, `downloadAllZip()`, `openMailDialog()`, `confirmSend()` | POST generate, download-all-zip, mail/send | 가장 복잡한 화면 |
| `card_users.html` | 카드 사용자 CRUD | `openModal()`, `editUser()`, `saveUser()`, `deleteUser()` | CRUD `/api/lookups/cards` | 모달 폼 |
| `projects.html` | 프로젝트 CRUD + 순서 | LookupReorder.init(), CRUD 함수 | CRUD + reorder `/api/lookups/projects` | lookup_reorder.js 연동 |
| `solutions.html` | 솔루션 CRUD + 순서 | 위와 동일 | CRUD + reorder `/api/lookups/solutions` | |
| `expense_categories.html` | 계정과목 CRUD + 순서 | 위와 동일 | CRUD + reorder `/api/lookups/accounts` | |
| `static/js/lookup_reorder.js` | 드래그앤드롭 순서 변경 | `LookupReorder.init()`, `enterReorder()`, `saveReorder()` | POST `/api/lookups/*/reorder` | 3개 마스터 공통 |

---

## 3. base.html

### 화면 책임
- 전체 레이아웃 구조 (사이드바 + 메인 영역)
- CSS 클래스 정의 (btn-primary, input-field 등)
- 전역 토스트 알림 제공

### 사이드바 구성
- 카드 오토 로고 + 서브타이틀
- 7개 메뉴 링크 (현재 경로에 따라 `.active` 클래스 자동 적용)
- `request.url.path` 비교로 현재 메뉴 하이라이팅

### 주요 함수

**`showToast(msg, type)`**
- **화면 책임:** 우하단 알림 표시
- **매개변수:** msg (문자열), type (success|error|warning|info)
- **동작:** div 생성 → opacity 전환 애니메이션 → 3.5초 후 자동 제거
- **연관:** 모든 페이지에서 호출

---

## 4. upload.html

### 화면 책임
파일 업로드 UI, 업로드 결과 표시

### 주요 이벤트

**파일 선택 (`fileInput.change`)**
- 선택된 파일명 표시 (복수 파일 시 개수 + 이름 목록)

**드래그앤드롭 (`dragover`, `dragleave`, `drop`)**
- 드래그 진입 시 테두리/배경 변경 (시각적 피드백)
- drop 시 `DataTransfer` API로 `fileInput.files` 동적 세팅

**폼 제출 (`submit`)**
- `FormData` 생성 → `files[]` 다중 파일 추가
- `fetch('POST /api/uploads', formData)`
- 응답 파싱 → 결과 패널 DOM 업데이트
- 성공/중복/오류 케이스별 토스트 표시

### 결과 표시 로직
```javascript
// 3가지 케이스 분기
if (skipped > 0 && success === 0 && !hasErrors)  → "중복 내역 포함" 경고
else if (hasErrors)                               → "일부 오류 발생" 경고
// 공통: 저장 성공(초록), 중복 스킵(노랑), 전체 행(파랑) 3개 카드로 표시
```

### 리뷰 포인트
- 버튼 비활성화/로딩 상태 잘 처리됨
- 에러 발생 시에도 다른 파일 결과 표시 가능 (개별 처리)

---

## 5. transactions.html

### 화면 책임
거래내역 필터 검색, 목록 표시, 재매핑/전체삭제

### 필터 폼
- `<form method="get" action="/transactions">` → GET 파라미터로 서버 전송
- 은행(select), 사용자명(text), 카드번호(text), 년월(text), 매핑상태(select)
- 서버에서 필터 조건 유지해 HTML 렌더링

### 주요 함수

**`remapAll()`**
```javascript
async function remapAll() {
  const res = await fetch('/api/transactions/remap', { method: 'POST' });
  const data = await res.json();
  showToast(`${data.remapped}건 재매핑 완료`, 'success');
  setTimeout(() => location.reload(), 1000);
}
```
- 호출 API: `POST /api/transactions/remap`
- 완료 후 페이지 리로드 (1초 지연)

**`deleteAllTransactions()`**
```javascript
async function deleteAllTransactions() {
  if (!confirm('모든 거래내역을 삭제하시겠습니까?...')) return;
  const res = await fetch('/api/transactions', { method: 'DELETE' });
  ...
}
```
- `confirm()` 대화상자로 재확인
- 호출 API: `DELETE /api/transactions`

### 리뷰 포인트
- 페이지네이션 링크에 filter_card_number 파라미터 누락 버그 있음 (이전 페이지 링크)
- 전체 삭제는 confirm으로만 방어 → 운영 환경에서 주의

---

## 6. exports.html (핵심 화면)

### 화면 책임
엑셀 파일 생성, 다운로드, Outlook 메일 발송 (가장 복잡한 화면)

### 주요 함수

**`generateFile(btn)`**
- 카드 단건 엑셀 생성 및 다운로드
- `data-*` 속성에서 카드 정보 읽음
- `POST /api/exports/generate` → 파일명 받음
- 임시 `<a>` 태그 생성으로 자동 다운로드
- 연결 API: `POST /api/exports/generate`, `GET /api/exports/download/{file}`

**`downloadAllZip()`**
- 테이블 전체 카드에 대해 ZIP 일괄 다운로드
- `querySelectorAll('.btn-generate')` → 모든 카드 정보 수집
- `POST /api/exports/download-all-zip`
- Blob API로 ZIP 파일 다운로드

**`openMailDialog()` / `openMailDialogForOne(btn)`**
- 전체 발송 또는 단건 발송 시작
- `_pendingSendCards` 변수로 발송 대상 관리 (null=전체, 배열=선택)
- `_checkAuthAndProceed()` → 인증 상태 확인 후 적절한 패널 표시

**`startAuth()`**
- `POST /api/mail/auth/start` → user_code, verification_url 수신
- Device Code 화면 표시
- `setInterval` 폴링 시작 (2초, `GET /api/mail/auth/status`)

**`confirmSend()`**
- 발송 확인 버튼 → `POST /api/mail/send`
- `_pendingSendCards || _getTableCards()` 발송 대상 결정
- 응답 → `_showResultPanel(data)`

**`_showPanel(name)`**
- 3개 패널(auth/send/result) 중 하나만 표시
- `['mail-auth-panel','mail-send-panel','mail-result-panel']` CSS 토글

**`_showResultPanel(data)`**
- 발송 결과 요약 (sent/failed/skipped) 카드 표시
- 상세 발송 내역 목록 표시

### 상태 변수
```javascript
let _pendingSendCards = null;  // null=전체, 배열=특정 카드
let _authPollTimer = null;     // setInterval 타이머 ID
```

### 리뷰 포인트
- `_pendingSendCards`가 전역 변수 → 다이얼로그 닫기 시 반드시 초기화 필요
- 인증 폴링 타이머 `_authPollTimer`는 `closeMailDialog()`에서 clearInterval 처리됨 (정상)
- 전체 카드 목록은 `_getTableCards()`로 DOM에서 읽음 → 서버 재조회 없음

---

## 7. card_users.html

### 화면 책임
CARD_USERS 테이블 조회, 신규 등록/수정/삭제

### 초기 렌더링
- Jinja2로 서버사이드 렌더링 (users 목록 → 테이블 생성)
- `tojson` 필터로 수정 버튼에 데이터 embed

```html
onclick='editUser({{ card_no | tojson }}, {{ user_data | tojson }})'
```

### 주요 함수

**`openModal()`**
- 등록 모달 열기 (폼 초기화)

**`editUser(cardNo, userData)`**
- 수정 모달 열기 (기존 데이터 폼에 채우기)
- `document.getElementById('edit-card-no').value = cardNo`로 ID 저장

**`saveUser()`** (실제 함수명 확인 필요)
- 등록/수정 분기 처리
- `edit-card-no` hidden input 값으로 신규/수정 판별
- 연결 API: POST 또는 PUT `/api/lookups/cards`

**`deleteUser(cardNo)`**
- confirm 후 `DELETE /api/lookups/cards/{cardNo}`

### 리뷰 포인트
- 등록/수정 후 페이지 리로드 방식 vs DOM 업데이트 방식 (확인 필요)
- 카드번호 `tojson` 처리로 특수문자 이스케이프

---

## 8. projects.html / solutions.html / expense_categories.html

### 화면 책임
마스터 데이터 CRUD + 드래그앤드롭 순서 변경

### Jinja2 데이터 전달 방식
```html
<script type="application/json" id="lookup-items-json">
  {{ lookup_reorder_items_json | safe }}
</script>
```
서버에서 JSON을 script 태그 안에 주입 → JS에서 파싱

### LookupReorder 연동
```javascript
LookupReorder.init({
  itemsScriptId: 'lookup-items-json',
  tbodyId: 'lookup-tbody',
  theadId: 'lookup-thead',
  apiReorder: '/api/lookups/projects/reorder',
  idType: 'string',
  nameLabel: '프로젝트',
  nameColumnTitle: '프로젝트명',
  onEdit: (row) => openEditModal(row),
  onDelete: (id) => deleteLookup(id),
});
```

### 리뷰 포인트
- 3개 페이지 구조 거의 동일 → LookupReorder 설정값만 다름
- 순서 저장 후 `window.location.reload()` (400ms 지연)로 서버 데이터 재로드

---

## 9. lookup_reorder.js (공통 JS 모듈)

### 화면 책임
PROJECTS/SOLUTIONS/EXPENSE_CATEGORIES 순서 편집 UI 공통 제공

### 상태
```javascript
let cfg = null;         // 설정 (init에서 주입)
let items = [];         // 현재 아이템 배열
let snapshot = null;    // 취소용 이전 상태 저장
let reorderMode = false; // 순서 편집 모드 여부
let openMenuIndex = null; // 열린 이동 메뉴 인덱스
let dragFromHandle = false; // 드래그 핸들에서 시작했는지
```

### 주요 함수

**`LookupReorder.init(config)`**
- 초기화: 설정 저장, 아이템 파싱, 테이블 초기 렌더링

**`enterReorder()`**
- 순서 편집 모드 진입
- snapshot 저장 (취소를 위해)
- 테이블 헤더/본체 재렌더링 (드래그 핸들, 이동 버튼 추가)

**`saveReorder()`**
- 현재 items 순서로 `POST /api/lookups/*/reorder` 호출
- 성공 시 0.4초 후 페이지 리로드

**`cancelReorder()`**
- snapshot으로 items 복원 → 일반 모드 복귀

**`moveItem(from, to)`**
- 배열 splice로 순서 변경 → 테이블 재렌더링

**드래그앤드롭**
- `dragstart/dragover/drop/dragend` 이벤트
- `dragFromHandle` 플래그로 핸들에서만 드래그 허용 (행 전체 드래그 방지)

### 리뷰 포인트
- IIFE 패턴 `(function() { ... })()` → 모듈 스코프 보호
- 취소 기능 있음 (snapshot 패턴)
- `escapeHtml()` 함수로 XSS 방지

---

## 10. 질문받기 쉬운 포인트

- **Q: 화면 데이터는 언제 서버에서 받아오나요?**  
  → 페이지 최초 로드 시 서버에서 Jinja2로 렌더링. 이후 CRUD는 fetch API로 부분 업데이트.

- **Q: 메일 발송 진행 중에 다른 작업을 할 수 있나요?**  
  → 다이얼로그가 모달이라 배경 클릭 불가. 메일 발송은 순차 처리.

- **Q: 순서 변경은 어떻게 저장되나요?**  
  → 드래그 완료 후 "저장" 버튼 클릭 시 서버 API 호출. 실시간 자동 저장 아님.
