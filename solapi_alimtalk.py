import hashlib
import hmac
import logging
import os
import re
import secrets
from datetime import datetime, timezone

import requests


logger = logging.getLogger(__name__)


def send_alimtalk(
    to: str,
    template_id: str,
    pf_id: str,
    variables: dict[str, str] | None = None,
) -> dict:
    """알림톡 한 건을 접수한다. success는 수신 완료가 아닌 SOLAPI 접수 성공이다.

    variables의 키는 승인된 템플릿의 변수명(예: #{이름})을 그대로 사용한다.
    FastAPI에서는 BackgroundTasks.add_task로 호출한다.
    타임아웃은 접수 여부가 불명확하므로 중복 발송 방지를 위해 재시도하지 않는다.
    """
    api_key = os.getenv("SOLAPI_KEY", "").strip()
    api_secret = os.getenv("SOLAPI_SECRET", "").strip()
    if not api_key or not api_secret:
        logger.warning("알림톡 발송 실패: SOLAPI_KEY / SOLAPI_SECRET 미설정")
        return {"success": False, "reason": "missing_credentials"}

    phone = re.sub(r"[\s()-]", "", to)
    if phone.startswith("+82"):
        phone = "0" + phone[3:]
    if not re.fullmatch(r"0[0-9]{8,10}", phone) or not template_id or not pf_id:
        logger.warning("알림톡 발송 실패: 수신번호 또는 템플릿/채널 ID 누락·오류")
        return {"success": False, "reason": "invalid_parameters"}

    date = datetime.now(timezone.utc).isoformat()
    salt = secrets.token_hex(16)
    signature = hmac.new(
        api_secret.encode(), (date + salt).encode(), hashlib.sha256
    ).hexdigest()
    authorization = (
        f"HMAC-SHA256 apiKey={api_key}, date={date}, "
        f"salt={salt}, signature={signature}"
    )
    message = {
        "to": phone,
        "type": "ATA",
        "country": "82",
        "kakaoOptions": {
            "pfId": pf_id,
            "templateId": template_id,
            "variables": variables or {},
            "disableSms": True,
        },
    }
    try:
        response = requests.post(
            "https://api.solapi.com/messages/v4/send-many/detail",
            headers={"Authorization": authorization},
            json={"messages": [message]},
            timeout=(3.05, 10),
        )
        response.raise_for_status()
        result = response.json()
    except requests.RequestException:
        # 응답 본문과 예외 메시지에는 개인정보가 포함될 수 있다.
        logger.warning("알림톡 발송 실패: SOLAPI HTTP/네트워크 오류")
        return {"success": False, "reason": "request_failed"}
    except ValueError:
        logger.warning("알림톡 발송 실패: SOLAPI JSON 응답 오류")
        return {"success": False, "reason": "invalid_response"}

    if not isinstance(result, dict):
        return {"success": False, "reason": "invalid_response"}
    group = result.get("groupInfo") or {}
    count = group.get("count") if isinstance(group, dict) else None
    if (
        result.get("failedMessageList")
        or not isinstance(count, dict)
        or count.get("registeredSuccess") != 1
    ):
        logger.warning("알림톡 발송 실패: SOLAPI 접수 실패")
        return {"success": False, "reason": "registration_failed"}
    return {"success": True, "group_id": group.get("groupId")}
