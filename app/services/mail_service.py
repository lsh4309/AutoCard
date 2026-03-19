"""Outlook 메일 발송 서비스 - Microsoft Graph API (Device Code Flow)"""
import base64
import json
import logging
import threading
from pathlib import Path
from typing import Any

import msal
import requests

from app.config import (
    AZURE_CLIENT_ID,
    AZURE_TENANT_ID,
    EMAIL_SENDER,
    TOKEN_CACHE_PATH,
    EXPORT_DIR,
)
from app.services.excel_export_service import generate_card_excel

logger = logging.getLogger(__name__)

GRAPH_SCOPES = ["https://graph.microsoft.com/Mail.Send"]
GRAPH_SEND_URL = f"https://graph.microsoft.com/v1.0/users/{EMAIL_SENDER}/sendMail"

# Device Code 인증 진행 상태 (스레드 공유)
_auth_state: dict[str, Any] = {
    "status": "idle",       # idle | pending | done | error
    "message": "",          # 사용자에게 보여줄 안내 메시지
    "verification_url": "", # https://microsoft.com/devicelogin
    "user_code": "",        # 입력할 코드
}
_auth_lock = threading.Lock()


# ────────────────────────────────────────────────────────────────
# 내부 유틸
# ────────────────────────────────────────────────────────────────

def _build_app() -> msal.PublicClientApplication:
    cache = msal.SerializableTokenCache()
    if TOKEN_CACHE_PATH.exists():
        cache.deserialize(TOKEN_CACHE_PATH.read_text(encoding="utf-8"))

    app = msal.PublicClientApplication(
        client_id=AZURE_CLIENT_ID,
        authority=f"https://login.microsoftonline.com/{AZURE_TENANT_ID}",
        token_cache=cache,
    )
    return app, cache


def _save_cache(cache: msal.SerializableTokenCache) -> None:
    if cache.has_state_changed:
        TOKEN_CACHE_PATH.write_text(cache.serialize(), encoding="utf-8")


def _get_token_silent() -> str | None:
    """저장된 토큰으로 조용히 갱신 시도. 없으면 None 반환."""
    try:
        app, cache = _build_app()
        accounts = app.get_accounts()
        if not accounts:
            return None
        result = app.acquire_token_silent(GRAPH_SCOPES, account=accounts[0])
        _save_cache(cache)
        if result and "access_token" in result:
            return result["access_token"]
    except Exception as e:
        logger.warning(f"토큰 자동 갱신 실패: {e}")
    return None


def _send_graph_mail(token: str, to_email: str, subject: str, body_html: str, attachment_path: Path) -> None:
    """Graph API로 메일 1건 발송. 실패 시 예외 raise."""
    with open(attachment_path, "rb") as f:
        content_bytes = base64.b64encode(f.read()).decode("utf-8")

    payload = {
        "message": {
            "subject": subject,
            "body": {"contentType": "HTML", "content": body_html},
            "toRecipients": [{"emailAddress": {"address": to_email}}],
            "attachments": [
                {
                    "@odata.type": "#microsoft.graph.fileAttachment",
                    "name": attachment_path.name,
                    "contentBytes": content_bytes,
                }
            ],
        },
        "saveToSentItems": "true",
    }

    resp = requests.post(
        GRAPH_SEND_URL,
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        json=payload,
        timeout=30,
    )
    if resp.status_code not in (200, 202):
        raise RuntimeError(f"Graph API 오류 [{resp.status_code}]: {resp.text}")


# ────────────────────────────────────────────────────────────────
# 공개 인터페이스
# ────────────────────────────────────────────────────────────────

def get_auth_status() -> dict:
    """현재 인증 상태 반환 (폴링용)"""
    with _auth_lock:
        return dict(_auth_state)


def is_authenticated() -> bool:
    """저장된 유효 토큰 존재 여부"""
    return _get_token_silent() is not None


