"""
notifier.py
-----------
Rich multi-channel notification system.

Channels
--------
- Telegram  — emoji-formatted messages with score bars and skill summaries
- Discord   — webhook embed (optional, skipped if DISCORD_WEBHOOK_URL is empty)

Public API
----------
notify(job_data, status_msg)   -> send to all configured channels
send_daily_digest()            -> summary of jobs processed in the last 24h
"""

import json
import datetime
import requests
import config
import db


# ---------------------------------------------------------------------------
# Score bar helper
# ---------------------------------------------------------------------------

def _score_bar(score: int, width: int = 10) -> str:
    filled = round((score / 100) * width)
    return "█" * filled + "░" * (width - filled)


def _status_emoji(status: str) -> str:
    mapping = {
        "applied":          "✅",
        "skipped":          "⏭️",
        "failed":           "❌",
        "tailoring_failed": "⚠️",
        "interview":        "🎯",
        "offer":            "🎉",
        "rejected":         "😔",
        "workday":          "🔧",
        "manual_required":  "📝",
    }
    for key, emoji in mapping.items():
        if key in (status or "").lower():
            return emoji
    return "📋"


# ---------------------------------------------------------------------------
# Telegram
# ---------------------------------------------------------------------------

def _send_telegram(message: str):
    if not config.TELEGRAM_BOT_TOKEN:
        print(f"[Telegram] Skipped (token not configured): {message[:80]}...")
        return
    url = f"https://api.telegram.org/bot{config.TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id":    config.TELEGRAM_CHAT_ID,
        "text":       message,
        "parse_mode": "HTML",
    }
    try:
        resp = requests.post(url, json=payload, timeout=10)
        if resp.status_code != 200:
            print(f"[Telegram] Error {resp.status_code}: {resp.text[:200]}")
    except Exception as e:
        print(f"[Telegram] Request failed: {e}")


# ---------------------------------------------------------------------------
# Discord
# ---------------------------------------------------------------------------

def _send_discord(title: str, description: str, color: int = 0x5865F2,
                  fields: list[dict] | None = None):
    if not config.DISCORD_WEBHOOK_URL:
        return
    embed = {
        "title":       title,
        "description": description,
        "color":       color,
        "timestamp":   datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "fields":      fields or [],
    }
    payload = {"embeds": [embed]}
    try:
        resp = requests.post(config.DISCORD_WEBHOOK_URL, json=payload, timeout=10)
        if resp.status_code not in (200, 204):
            print(f"[Discord] Error {resp.status_code}: {resp.text[:200]}")
    except Exception as e:
        print(f"[Discord] Request failed: {e}")


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def notify(job_data: dict, status_msg: str):
    company  = job_data.get('company', 'Unknown')
    role     = job_data.get('role', 'Unknown')
    score    = job_data.get('fit_score') or 0
    status   = job_data.get('status', '')
    source   = job_data.get('source', 'whatsapp')
    emoji    = _status_emoji(status)
    bar      = _score_bar(score)

    skill_gap_str = job_data.get('skill_gap') or ''
    try:
        sg = json.loads(skill_gap_str) if isinstance(skill_gap_str, str) and skill_gap_str else {}
    except Exception:
        sg = {}
    missing = ", ".join(sg.get('missing_skills', [])[:4]) or "—"

    salary_str = job_data.get('salary_estimate') or ''
    try:
        sal = json.loads(salary_str) if isinstance(salary_str, str) and salary_str else {}
    except Exception:
        sal = {}
    salary_range = sal.get('monthly_range', '—')

    tg_msg = (
        f"{emoji} <b>{role}</b> @ <b>{company}</b>\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"📊 Fit Score : <code>{score}/100</code>  {bar}\n"
        f"💰 Est. Stipend : {salary_range}/mo\n"
        f"🔍 Missing Skills : {missing}\n"
        f"📡 Source : {source}\n"
        f"📌 Status : {status_msg}\n"
        f"━━━━━━━━━━━━━━━━━━"
    )
    _send_telegram(tg_msg)

    color = 0x57F287 if "applied" in status else 0xED4245 if "fail" in status else 0xFEE75C
    _send_discord(
        title=f"{emoji} {role} @ {company}",
        description=status_msg,
        color=color,
        fields=[
            {"name": "Fit Score",      "value": f"`{score}/100` {bar}", "inline": True},
            {"name": "Est. Stipend",   "value": f"{salary_range}/mo",   "inline": True},
            {"name": "Missing Skills", "value": missing,                 "inline": False},
            {"name": "Source",         "value": source,                  "inline": True},
        ]
    )


def send_daily_digest():
    all_jobs  = db.get_all_jobs(limit=500)
    now       = datetime.datetime.now()
    cutoff    = now - datetime.timedelta(hours=24)

    recent = []
    for j in all_jobs:
        try:
            applied_at = datetime.datetime.fromisoformat(str(j.get('applied_at') or ''))
            if applied_at >= cutoff:
                recent.append(j)
        except Exception:
            pass

    if not recent:
        return

    stats    = db.get_analytics()
    applied  = sum(1 for j in recent if j.get('status') == 'applied')
    skipped  = sum(1 for j in recent if j.get('status') == 'skipped')
    avg_sc   = round(sum(j.get('fit_score') or 0 for j in recent) / len(recent), 1)

    digest = (
        f"🌅 <b>Daily Job Digest</b> — {now.strftime('%d %b %Y')}\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"📝 Jobs processed: {len(recent)}\n"
        f"✅ Applied        : {applied}\n"
        f"⏭️  Skipped        : {skipped}\n"
        f"📊 Avg score      : {avg_sc}\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"📈 All-time total : {stats['total']} jobs\n"
        f"🎯 All-time offers: {stats['offers']}\n"
    )
    _send_telegram(digest)

    _send_discord(
        title=f"🌅 Daily Digest — {now.strftime('%d %b')}",
        description=f"**{len(recent)}** jobs processed today",
        color=0x5865F2,
        fields=[
            {"name": "Applied",     "value": str(applied),         "inline": True},
            {"name": "Skipped",     "value": str(skipped),         "inline": True},
            {"name": "Avg Score",   "value": str(avg_sc),          "inline": True},
            {"name": "All-time",    "value": str(stats['total']),  "inline": True},
            {"name": "Interviews",  "value": str(stats['interviews']), "inline": True},
            {"name": "Offers",      "value": str(stats['offers']),    "inline": True},
        ]
    )
