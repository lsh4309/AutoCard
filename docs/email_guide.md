법카자동화 Outlook 메일 전송 기능 설계문서 v1.0
1. 목적

법카자동화 웹페이지에서 카드 사용 결과 파일을 법카 사용자 이메일로 전송하는 기능을 추가한다.
이 기능은 Outlook 데스크톱 자동화나 SMTP 계정/비밀번호 방식이 아니라, Microsoft Graph API + Microsoft Entra 앱 등록 + 서버 백엔드 자동 발송 구조로 설계한다. Microsoft는 Exchange Online의 SMTP AUTH Basic 인증을 2026년 3월 제거한다고 안내하고 있고, Graph의 sendMail은 애플리케이션 권한으로 사용할 수 있으므로, 장기 운영 관점에서 Graph 기반이 더 적합하다.

2. 범위

이번 기능의 범위는 아래와 같다.

결과 파일 생성 이후, 사용자별 수신 이메일로 메일 발송

발송 전 미리보기

발송 이력 저장

성공/실패 상태 조회

실패 건 재시도

첨부파일 용량 정책 적용

관리자용 이메일 매핑 검증 기능

이번 1차 범위에서는 "시스템이 전용 발신 메일박스로 자동 전송" 하는 구조를 기준으로 한다. 사용자가 자신의 Microsoft 계정으로 직접 로그인해서 자기 이름으로 보내는 방식은 1차 범위에서 제외한다. 사용자별 로그인 방식은 delegated access + authorization code flow가 필요하며, 이 경우 리디렉션 URI와 사용자 로그인 흐름이 별도로 필요하다.

3. 핵심 설계 원칙
3.1 인증 방식

권장 방식은 app-only(client credentials) 이다. 이 흐름은 사용자 로그인 없이 애플리케이션 자체 권한으로 토큰을 받아 Graph를 호출하는 방식이며, Microsoft는 이런 서버/데몬성 시나리오에 client credentials 흐름을 안내한다. 또한 프로덕션에서는 client secret보다 certificate credentials 또는 federated credentials 사용을 권장한다.

3.2 발신 메일박스

발신자는 개인 계정이 아니라 전용 시스템 메일박스로 고정한다. 예: card-auto@pine-partners.com
Graph sendMail은 application permission으로 사용할 수 있고, /users/{id | userPrincipalName}/sendMail 경로를 지원한다. 또한 기본적으로 Sent Items에 저장된다. 성공 응답은 202 Accepted 이며, 이는 "요청 수락"이지 "최종 배달 완료"를 의미하지 않는다.

3.3 권한 최소화

애플리케이션에 Mail.Send application permission을 부여하되, 앱이 접근 가능한 사서함 범위를 전용 발신 메일박스 1개로 제한해야 한다. Microsoft는 Exchange Online의 RBAC for Applications(App RBAC) 로 리소스 범위를 제한하는 방식을 안내하고 있고, 기존 Application Access Policy는 레거시로 안내된다.

3.4 첨부파일 정책

Graph는 JSON sendMail 호출에 파일 첨부를 포함할 수 있지만, 일반 첨부 API는 3MB 미만 제한이 있다. 3MB~150MB는 draft message + upload session 방식이 필요하며, 이 경로는 Mail.ReadWrite 권한이 필요하다. 따라서 1차 MVP는 3MB 이하 첨부만 허용하고, 초과 시에는 다운로드 링크 메일 또는 추후 확장 방식으로 처리하는 것이 안전하다.

4. 목표 아키텍처

구조는 아래와 같다.

사용자가 웹에서 결과 파일 생성

시스템이 카드/사용자 기준으로 수신 이메일 후보 조회

발송 미리보기 화면 제공

사용자가 "발송 요청" 실행

서버가 발송 배치와 발송 항목을 DB에 저장

별도 워커가 Graph API로 순차 발송

성공/실패 상태를 DB에 기록

화면에서 이력 조회 및 실패 건 재시도

중요한 점은, 웹 요청 안에서 전체 메일을 동기식으로 다 보내지 않는 것이다. Graph sendMail은 202 Accepted 를 반환하고 실제 배달 처리는 이후 단계에서 이루어지므로, 웹 요청-응답과 발송 처리를 분리한 DB 기반 outbox/queue 방식이 운영상 훨씬 안정적이다.

