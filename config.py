import os
from datetime import timedelta

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key")
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL", "sqlite:///af_imperiya.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # file uploads
    UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), "uploads")
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024

    # telegram
    TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    TELEGRAM_DEFAULT_CHAT_ID = os.environ.get("TELEGRAM_DEFAULT_CHAT_ID", "")

    REMEMBER_COOKIE_DURATION = timedelta(days=7)
