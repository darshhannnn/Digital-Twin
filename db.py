import sqlite3
import hashlib
import datetime
import config

# ---------------------------------------------------------------------------
# Schema helpers
# ---------------------------------------------------------------------------

def _migrate(cursor):
    """Add new columns to existing tables if they don't exist yet (safe migration)."""
    existing = {row[1] for row in cursor.execute("PRAGMA table_info(jobs)")}
    new_cols = {
        "cover_letter_path": "TEXT",
        "skill_gap":         "TEXT",
        "interview_prep":    "TEXT",
        "salary_estimate":   "TEXT",
        "source":            "TEXT DEFAULT 'whatsapp'",
        "jd_hash":           "TEXT",
    }
    for col, col_type in new_cols.items():
        if col not in existing:
            cursor.execute(f"ALTER TABLE jobs ADD COLUMN {col} {col_type}")


def init_db():
    with sqlite3.connect(config.DB_PATH) as conn:
        cursor = conn.cursor()

        cursor.execute('''
        CREATE TABLE IF NOT EXISTS jobs (
            id               INTEGER PRIMARY KEY AUTOINCREMENT,
            company          TEXT,
            role             TEXT,
            batch            TEXT,
            location         TEXT,
            referral_url     TEXT,
            jd_text          TEXT,
            fit_score        INTEGER,
            resume_path      TEXT,
            cover_letter_path TEXT,
            skill_gap        TEXT,
            interview_prep   TEXT,
            salary_estimate  TEXT,
            source           TEXT DEFAULT 'whatsapp',
            jd_hash          TEXT,
            status           TEXT,
            applied_at       TIMESTAMP
        )
        ''')

        cursor.execute('''
        CREATE TABLE IF NOT EXISTS seen_messages (
            channel     TEXT,
            message_id  TEXT,
            seen_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (channel, message_id)
        )
        ''')

        cursor.execute('''
        CREATE TABLE IF NOT EXISTS status_history (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            job_id     INTEGER NOT NULL,
            old_status TEXT,
            new_status TEXT,
            note       TEXT,
            changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (job_id) REFERENCES jobs(id)
        )
        ''')

        cursor.execute('''
        CREATE TABLE IF NOT EXISTS jd_cache (
            url        TEXT PRIMARY KEY,
            jd_text    TEXT,
            scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')

        _migrate(cursor)
        conn.commit()


# ---------------------------------------------------------------------------
# Seen-message helpers
# ---------------------------------------------------------------------------

def is_message_seen(channel, message_id):
    with sqlite3.connect(config.DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute(
            'SELECT 1 FROM seen_messages WHERE channel = ? AND message_id = ?',
            (channel, message_id)
        )
        return cursor.fetchone() is not None


def mark_message_seen(channel, message_id):
    with sqlite3.connect(config.DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute(
            'INSERT OR IGNORE INTO seen_messages (channel, message_id) VALUES (?, ?)',
            (channel, message_id)
        )
        conn.commit()


# ---------------------------------------------------------------------------
# JD Cache helpers
# ---------------------------------------------------------------------------

def _url_key(url: str) -> str:
    return url.strip().lower()


def get_cached_jd(url: str) -> str | None:
    with sqlite3.connect(config.DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute(
            'SELECT jd_text, scraped_at FROM jd_cache WHERE url = ?',
            (_url_key(url),)
        )
        row = cursor.fetchone()
    if not row:
        return None
    jd_text, scraped_at_str = row
    try:
        scraped_at = datetime.datetime.fromisoformat(scraped_at_str)
        age_hours = (datetime.datetime.now() - scraped_at).total_seconds() / 3600
        if age_hours > config.JD_CACHE_TTL_HOURS:
            return None
    except Exception:
        return None
    return jd_text


def cache_jd(url: str, jd_text: str):
    with sqlite3.connect(config.DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute(
            'INSERT OR REPLACE INTO jd_cache (url, jd_text, scraped_at) VALUES (?, ?, ?)',
            (_url_key(url), jd_text, datetime.datetime.now().isoformat())
        )
        conn.commit()


# ---------------------------------------------------------------------------
# Job deduplication
# ---------------------------------------------------------------------------

def job_fingerprint(company: str, role: str) -> str:
    key = f"{(company or '').lower().strip()}|{(role or '').lower().strip()}"
    return hashlib.md5(key.encode()).hexdigest()


def is_duplicate_job(url: str | None, company: str, role: str) -> bool:
    with sqlite3.connect(config.DB_PATH) as conn:
        cursor = conn.cursor()
        found = False
        if url:
            cursor.execute('SELECT 1 FROM jobs WHERE referral_url = ?', (url,))
            if cursor.fetchone():
                found = True
        if not found:
            fp = job_fingerprint(company, role)
            cursor.execute('SELECT 1 FROM jobs WHERE jd_hash = ?', (fp,))
            if cursor.fetchone():
                found = True
    return found


# ---------------------------------------------------------------------------
# Job CRUD
# ---------------------------------------------------------------------------

def save_job(job_data: dict) -> int:
    with sqlite3.connect(config.DB_PATH) as conn:
        cursor = conn.cursor()
        fp = job_fingerprint(job_data.get('company', ''), job_data.get('role', ''))
        cursor.execute('''
        INSERT INTO jobs
          (company, role, batch, location, referral_url, jd_text, fit_score,
           resume_path, cover_letter_path, skill_gap, interview_prep, salary_estimate,
           source, jd_hash, status, applied_at)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        ''', (
            job_data.get('company'),
            job_data.get('role'),
            job_data.get('batch'),
            job_data.get('location'),
            job_data.get('referral_url'),
            job_data.get('jd_text'),
            job_data.get('fit_score'),
            job_data.get('resume_path'),
            job_data.get('cover_letter_path'),
            job_data.get('skill_gap'),
            job_data.get('interview_prep'),
            job_data.get('salary_estimate'),
            job_data.get('source', 'whatsapp'),
            fp,
            job_data.get('status'),
            job_data.get('applied_at'),
        ))
        job_id = cursor.lastrowid
        conn.commit()
    return job_id


def update_job_status(job_id: int, new_status: str, note: str = ""):
    with sqlite3.connect(config.DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT status FROM jobs WHERE id = ?', (job_id,))
        row = cursor.fetchone()
        old_status = row[0] if row else None
        cursor.execute('UPDATE jobs SET status = ? WHERE id = ?', (new_status, job_id))
        cursor.execute(
            'INSERT INTO status_history (job_id, old_status, new_status, note) VALUES (?,?,?,?)',
            (job_id, old_status, new_status, note)
        )
        conn.commit()


_UPDATEABLE_FIELDS = frozenset({
    'cover_letter_path', 'skill_gap', 'interview_prep',
    'salary_estimate', 'resume_path', 'status'
})

def update_job_field(job_id: int, field: str, value):
    if field not in _UPDATEABLE_FIELDS:
        raise ValueError(f"Field '{field}' is not updatable via this function.")
    with sqlite3.connect(config.DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute(f'UPDATE jobs SET {field} = ? WHERE id = ?', (value, job_id))
        conn.commit()


def get_all_jobs(limit: int = 200) -> list[dict]:
    with sqlite3.connect(config.DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(
            'SELECT * FROM jobs ORDER BY id DESC LIMIT ?', (limit,)
        )
        jobs = [dict(row) for row in cursor.fetchall()]
    return jobs


def get_job(job_id: int) -> dict | None:
    with sqlite3.connect(config.DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM jobs WHERE id = ?', (job_id,))
        row = cursor.fetchone()
    return dict(row) if row else None


def get_analytics() -> dict:
    with sqlite3.connect(config.DB_PATH) as conn:
        cursor = conn.cursor()
        stats = {}

        cursor.execute('SELECT COUNT(*) FROM jobs')
        stats['total'] = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM jobs WHERE status = 'applied'")
        stats['applied'] = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM jobs WHERE status = 'skipped'")
        stats['skipped'] = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM jobs WHERE status LIKE '%interview%'")
        stats['interviews'] = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM jobs WHERE status LIKE '%offer%'")
        stats['offers'] = cursor.fetchone()[0]

        cursor.execute('SELECT AVG(fit_score) FROM jobs WHERE fit_score IS NOT NULL')
        avg = cursor.fetchone()[0]
        stats['avg_score'] = round(avg, 1) if avg else 0

        cursor.execute(
            'SELECT company, COUNT(*) as c FROM jobs GROUP BY company ORDER BY c DESC LIMIT 5'
        )
        stats['top_companies'] = [{'company': r[0], 'count': r[1]} for r in cursor.fetchall()]

        cursor.execute(
            "SELECT status, COUNT(*) as c FROM jobs GROUP BY status ORDER BY c DESC"
        )
        stats['by_status'] = [{'status': r[0], 'count': r[1]} for r in cursor.fetchall()]

        cursor.execute(
            "SELECT source, COUNT(*) as c FROM jobs GROUP BY source ORDER BY c DESC"
        )
        stats['by_source'] = [{'source': r[0], 'count': r[1]} for r in cursor.fetchall()]

    return stats


if __name__ == "__main__":
    init_db()
    print("DB initialized.")
