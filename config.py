import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------------
# API Keys and Tokens
# ---------------------------------------------------------------------------
TELEGRAM_BOT_TOKEN  = os.getenv("TELEGRAM_BOT_TOKEN") or ""
TELEGRAM_CHAT_ID    = os.getenv("TELEGRAM_CHAT_ID") or ""
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL") or ""

# ---------------------------------------------------------------------------
# Ollama Settings  (local LLM for parsing & scoring)
# ---------------------------------------------------------------------------
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
OLLAMA_MODEL = "qwen3:4b"

# ---------------------------------------------------------------------------
# Application Settings
# ---------------------------------------------------------------------------
FIT_SCORE_THRESHOLD = int(os.getenv("FIT_SCORE_THRESHOLD", "70"))
TARGET_BATCH        = os.getenv("TARGET_BATCH", "2026")
CHECK_INTERVAL      = int(os.getenv("CHECK_INTERVAL", "3600"))
JD_CACHE_TTL_HOURS  = int(os.getenv("JD_CACHE_TTL_HOURS", "24"))

# WhatsApp channels to monitor
WHATSAPP_CHANNELS = [
    "Jobs Careers"
]

# LinkedIn search queries for multi-source discovery
LINKEDIN_SEARCH_QUERIES = [
    f"Software Engineer Intern {TARGET_BATCH}",
    f"SDE Intern {TARGET_BATCH}",
    f"Data Scientist Intern {TARGET_BATCH}",
]

# Flask dashboard
DASHBOARD_PORT = int(os.getenv("DASHBOARD_PORT", "5000"))
DASHBOARD_HOST = os.getenv("DASHBOARD_HOST", "127.0.0.1")

# Dashboard API key (optional, for securing endpoints)
DASHBOARD_API_KEY = os.getenv("DASHBOARD_API_KEY") or ""

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
BASE_DIR           = Path(__file__).parent
RESUMES_DIR        = BASE_DIR / "resumes"
COVER_LETTERS_DIR  = BASE_DIR / "cover_letters"
MASTER_RESUME_PATH = BASE_DIR / "master_resume.txt"
DB_PATH            = BASE_DIR / "jobs.db"
CHROME_DATA_DIR    = BASE_DIR / "chrome_data"

# Ensure directories exist
RESUMES_DIR.mkdir(exist_ok=True)
COVER_LETTERS_DIR.mkdir(exist_ok=True)
CHROME_DATA_DIR.mkdir(exist_ok=True)

# Create master resume placeholder if not exists
if not MASTER_RESUME_PATH.exists():
    with open(MASTER_RESUME_PATH, "w") as f:
        f.write("Paste your base resume here.")
