import os

from dotenv import load_dotenv

load_dotenv()


SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER") or os.getenv("DEFAULT_FROM_EMAIL") or os.getenv("EMAIL_HOST_USER")
_raw_password = os.getenv("SMTP_PASSWORD") or os.getenv("EMAIL_HOST_PASSWORD", "")
SMTP_PASSWORD = _raw_password.replace(" ", "") if _raw_password else None
SMTP_FROM_NAME = os.getenv("SMTP_FROM_NAME", "ResearchMate")
SMTP_FROM_EMAIL = os.getenv("SMTP_FROM_EMAIL") or SMTP_USER

OTP_EXPIRY_MINUTES = 10

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
JWT_ALGORITHM = "HS256"
JWT_ACCESS_TOKEN_EXPIRE_MINUTES = 60

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/api/chat")
LLM_MODEL_NAME = os.getenv("LLM_MODEL_NAME", "qwen3:8b")