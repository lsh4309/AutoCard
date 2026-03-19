import os
from pathlib import Path
from urllib.parse import quote_plus
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

# .env 로드 (PostgreSQL 환경변수)
load_dotenv(BASE_DIR / ".env")
UPLOAD_DIR = BASE_DIR / "uploads"
EXPORT_DIR = BASE_DIR / "exports"

# PostgreSQL - 모든 테이블 (거래내역 + 마스터)
PG_HOST = os.getenv("PG_HOST", "localhost")
PG_PORT = int(os.getenv("PG_PORT", "5432"))
PG_DATABASE = os.getenv("PG_DATABASE", "postgres")
PG_USER = os.getenv("PG_USER", "postgres")
PG_PASSWORD = os.getenv("PG_PASSWORD", "postgres")

DATABASE_URL = (
    f"postgresql://{PG_USER}:{quote_plus(PG_PASSWORD)}@{PG_HOST}:{PG_PORT}/{PG_DATABASE}"
)

UPLOAD_DIR.mkdir(exist_ok=True)
EXPORT_DIR.mkdir(exist_ok=True)
