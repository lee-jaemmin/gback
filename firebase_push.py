import json
import os
from pathlib import Path

import firebase_admin
from firebase_admin import credentials, messaging


def initialize_firebase() -> bool:
    if firebase_admin._apps: # 이미 초기화 되어있으면 True 반환. 중요한부분임.
        return True

    firebase_service_account_json = os.getenv("FIREBASE_SERVICE_ACCOUNT_JSON")
    # 이 방식은 railway 환경변수에 직접 json을 통째로 넣어야함.

    if firebase_service_account_json:
        try:
            service_account_info = json.loads(firebase_service_account_json) # "json" (문자열) -> python dict
            cred = credentials.Certificate(service_account_info)
            firebase_admin.initialize_app(cred)
            return True
        except Exception as e:
            print(f"Firebase initialization failed from env: {e}")
            return False

    local_path = Path("secrets/firebase-service-account.json")
    # 로컬 개발 시 이 파일을 읽으라는 뜻

    if local_path.exists():
        try:
            cred = credentials.Certificate(str(local_path))
            firebase_admin.initialize_app(cred)
            return True
        except Exception as e:
            print(f"Firebase initialization failed from local file: {e}")
            return False

    print("Firebase service account is not configured. Push notification is disabled.")
    return False


def send_push_to_token(
    token: str,
    title: str,
    body: str,
    data: dict[str, str] | None = None, #3.10이후 문법. = Optional[dict[str, str]]
):
    if not initialize_firebase():
        return {
            "success": False,
            "reason": "Firebase service account is not configured",
        }

    message = messaging.Message(
        notification=messaging.Notification(
            title=title,
            body=body,
        ), # 폰 알림창에서 보이는 부분
        data=data or {}, # data=None -> {}생성. 안전성.
        token=token,
    )

    response = messaging.send(message) # message id return.

    return {
        "success": True,
        "response": response,
    } # 알아보기 쉽게 반환값을 dict로.