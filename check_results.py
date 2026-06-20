import sqlite3
import config

def check_db():
    try:
        with sqlite3.connect(config.DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT company, role, fit_score, status, applied_at FROM jobs ORDER BY id DESC LIMIT 10")
            rows = cursor.fetchall()
            for row in rows:
                print(row)
    except Exception as e:
        print(f"Error reading database: {e}")

if __name__ == "__main__":
    check_db()