5. 권장 기능 범위 상세
5.1 1차 MVP

전용 발신 메일박스 1개 사용

수신자는 내부 도메인(@pine-partners.com)만 허용

첨부파일 3MB 이하만 허용

미리보기 / 발송 / 이력 / 재시도 지원

템플릿 제목/본문 사용

발송 로그 저장

실패 건 상세 사유 표시

5.2 2차 확장

3MB 초과 파일 upload session 지원

HTML 템플릿 고도화

예약 발송

관리자 승인 후 발송

조직도/인사 마스터 기반 이메일 자동 동기화

다운로드 링크 방식 병행

6. 데이터 설계

현재 화면에서는 사용자이름@pine-partners.com 형태로 이메일을 계산해서 쓰고 있지만, 실제 발송 기준값은 명시적 DB 컬럼으로 관리해야 한다.
이유는 이름 중복, 이름 변경, 실제 메일 alias 불일치, 퇴사/휴직/겸직 등의 오발송 리스크 때문이다.

6.1 사용자 이메일 마스터

권장안은 user_master 분리지만, 빠른 1차 구현이라면 현재 card_master 기반으로 시작해도 된다.

권장 컬럼:

user_name

email

email_source (manual, derived, imported)

email_verified_yn

active_yn

updated_at

1차 현실안:

초기값은 user_name + "@pine-partners.com" 으로 자동 생성

관리자 화면에서 검토 후 email_verified_yn = Y 로 확정

실제 발송은 verified email 만 사용

미확정 건은 발송 대상에서 제외

6.2 발송 배치 테이블

mail_send_batch

id

batch_type (result_file_send)

sender_mailbox

subject_template

body_template

requested_by

requested_at

status (draft, pending, sending, completed, partial_failed, failed)

total_count

success_count

fail_count

created_at

updated_at

6.3 발송 항목 테이블

mail_send_item

id

batch_id

card_no

user_name

recipient_email

recipient_email_verified_yn

file_name

file_path

file_size

mail_subject

mail_body

status (pending, sending, sent, failed, skipped)

retry_count

last_error_code

last_error_message

requested_at

sent_at

created_at

updated_at

6.4 중복 방지

권장 제약:

(batch_id, recipient_email, file_path) unique

또는 (recipient_email, file_hash, logical_period) unique

이렇게 해야 같은 파일을 같은 사용자에게 같은 배치에서 중복 발송하지 않는다.

7. 업무 프로세스 설계
7.1 이메일 매핑 준비

card_master 에서 사용자명 조회

email 값이 있으면 우선 사용

없으면 user_name@pine-partners.com 후보 생성

관리자 화면에서 검토/수정

검증 완료된 사용자만 실제 발송 허용

7.2 발송 미리보기

사용자가 결과 파일 생성 후 "메일 발송" 화면으로 이동하면 아래 항목을 보여준다.

카드번호

사용자명

수신 이메일

이메일 검증 여부

첨부파일명

파일 크기

발송 가능 여부

제외 사유

7.3 발송 요청

사용자가 "전체 발송" 또는 "선택 발송" 클릭 시:

서버가 발송 대상 검증

mail_send_batch 생성

각 건별 mail_send_item 생성

상태를 pending 으로 저장

워커가 배치를 처리

7.4 워커 발송

워커는 pending 항목을 읽어서 다음 순서로 처리한다.

상태를 sending 으로 변경

Graph access token 획득

/users/{sender_upn}/sendMail 호출

성공 시 sent

실패 시 failed, 에러 코드/메시지 저장

재시도 대상이면 retry_count + 1

Graph sendMail은 application permission에서 Mail.Send 를 사용하며, 202 Accepted 를 반환한다. 기본적으로 Sent Items에 저장된다.

7.5 실패 처리

실패 사유 예시:

이메일 미검증

수신 이메일 형식 오류

첨부파일 없음

첨부파일 용량 초과

Graph 인증 실패

권한 부족

Graph 일시적 오류

속도 제한(throttling)

재시도 정책:

1차: 즉시 재시도 없음

2차: 수동 재시도 버튼

