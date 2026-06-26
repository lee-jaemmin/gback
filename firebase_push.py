import json
import os
from pathlib import Path

import firebase_admin
from firebase_admin import credentials, messaging


def initialize_firebase() -> bool:
    if firebase_admin._apps:
        return True

    firebase_service_account_json = os.getenv("FIREBASE_SERVICE_ACCOUNT_JSON")

    if firebase_service_account_json:
        try:
            service_account_info = json.loads(firebase_service_account_json)
            cred = credentials.Certificate(service_account_info)
            firebase_admin.initialize_app(cred)
            return True
        except Exception as e:
            print(f"Firebase initialization failed from env: {e}")
            return False

    local_path = Path("secrets/firebase-service-account.json")

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
    data: dict[str, str] | None = None,
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
        ),
        data=data or {},
        token=token,
    )

    response = messaging.send(message)

    return {
        "success": True,
        "response": response,
    }