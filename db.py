import sqlite3
import config

def init_db():
    conn = sqlite3.connect(config.DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS jobs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        company TEXT,
        role TEXT,
        batch TEXT,
        location TEXT,
        referral_url TEXT,
        jd_text TEXT,
        fit_score INTEGER,
        resume_path TEXT,
        status TEXT,
        applied_at TIMESTAMP
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS seen_messages (
        channel TEXT,
        message_id TEXT,
        seen_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (channel, message_id)
    )
    ''')
    
    conn.commit()
    conn.close()

def is_message_seen(channel, message_id):
    conn = sqlite3.connect(config.DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT 1 FROM seen_messages WHERE channel = ? AND message_id = ?', (channel, message_id))
    seen = cursor.fetchone() is not None
    conn.close()
    return seen

def mark_message_seen(channel, message_id):
    conn = sqlite3.connect(config.DB_PATH)
    cursor = conn.cursor()
    cursor.execute('INSERT OR IGNORE INTO seen_messages (channel, message_id) VALUES (?, ?)', (channel, message_id))
    conn.commit()
    conn.close()

def save_job(job_data):
    conn = sqlite3.connect(config.DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
    INSERT INTO jobs (company, role, batch, location, referral_url, jd_text, fit_score, resume_path, status, applied_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        job_data.get('company'),
        job_data.get('role'),
        job_data.get('batch'),
        job_data.get('location'),
        job_data.get('referral_url'),
        job_data.get('jd_text'),
        job_data.get('fit_score'),
        job_data.get('resume_path'),
        job_data.get('status'),
        job_data.get('applied_at')
    ))
    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
