import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# API Keys and Tokens
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "your_gemini_api_key_here")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "your_telegram_bot_token_here")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "your_telegram_chat_id_here")

# Ollama Settings
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
os.environ["OLLAMA_HOST"] = OLLAMA_BASE_URL
OLLAMA_MODEL = "qwen3:4b"

# Application Settings
FIT_SCORE_THRESHOLD = 70
WHATSAPP_CHANNELS = [
    "Jobs Careers"
]
CHECK_INTERVAL = 3600  # 1 hour in seconds
TARGET_BATCH = "2026"

# Paths
BASE_DIR = Path(__file__).parent
RESUMES_DIR = BASE_DIR / "resumes"
MASTER_RESUME_PATH = BASE_DIR / "master_resume.txt"
DB_PATH = BASE_DIR / "jobs.db"
CHROME_DATA_DIR = BASE_DIR / "chrome_data"

# Ensure directories exist
RESUMES_DIR.mkdir(exist_ok=True)
CHROME_DATA_DIR.mkdir(exist_ok=True)

# Create master resume placeholder if not exists
if not MASTER_RESUME_PATH.exists():
    with open(MASTER_RESUME_PATH, "w") as f:
        f.write("Paste your base resume here.")
