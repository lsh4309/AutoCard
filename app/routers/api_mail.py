"""메일 발송 API"""
import logging
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services import mail_service
from app.services.transaction_service import get_cards_for_export

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/mail", tags=["mail"])


class MailSendRequest(BaseModel):
    year_month: str | None = None
    cards: list[dict] | None = None  # 없으면 해당 년월 전체 발송


@router.get("/auth/status")
def auth_status():
    """현재 인증 상태 + 토큰 유효 여부 반환 (폴링용)"""
    state = mail_service.get_auth_status()
    state["has_token"] = mail_service.is_authenticated()
    return state


@router.post("/auth/start")
def auth_start():
    """Device Code 인증 시작. verification_url과 user_code 반환."""
    if mail_service.is_authenticated():
        return {"status": "done", "message": "이미 인증되어 있습니다.", "has_token": True}
    result = mail_service.start_device_code_auth()
    return result


@router.post("/send")
def send_mails(body: MailSendRequest, db: Session = Depends(get_db)):
    """
    카드별 엑셀을 생성해 각 사용자 이메일로 발송.
    body.cards가 없으면 year_month 기준 전체 대상 발송.
    """
    if not mail_service.is_authenticated():
        raise HTTPException(
            status_code=401,
            detail="Outlook 인증이 필요합니다. 먼저 인증을 완료해주세요.",
        )

    cards = body.cards
    if not cards:
        cards = get_cards_for_export(db, body.year_month)

    if not cards:
        raise HTTPException(status_code=404, detail="발송할 대상이 없습니다.")

    try:
        results = mail_service.send_card_mails(db=db, cards=cards)
    except PermissionError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except Exception as e:
        logger.error(f"메일 발송 오류: {e}")
        raise HTTPException(status_code=500, detail=str(e))

    sent = sum(1 for r in results if r["status"] == "sent")
    failed = sum(1 for r in results if r["status"] == "failed")
    skipped = sum(1 for r in results if r["status"] == "skipped")

    return {
        "status": "ok",
        "sent": sent,
        "failed": failed,
        "skipped": skipped,
        "details": results,
    }
