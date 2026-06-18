import firebase_admin
from firebase_admin import credentials, messaging

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