추후: 지수 백오프 자동 재시도

8. 인증/권한 설계 상세
8.1 Entra 앱 등록

앱 유형: single-tenant

권한: Microsoft Graph Mail.Send application permission

운영 권장 자격증명: certificate

개발/로컬 한정: client secret 가능

Microsoft는 앱 등록 시 프로덕션 앱에 client secret보다 certificate credentials 또는 federated credentials 사용을 권장한다.

8.2 왜 redirect URI 중심 구조가 아닌가

현재 요구사항은 "사용자 각자가 로그인해서 보내기" 가 아니라 "시스템이 서버에서 자동 발송" 이다.
리디렉션 URI가 핵심이 되는 구조는 delegated access + authorization code flow 에서 필요하다. 이 흐름은 Microsoft 로그인 후 앱으로 돌아오는 콜백 경로가 필요하다. 반면 지금은 사용자 없는 app-only 접근이 더 적합하다.

8.3 메일박스 범위 제한

앱에 Mail.Send application permission을 주면 원칙적으로 조직 내 사용자 메일 발송 권한이 넓게 열릴 수 있으므로, Exchange Online에서 App RBAC 으로 card-auto@pine-partners.com 같은 발신 전용 사서함으로 범위를 제한해야 한다. 레거시인 Application Access Policy는 신규 구성이 아니라면 권장하지 않는다.

9. 백엔드 설계
9.1 모듈 구성 권장

현재는 CARD_AUTO 단일 폴더 기준이므로, 구조는 과하게 쪼개지 말고 아래 정도가 적당하다.

config.py

services/mail_graph_service.py

services/mail_template_service.py

services/mail_queue_service.py

routers/mail.py

models.py 또는 mail 관련 model 파일

jobs/mail_sender.py

templates/mail/ 또는 DB 템플릿

9.2 환경변수

권장 .env 항목:

MS_TENANT_ID

MS_CLIENT_ID

MS_CLIENT_SECRET 또는 인증서 경로/식별값

OUTLOOK_SENDER_UPN

MAIL_ALLOWED_DOMAIN=pine-partners.com

MAIL_ATTACHMENT_MAX_MB=3

MAIL_SEND_ENABLED=true

MAIL_RETRY_MAX=3

9.3 권장 발송 서비스 책임 분리

mail_graph_service

토큰 획득

Graph API 호출

예외 변환

mail_template_service

제목/본문 렌더링

변수 치환

기본 템플릿 관리

mail_queue_service

배치 생성

항목 생성

상태 변경

실패/재시도 처리

9.4 토큰 획득 방식

raw HTTP로 직접 구현할 수도 있지만, Microsoft는 가능한 경우 MSAL 사용을 권장한다. 따라서 Python에서는 MSAL 기반으로 토큰을 받고, 실제 메일 전송은 httpx 또는 requests 로 Graph REST 호출하는 방식이 가장 단순하다.

9.5 워커 방식

1차 구현에서는 Redis/Celery까지 가지 말고, DB 기반 outbox + 별도 워커 커맨드 구조를 권장한다.

예:

웹앱: 발송 요청 저장만 수행

워커: python -m ...mail_sender 형태로 주기 실행

운영: 작업 스케줄러/cron/systemd/supervisor 중 하나로 주기 실행

이 구조가 FastAPI BackgroundTasks 보다 낫다. 이유는 서버 재시작, 중복 실행, 상태 추적, 장애 복구가 더 쉽기 때문이다.

10. API 설계

권장 엔드포인트는 아래와 같다.

10.1 이메일 후보 조회

GET /api/mail/preview?result_batch_id=...

응답:

대상 목록

사용자명

카드번호

후보 이메일

검증 여부

파일명

파일 크기

발송 가능 여부

제외 사유

10.2 이메일 매핑 수정

PUT /api/mail/user-email

요청:

user_name

email

email_verified_yn

10.3 발송 요청

POST /api/mail/send

요청:

result_batch_id

selected_items

subject_template

body_template

응답:

mail_batch_id

status=pending

total_count

10.4 발송 이력 조회

GET /api/mail/batches
GET /api/mail/batches/{batch_id}

10.5 실패 건 재시도

