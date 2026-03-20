# 05. 프론트엔드 전체 구조 (Frontend Overview)

## 1. 문서 목적
프론트엔드 전체 구조, 기술 스택, 화면 구성 방식, 사용자 액션이 API로 이어지는 패턴을 설명합니다.

---

## 2. 핵심 요약

| 항목 | 내용 |
|------|------|
| **렌더링 방식** | 서버사이드 렌더링 (Jinja2 템플릿) |
| **CSS 프레임워크** | Tailwind CSS (CDN 로드) |
| **JavaScript** | Vanilla JS (프레임워크 없음) |
| **아이콘** | Font Awesome 6.4.0 (CDN) |
| **상태관리** | 없음 (JS 전역 변수 + DOM 직접 조작) |
| **API 통신** | `fetch()` (Async/Await) |
| **페이지 수** | 8개 HTML 템플릿 |

---

## 3. 기술 스택 상세

```
Jinja2           - 서버에서 HTML 생성 (Python 변수 → HTML 삽입)
Tailwind CSS     - 유틸리티 기반 CSS 클래스 (CDN, 빌드 불필요)
Font Awesome     - 아이콘 라이브러리 (CDN)
Vanilla JS       - 별도 프레임워크 없이 순수 JS
fetch API        - 비동기 HTTP 요청
```

**왜 이 스택?**
- React/Vue 없이 Jinja2만으로 빠르게 개발 가능
- 초기 로드 시 서버에서 완성된 HTML 반환 → SEO/복잡성 불필요
- Tailwind CDN으로 별도 빌드 환경 없음
- 대화형 기능(업로드, 메일 발송)은 fetch로 처리

---

## 4. 디렉토리 구조

```
app/
├── templates/
│   ├── base.html               # ★ 공통 레이아웃 (모든 페이지가 상속)
│   ├── upload.html             # 파일 업로드 화면
│   ├── transactions.html       # 거래내역 조회/관리 화면
│   ├── exports.html            # 엑셀 생성 + 메일 발송 화면 (가장 복잡)
│   ├── card_users.html         # 카드 사용자 관리 화면
│   ├── projects.html           # 프로젝트 관리 화면
│   ├── solutions.html          # 솔루션 관리 화면
│   └── expense_categories.html # 계정과목 관리 화면
└── static/
    └── js/
        └── lookup_reorder.js   # 마스터 데이터 드래그앤드롭 순서 변경 공통 JS
```

---

## 5. 페이지 구성 방식

### 공통 레이아웃 (`base.html`)

모든 페이지는 `base.html`을 `{% extends %}`로 상속합니다.

```html
<!-- base.html 구조 -->
<html>
  <head>
    Tailwind CSS CDN
    Font Awesome CDN
    공통 스타일 (btn-primary, input-field 등 커스텀 클래스)
  </head>
  <body>
    <aside> 사이드바 네비게이션 </aside>
    <main>
      <header> 페이지 제목 영역 </header>
      <div> {% block content %} </div>
    </main>
    <div id="toast-container"> 전역 토스트 알림 </div>
    <script> showToast() 함수 </script>
    {% block scripts %}
  </body>
</html>
```

**공통 CSS 클래스:**
| 클래스 | 용도 |
|--------|------|
| `.btn-primary` | 파란색 주요 버튼 |
| `.btn-secondary` | 회색 보조 버튼 |
| `.btn-danger` | 빨간색 위험 버튼 |
| `.btn-success` | 초록색 성공 버튼 |
| `.input-field` | 인풋 필드 |
| `.select-field` | 셀렉트 박스 |
| `.badge-ok/warn/error/unmapped` | 상태 뱃지 |
| `.nav-link` | 사이드바 네비게이션 링크 |

---

## 6. 화면별 구성 및 특징

### upload.html (파일 업로드)
- **구성:** 드래그앤드롭 업로드 영역 + 결과 패널
- **특징:**
  - 드래그앤드롭 + 클릭 업로드 모두 지원
  - 다중 파일 선택 (`multiple` input)
  - 업로드 결과: 성공/중복/전체 건수를 카드 형태로 표시
  - 버튼 상태 관리 (로딩 중 비활성화)

### transactions.html (거래내역)
- **구성:** 필터 폼 + 액션 바 + 테이블 + 페이지네이션
- **특징:**
  - 필터는 서버사이드 렌더링 (form GET 전송)
  - 재매핑/전체삭제는 JS fetch로 처리
  - 매핑 상태에 따른 시각적 구분 (초록/빨간색)
  - 고정 헤더 테이블 (max-height, overflow)

### exports.html (결과 파일 생성)
- **구성:** 필터 + 카드 목록 테이블 + 메일 발송 다이얼로그
- **특징:**
  - 가장 복잡한 화면 (엑셀 생성 + ZIP + 메일 발송 모두 포함)
  - 메일 발송은 3단계 다이얼로그 UI (인증 → 확인 → 결과)
  - Device Code 인증 폴링 구현 (2초 간격 `setInterval`)
  - 전체 발송과 개별 발송 모두 지원

