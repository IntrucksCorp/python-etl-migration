import os
from dotenv import load_dotenv

load_dotenv()

# ── Nowcerts ───────────────────────────────────────────────────
NOWCERTS_API_BASE_URL: str = os.getenv("NOWCERTS_API_BASE_URL", "https://api.nowcerts.com/api")
NOWCERTS_USERNAME: str = os.getenv("NOWCERTS_USERNAME", "")
NOWCERTS_PASSWORD: str = os.getenv("NOWCERTS_PASSWORD", "")

# ── Supabase ───────────────────────────────────────────────────
SUPABASE_URL: str = os.getenv("SUPABASE_URL", "https://eovqdeaocpccpwwqrbyb.supabase.co")
SUPABASE_SERVICE_ROLE_KEY: str = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")

# ── Migración ──────────────────────────────────────────────────
TARGET_ORG_ID: str = os.getenv("TARGET_ORG_ID", "")
PAGE_SIZE: int = int(os.getenv("PAGE_SIZE", "500"))
REQUEST_DELAY: float = float(os.getenv("REQUEST_DELAY", "0.3"))
LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
