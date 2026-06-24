import firebase_admin
from firebase_admin import credentials, messaging
import os
import json

firebase_service_account_json = os.getenv("FIREBASE_SERVICE_ACCOUNT_JSON")

if firebase_service_account_json:
    # Railway에서는 서비스 계정 JSON 문자열을 환경변수로 넣습니다.
    service_account_info = json.loads(firebase_service_account_json)
    cred = credentials.Certificate(service_account_info)
else:
    # 로컬 개발에서는 기존 파일 경로를 그대로 사용합니다.
    cred = credentials.Certificate("secrets/firebase-service-account.json")

if not firebase_admin._apps:
    firebase_admin.initialize_app(cred)

def send_push_to_token(
    token: str,
    title: str,
    body: str,
    data: dict[str, str] | None = None,
):
    message = messaging.Message(
        notification=messaging.Notification(
            title=title,
            body=body,
        ),
        data=data or {},
        token=token,
    )

    return messaging.send(message)