def start_device_code_auth() -> dict:
    """
    Device Code 인증 시작.
    백그라운드 스레드에서 진행하며, 상태는 _auth_state로 폴링 가능.
    반환값: { verification_url, user_code, message }
    """
    with _auth_lock:
        if _auth_state["status"] == "pending":
            return dict(_auth_state)

    def _run():
        with _auth_lock:
            _auth_state.update({"status": "pending", "message": "인증 대기 중...", "verification_url": "", "user_code": ""})

        try:
            app, cache = _build_app()
            flow = app.initiate_device_flow(scopes=GRAPH_SCOPES)
            if "user_code" not in flow:
                raise RuntimeError("Device flow 시작 실패: " + str(flow.get("error_description", flow)))

            with _auth_lock:
                _auth_state.update({
                    "status": "pending",
                    "message": flow.get("message", ""),
                    "verification_url": flow.get("verification_uri", "https://microsoft.com/devicelogin"),
                    "user_code": flow.get("user_code", ""),
                })

            # 사용자가 브라우저에서 로그인 완료할 때까지 대기 (최대 15분)
            result = app.acquire_token_by_device_flow(flow)
            _save_cache(cache)

            if "access_token" in result:
                with _auth_lock:
                    _auth_state.update({"status": "done", "message": "인증 완료", "verification_url": "", "user_code": ""})
            else:
                err = result.get("error_description", str(result))
                with _auth_lock:
                    _auth_state.update({"status": "error", "message": f"인증 실패: {err}"})

        except Exception as e:
            logger.error(f"Device Code 인증 오류: {e}")
            with _auth_lock:
                _auth_state.update({"status": "error", "message": str(e)})

    t = threading.Thread(target=_run, daemon=True)
    t.start()

    # 스레드가 flow 정보를 채울 때까지 짧게 대기
    import time
    for _ in range(30):
        time.sleep(0.3)
        with _auth_lock:
            if _auth_state["user_code"]:
                break

    with _auth_lock:
        return dict(_auth_state)


def send_card_mails(db, cards: list[dict]) -> list[dict]:
    """
    카드별 엑셀 생성 후 이메일 발송.
    cards: get_cards_for_export 결과 리스트 (user_email 필수)
    반환: [ { user_name, to, file_name, status, error } ]
    """
    token = _get_token_silent()
    if not token:
        raise PermissionError("인증이 필요합니다. 먼저 Outlook 인증을 진행해주세요.")

    results = []
    for card in cards:
        to_email = card.get("user_email")
        user_name = card.get("user_name", "")
        year_month = card.get("year_month", "")
        bank = card.get("bank", "")
        card_number = card.get("card_number", "")

        if not to_email:
            results.append({
                "user_name": user_name,
                "to": "",
                "file_name": "",
                "status": "skipped",
                "error": "이메일 주소 없음 (카드 사용자 마스터에서 이메일을 등록해주세요)",
            })
            continue

        try:
            file_path = generate_card_excel(
                db=db,
                card_number=card_number,
                bank=bank,
                year_month=year_month,
                user_name=user_name,
            )

            ym_display = f"{year_month[:4]}년 {year_month[4:]}월" if year_month and len(year_month) == 6 else year_month
            subject = f"[법인카드] {user_name}님 {ym_display} 카드 사용내역"
            body_html = _build_mail_body(user_name, ym_display, file_path.name)

            _send_graph_mail(token, to_email, subject, body_html, file_path)

            results.append({
                "user_name": user_name,
                "to": to_email,
                "file_name": file_path.name,
                "status": "sent",
                "error": "",
            })
            logger.info(f"메일 발송 성공: {user_name} → {to_email}")

        except Exception as e:
            logger.error(f"메일 발송 실패: {user_name} ({to_email}): {e}")
            results.append({
                "user_name": user_name,
                "to": to_email,
                "file_name": "",
                "status": "failed",
                "error": str(e),
            })

    return results


def _build_mail_body(user_name: str, ym_display: str, file_name: str) -> str:
    return f"""
<div style="font-family: 'Malgun Gothic', Arial, sans-serif; font-size: 14px; color: #222; max-width: 600px; line-height: 1.7;">
  <p style="margin: 0 0 16px 0;">{user_name} 님 안녕하세요,</p>
  <p style="margin: 0 0 8px 0;">{ym_display} 법인카드 사용내역 파일을 첨부 드립니다.</p>
  <p style="margin: 0 0 16px 0;">첨부 파일을 확인하시고 프로젝트명, 솔루션, 계정과목 등을 입력하여 회신 부탁드립니다.</p>

  <hr style="border: none; border-top: 1px solid #ddd; margin: 20px 0;" />

  <p style="font-size: 12px; color: #444; margin: 0; line-height: 1.8;">
    감사합니다.<br>
    이정숙 드림.<br>
    경영지원본부/매니저/팀장
  </p>
  <br>
  <p style="font-size: 12px; color: #444; margin: 0; line-height: 1.8;">
    Pinetree Partners <br>
    파인트리파트너스㈜ <br>
    Tel : 02-3775-1195 / Fax: 02-6305-5776<br>
    Mobile : 010-8973-6284<br>
    E-mail: <a href="mailto:jeongsook.lee@pine-partners.com" style="color: #1a73e8;">jeongsook.lee@pine-partners.com</a>
  </p>

  <p style="color: #aaa; font-size: 11px; margin-top: 20px; border-top: 1px solid #eee; padding-top: 10px;">
    본 메일은 법인카드 관리 시스템(Card Auto)에서 자동 발송되었습니다.<br>
    문의사항은 담당자에게 연락해 주세요.
  </p>
</div>
"""