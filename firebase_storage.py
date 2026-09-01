import os

from firebase_admin import storage

from firebase_push import initialize_firebase
# FASTAPI가 어느 Firebase Storage에 접근할 지 결정

def get_storage_bucket():
    if not initialize_firebase():
        raise RuntimeError("Firebase initialization failed")

    bucket_name = os.getenv("FIREBASE_STORAGE_BUCKET")
    if not bucket_name:
        raise RuntimeError("FIREBASE_STORAGE_BUCKET is not configured")

    return storage.bucket(bucket_name)
