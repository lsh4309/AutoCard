"""거래 데이터 검증 서비스"""
from app.models import Transaction


FLEX_VALID_VALUES = {"O", "X"}


def validate_transaction(tx: Transaction) -> tuple[str, str]:
    """
    단건 거래 검증.
    Returns: (status, message)  status: "ok" | "warning" | "error"
    """
    issues = []

    if tx.mapping_status == "unmapped":
        issues.append("카드 사용자 미매핑")

    if not tx.project_name:
        issues.append("프로젝트명 미입력")

    if not tx.solution_name:
        issues.append("솔루션 미입력")

    if not tx.account_subject:
        issues.append("계정과목/지출내역 미입력")

    if tx.flex_pre_approved and tx.flex_pre_approved not in FLEX_VALID_VALUES:
        issues.append(f"Flex 사전승인 값 오류 (입력값: {tx.flex_pre_approved})")

    if not issues:
        return "ok", ""

    # 사용자 미매핑은 error, 나머지는 warning
    if "카드 사용자 미매핑" in issues:
        return "error", " / ".join(issues)
    return "warning", " / ".join(issues)


def validate_all(transactions: list[Transaction]) -> list[Transaction]:
    """목록 일괄 검증 후 status 업데이트 (DB commit은 호출자에서)"""
    for tx in transactions:
        status, msg = validate_transaction(tx)
        tx.validation_status = status
        tx.validation_message = msg
    return transactions
