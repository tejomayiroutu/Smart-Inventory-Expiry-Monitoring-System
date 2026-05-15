import os
from dotenv import load_dotenv


load_dotenv()


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-this")

    DB_USER = os.getenv("DB_USER", "root")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "")
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = os.getenv("DB_PORT", "3306")
    DB_NAME = os.getenv("DB_NAME", "expiry_tracker")
    
    SQLALCHEMY_DATABASE_URI = (
        f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    MAIL_SERVER = os.getenv("MAIL_SERVER", "smtp.gmail.com")
    MAIL_PORT = int(os.getenv("MAIL_PORT", 587))
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.getenv("MAIL_USERNAME", "")
    MAIL_PASSWORD = os.getenv("MAIL_PASSWORD", "")
    MAIL_DEFAULT_SENDER = os.getenv("MAIL_DEFAULT_SENDER", MAIL_USERNAME)

    # When True, expiry emails are printed to the terminal instead of using SMTP.
    # Set MAIL_CONSOLE=false in .env when you are ready to send real mail.
    MAIL_CONSOLE = os.getenv("MAIL_CONSOLE", "true").lower() in ("1", "true", "yes")

    # Daily digest (server local time). Set SCHEDULER_ENABLED=false to turn off jobs.
    SCHEDULER_ENABLED = os.getenv("SCHEDULER_ENABLED", "true").lower() in ("1", "true", "yes")
    SCHEDULER_HOUR = int(os.getenv("SCHEDULER_HOUR", "8"))
    SCHEDULER_MINUTE = int(os.getenv("SCHEDULER_MINUTE", "0"))

    # Flask-WTF (CSRF tokens in forms)
    WTF_CSRF_TIME_LIMIT = None