POST /api/mail/batches/{batch_id}/retry
또는
POST /api/mail/items/{item_id}/retry

11. 프론트 설계
11.1 화면 1: 메일 발송 미리보기

컬럼 예시:

선택 체크박스

카드번호

사용자명

수신 이메일

이메일 상태

파일명

파일 크기

발송 가능

제외 사유

버튼:

이메일 자동생성

이메일 검증 반영

선택 발송

전체 발송

테스트 발송

11.2 화면 2: 발송 결과

상단:

배치 ID

요청자

요청 시각

전체/성공/실패 수

하단 목록:

사용자명

이메일

상태

에러 메시지

재시도 버튼

11.3 화면 3: 사용자 이메일 관리

사용자명 검색

이메일 수정

검증 여부 체크

일괄 자동생성

미검증 목록 보기

12. 메일 본문/제목 정책

권장 제목 예시:
[법인카드 자동화] {yyyy-mm} 사용내역 결과파일 안내

권장 본문 예시:

인사말

첨부파일 안내

문의처

자동발송 문구

1차는 plain text 또는 단순 HTML로 충분하다.
본문 템플릿 변수:

user_name

period

card_last4

file_name

13. 첨부파일 정책
13.1 1차 정책

첨부파일 3MB 이하만 허용

초과 시 failed 또는 skipped

에러 메시지에 "용량 초과로 링크 전송 필요" 표시

13.2 2차 확장

3MB~150MB 파일을 지원하려면 아래 플로우로 바꿔야 한다.

draft message 생성

upload session 생성

파일 chunk upload

draft send

이 경로는 Mail.ReadWrite 권한이 필요하고 구현 복잡도가 증가한다. Microsoft 문서도 대용량 첨부는 upload session 방식으로 설명한다.

14. 보안 설계

client secret를 코드 저장소에 커밋 금지

운영은 certificate credentials 권장

.env 또는 서버 비밀 저장소 사용

발신 메일박스 범위 제한 필수

수신 도메인 allowlist 적용

미검증 이메일 발송 금지

로그에 첨부파일 원문/민감정보 전체 저장 금지

카드번호는 화면/로그에서 끝 4자리만 표시

파일 경로는 상대경로/내부 식별자로 저장

테스트/운영 발송 모드 분리

Microsoft는 프로덕션 앱에서 client secret보다 certificate/federated credentials 사용을 권장한다.

15. 운영/장애 대응 설계
15.1 상태값

배치:

draft

pending

sending

completed

partial_failed

failed

항목:

pending

sending

sent

failed

skipped

15.2 운영 지표

일일 발송 건수

성공률

실패율

평균 처리시간

재시도 건수

이메일 미검증 건수

15.3 장애 시나리오

Entra 자격증명 만료

관리자 동의 누락

App RBAC 미설정

첨부파일 누락

결과파일 경로 오류

Graph throttling

네트워크 장애

15.4 운영 대응

실패 배치 조회 화면 제공

항목별 재시도 지원

테스트 수신자 1인 대상 테스트 발송 지원

발송 기능 on/off 환경변수 제공

16. 테스트 설계
16.1 단위 테스트

이메일 주소 검증

템플릿 렌더링

파일 크기 검증

발송 대상 필터링

상태 전이 로직

16.2 통합 테스트

가짜 Graph 응답 목킹

성공 202 처리

4xx/5xx 실패 처리

중복 발송 방지

재시도 처리

Graph sendMail 성공 시 202 Accepted 를 반환하고, 이는 요청 수락이지 최종 배달 완료는 아니라는 점을 테스트와 UI 문구에 반영해야 한다.

16.3 운영 테스트

테스트 메일박스 1개 준비

내부 사용자 2~3명 대상 시범 발송

1MB 이하 파일

3MB 근접 파일

3MB 초과 파일

미검증 이메일

없는 파일 경로

17. 구현 우선순위
1순위

DB 컬럼/테이블 추가

이메일 매핑 UI

미리보기 API/UI

발송 배치 생성 API

Graph app-only 발송 서비스

워커

이력 조회/재시도

2순위

HTML 템플릿

테스트 발송

관리자 발송 승인

링크 전송 모드

3순위

대용량 첨부 upload session

예약 발송

고급 리포트/통계
