import os

BASE_URL = os.environ.get("APPLIFT_SDK_API_BASE_URL", "https://python.exercise.applifting.cz/")

TOKEN_EXPIRATION_SECONDS = int(os.environ.get("TOKEN_EXPIRATION_SECONDS", 300))
TOKEN_EXPIRATION_BUFFER_SECONDS = int(os.environ.get("TOKEN_EXPIRATION_BUFFER_SECONDS", 5))