### card_users.html, projects.html, solutions.html, expense_categories.html
- **구성:** 목록 테이블 + 등록/수정 모달
- **특징:**
  - Jinja2로 초기 데이터 렌더링
  - CRUD는 JS fetch로 처리 (페이지 리로드 없음)
  - 프로젝트/솔루션/계정과목: 드래그앤드롭 순서 변경 (`lookup_reorder.js`)

---

## 7. 사용자 액션 → API 연결 패턴

### 패턴 1: 서버사이드 렌더링 (페이지 탐색)
```
사용자 → 링크 클릭 또는 폼 submit (GET)
  → 브라우저 페이지 이동
  → FastAPI pages.py 처리
  → Jinja2 템플릿 렌더링
  → 완성된 HTML 반환
```

### 패턴 2: 비동기 API 호출 (fetch)
```javascript
// 대표 패턴
const res = await fetch('/api/uploads', { method: 'POST', body: formData });
const data = await res.json();
if (!res.ok) {
  showToast(data.detail || '오류', 'error');
  return;
}
// DOM 업데이트
```

**모든 fetch 호출의 공통 패턴:**
1. 버튼 비활성화 + 로딩 인디케이터 표시
2. `fetch()` 호출
3. `res.ok` 확인
4. 성공: DOM 업데이트 + `showToast('완료', 'success')`
5. 실패: `showToast(error, 'error')`
6. `finally`: 버튼 원상 복구

---

## 8. 상태관리

React/Vue 없이 Vanilla JS로 상태를 관리합니다.

| 상태 | 관리 방식 |
|------|-----------|
| 업로드 결과 | DOM 직접 조작 (`innerHTML`) |
| 메일 발송 대상 | 모듈 수준 변수 `_pendingSendCards` |
| 인증 폴링 타이머 | `_authPollTimer = setInterval(...)` |
| 모달 열림/닫힘 | CSS `hidden` 클래스 토글 |
| 편집 중인 항목 | `<input type="hidden" id="edit-card-no">` (hidden input) |

---

## 9. 공통 컴포넌트/유틸 구조

### 토스트 알림 (`showToast`)
**위치:** `base.html`의 `<script>` 블록

```javascript
showToast('메시지', 'success|error|warning|info')
```

- 화면 우하단에 색상별 알림 표시
- 3.5초 후 자동 사라짐
- 페이지별 재사용 없이 base.html에서 전역 제공

### 드래그앤드롭 순서 변경 (`lookup_reorder.js`)
**위치:** `app/static/js/lookup_reorder.js`

프로젝트/솔루션/계정과목 페이지에서 공통으로 사용.  
아이템을 드래그해 순서 변경 → `POST /api/lookups/{type}/reorder` 호출.

---

## 10. 프론트에서 중요한 설계 포인트

### 포인트 1: 서버사이드 렌더링 + 점진적 향상
초기 페이지 로드는 서버에서 완전한 HTML 생성.  
CRUD/액션만 fetch API로 처리 → 첫 로드 빠르고 JS 없어도 기본 조회 가능.

### 포인트 2: 메일 발송 다이얼로그 상태 관리
3단계 패널 전환 (인증 → 확인 → 결과)을 `_showPanel()` 함수로 일관 관리.

```javascript
function _showPanel(name) {
  ['mail-auth-panel','mail-send-panel','mail-result-panel'].forEach(id => {
    document.getElementById(id).classList.add('hidden');
  });
  document.getElementById(name).classList.remove('hidden');
}
```

### 포인트 3: Device Code 인증 폴링
인증 완료 여부를 2초마다 서버에 체크.

```javascript
_authPollTimer = setInterval(async () => {
  const r = await fetch('/api/mail/auth/status');
  const s = await r.json();
  if (s.status === 'done' || s.has_token) {
    clearInterval(_authPollTimer);
    // → 발송 패널로 전환
  }
}, 2000);
```

### 포인트 4: Jinja2 tojson 필터
서버 데이터를 JS에서 직접 사용할 때 안전한 JSON 직렬화.

```html
<!-- card_users.html -->
onclick='editUser({{ card_no | tojson }}, {{ user_data | tojson }})'
```

---

## 11. 질문받기 쉬운 포인트

- **Q: React/Vue를 왜 안 쓰나요?**  
  → 사내 내부 도구로 규모가 크지 않아 Vanilla JS + Jinja2 SSR로 충분. 빌드 환경 불필요.

- **Q: 화면이 새로고침 없이 업데이트되는 건가요?**  
  → CRUD 작업은 fetch API 사용해 페이지 리로드 없이 처리. 필터 검색은 서버사이드 렌더링.

- **Q: 모바일에서도 쓸 수 있나요?**  
  → Tailwind CSS로 반응형 클래스 일부 사용 중이나, 주요 대상은 데스크톱 브라우저.

---

## 12. 확인 필요 사항

- 외부 CDN(Tailwind, Font Awesome) 의존 → 인터넷 없는 환경에서는 로딩 불가
- `lookup_reorder.js` 파일의 내용 확인 필요 (코드 분석 미완료)
