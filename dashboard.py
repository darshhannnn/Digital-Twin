"""
dashboard.py
------------
Flask web dashboard for monitoring the Digital Twin job agent.

Routes
------
GET  /                          — main dashboard
GET  /api/job/<id>              — job detail JSON
POST /api/job/<id>/status       — update job status
GET  /api/analytics             — analytics JSON
POST /api/run                   — trigger a background agent run
"""

import sys
import json
import threading
import datetime
import functools
import config
import db

from flask import Flask, render_template, jsonify, request

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

app = Flask(__name__)
db.init_db()

_agent_lock = threading.Lock()
_agent_running = False


def _require_api_key(f):
    @functools.wraps(f)
    def decorated(*args, **kwargs):
        if config.DASHBOARD_API_KEY:
            api_key = request.headers.get("X-API-Key") or request.args.get("api_key")
            if api_key != config.DASHBOARD_API_KEY:
                return jsonify({"error": "Unauthorized"}), 401
        return f(*args, **kwargs)
    return decorated


# ---------------------------------------------------------------------------
# Pages
# ---------------------------------------------------------------------------

@app.route("/")
def index():
    jobs  = db.get_all_jobs(limit=300)
    stats = db.get_analytics()
    return render_template("index.html", jobs=jobs, stats=stats)


# ---------------------------------------------------------------------------
# API
# ---------------------------------------------------------------------------

@app.route("/api/job/<int:job_id>")
@_require_api_key
def api_job(job_id: int):
    job = db.get_job(job_id)
    if not job:
        return jsonify({"error": "Not found"}), 404
    return jsonify(job)


@app.route("/api/job/<int:job_id>/status", methods=["POST"])
@_require_api_key
def api_update_status(job_id: int):
    body   = request.get_json(force=True) or {}
    status = body.get("status", "")
    note   = body.get("note", "")
    if not status:
        return jsonify({"error": "status is required"}), 400
    db.update_job_status(job_id, status, note)
    return jsonify({"ok": True, "job_id": job_id, "new_status": status})


@app.route("/api/analytics")
@_require_api_key
def api_analytics():
    return jsonify(db.get_analytics())


@app.route("/api/run", methods=["POST"])
@_require_api_key
def api_run():
    global _agent_running
    with _agent_lock:
        if _agent_running:
            return jsonify({"message": "Agent is already running. Please wait."}), 409
        _agent_running = True

    def _run():
        global _agent_running
        try:
            import main as agent_main
            agent_main.run_agent()
        except Exception as e:
            print(f"[Dashboard] Agent run error: {e}")
        finally:
            with _agent_lock:
                _agent_running = False

    t = threading.Thread(target=_run, daemon=True)
    t.start()
    return jsonify({"message": "Agent started", "started_at": datetime.datetime.now().isoformat()})


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print(f"Dashboard running at http://{config.DASHBOARD_HOST}:{config.DASHBOARD_PORT}")
    app.run(
        host=config.DASHBOARD_HOST,
        port=config.DASHBOARD_PORT,
        debug=False,
        use_reloader=False,
    )
