# Azure AD 앱 등록 가이드 (PineFlow 메일 발송 설정)

PineFlow의 메일 발송 기능은 Microsoft Graph API를 사용합니다.
최초 1회 Azure AD 앱 등록이 필요하며, 이후에는 별도 설정 없이 사용 가능합니다.

---

## 1. 앱 등록

1. [portal.azure.com](https://portal.azure.com) 에 회사 계정으로 로그인
2. 상단 검색창에 `앱 등록` 검색 → 클릭
3. **"+ 새 등록"** 클릭
4. 아래와 같이 입력 후 **"등록"** 클릭

| 항목 | 값 |
|------|-----|
| 이름 | `PineFlow` (임의 지정 가능) |
| 지원되는 계정 유형 | 이 조직 디렉터리의 계정만 (단일 테넌트) |
| 리디렉션 URI | 비워두기 |

5. 등록 완료 후 **개요** 화면에서 아래 두 값을 복사해 보관

```
애플리케이션(클라이언트) ID  →  AZURE_CLIENT_ID
디렉터리(테넌트) ID          →  AZURE_TENANT_ID
```

---

## 2. API 권한 추가

1. 왼쪽 메뉴 **"API 사용 권한"** 클릭
2. **"+ 권한 추가"** → **"Microsoft Graph"** → **"위임된 권한"**
3. 검색창에 `Mail.Send` 입력 → 체크
4. **"권한 추가"** 클릭

> 결과: `User.Read`, `Mail.Send` 두 항목이 목록에 표시되면 정상

---

## 3. 리디렉션 URI 추가

1. 왼쪽 메뉴 **"인증"** 클릭
2. **"+ 플랫폼 추가"** → **"모바일 및 데스크톱 애플리케이션"** 선택
3. 아래 URI 체크 후 **"구성"** 클릭

```
https://login.microsoftonline.com/common/oauth2/nativeclient
```

---

## 4. 공용 클라이언트 흐름 허용

1. 왼쪽 메뉴 **"인증"** 클릭
2. 상단 **"설정"** 탭 클릭
3. **"고급 설정"** 섹션에서 **"공용 클라이언트 흐름 허용"** → **"예"** 선택
4. **"저장"** 클릭

> 이 설정이 없으면 `AADSTS7000218` 오류 발생

---

## 5. docker-compose.yml 환경변수 설정

`docker-compose.yml` 의 backend 서비스 environment 항목에 아래 값 추가:

```yaml
EMAIL_SENDER: 발신자이메일@pine-partners.com
AZURE_CLIENT_ID: (1단계에서 복사한 클라이언트 ID)
AZURE_TENANT_ID: (1단계에서 복사한 테넌트 ID)
```

---

## 6. 최초 인증 (1회만)

1. PineFlow 접속 → 내역 업로드 후 **"메일 발송"** 버튼 클릭
2. 인증 다이얼로그에서 접속 주소와 코드 확인
3. 브라우저에서 접속 주소 열기 → 코드 입력 → 회사 계정으로 로그인
4. "디바이스에서 애플리케이션에 로그인하셨습니다" 메시지 확인
5. PineFlow 화면이 자동으로 수신자 목록으로 전환됨

> 인증 토큰은 `/app/data/o365_token.json` 에 저장되며, 만료 시 자동 갱신됩니다.
> 컨테이너를 재시작해도 토큰은 유지됩니다.

---

## 현재 등록된 앱 정보 (파인트리파트너스)

| 항목 | 값 |
|------|-----|
| 앱 이름 | pineflow_test |
| AZURE_CLIENT_ID | `24d5f24b-e4e0-45c5-ac49-9a5d5b847b85` |
| AZURE_TENANT_ID | `0ed5be46-f0d7-43ab-9203-c52042f64f1f` |
| EMAIL_SENDER | `ihyeon.yun@pine-partners.com` |
