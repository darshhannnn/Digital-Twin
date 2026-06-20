# WhatsApp Job Agent

An AI-powered job application assistant that monitors WhatsApp channels, evaluates job postings, and automatically applies to relevant roles. Runs fully local with Ollama — no API keys required.

## Features

- **WhatsApp Monitoring**: Automatically scrapes specified WhatsApp channels for new job postings.
- **AI-Powered Parsing**: Uses **Ollama (qwen3:4b)** to extract structured job details from raw messages.
- **Smart Scoring**: Evaluates the fit between job descriptions and your resume using local LLMs.
- **Resume Tailoring**: Rewrites your resume bullets specifically for each job using local Ollama.
- **Automated Applications**: Uses **Playwright** to auto-fill forms on platforms like **Workday, Greenhouse, and Lever**.
- **Native PDF Generation**: Generates professional, tailored PDFs on the fly.
- **Telegram Notifications**: Get real-time updates on your phone for every application.

## Tech Stack

- **Python 3.11+**
- **Playwright** (Browser Automation)
- **Ollama** (Local LLM — all inference runs on your GPU)
- **fpdf2** (PDF Generation)
- **SQLite** (Job Tracking & History)
- **Flask** (Dashboard)

## Getting Started

### 1. Prerequisites
- Install [Ollama](https://ollama.com/) and pull the model:
  ```bash
  ollama pull qwen3:4b
  ```
- Install Python dependencies:
  ```bash
  pip install -r requirements.txt
  python -m playwright install chromium
  ```

### 2. Configuration
Copy `.env.example` to `.env` and fill in your values:
```bash
cp .env.example .env
```
- `WHATSAPP_CHANNELS` in `config.py`: List of channel names to monitor.
- `TARGET_BATCH` in `config.py`: e.g., "2026".

### 3. Usage
1. **Initial Login**: Run the scraper once to scan the WhatsApp QR code:
   ```bash
   python whatsapp.py
   ```
2. **Start the Agent**:
   ```bash
   python main.py
   ```

## Project Structure

- `llm.py`: Shared Ollama client with JSON retry/repair logic.
- `whatsapp.py`: Handles WhatsApp Web interaction and message scraping.
- `parser.py`: Uses AI to turn chat messages into structured JSON.
- `scraper.py`: Extracts Job Descriptions from URLs.
- `scorer.py`: Calculates fit score (0-100).
- `analyzer.py`: Skill gap analysis, interview prep, salary estimation.
- `tailor.py`: Personalizes your resume for each job.
- `cover_letter.py`: Generates tailored cover letters.
- `applier.py`: The automation engine for career pages.
- `pdf.py`: Converts tailored data into a PDF resume.
- `dashboard.py`: Flask web dashboard for monitoring.

## Disclaimer
This tool is for educational purposes. Always review automated applications to ensure accuracy and compliance with job board terms of service.
