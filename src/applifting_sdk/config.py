import os

BASE_URL = os.getenv("OFFERS_API_BASE_URL", "https://python.exercise.applifting.cz/")

TOKEN_EXPIRATION_SECONDS = int(os.getenv("TOKEN_EXPIRATION_SECONDS", 300))
TOKEN_EXPIRATION_BUFFER_SECONDS = int(os.getenv("TOKEN_EXPIRATION_BUFFER_SECONDS", 5))
