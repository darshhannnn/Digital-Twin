# WhatsApp Job Agent 🚀

An AI-powered job application assistant that monitors WhatsApp channels, evaluates job postings, and automatically applies to relevant roles.

## 🌟 Features

- **WhatsApp Monitoring**: Automatically scrapes specified WhatsApp channels for new job postings.
- **AI-Powered Parsing**: Uses **Ollama (qwen3:4b)** to extract structured job details (Company, Role, Batch, URL) from raw messages.
- **Smart Scoring**: Evaluates the fit between job descriptions and your resume using local LLMs.
- **Resume Tailoring**: Leverages **Gemini 1.5 Flash** to rewrite your resume bullets specifically for each job.
- **Automated Applications**: Uses **Playwright** to auto-fill forms on platforms like **Workday, Greenhouse, and Lever**.
- **Native PDF Generation**: Generates professional, tailored PDFs on the fly.
- **Telegram Notifications**: Get real-time updates on your phone for every application or manual review request.

## 🛠️ Tech Stack

- **Python 3.11+**
- **Playwright** (Browser Automation)
- **Ollama** (Local LLM for Parsing & Scoring)
- **Google Gemini API** (Resume Tailoring)
- **fpdf2** (Native PDF Generation)
- **SQLite** (Job Tracking & History)

## 🚀 Getting Started

### 1. Prerequisites
- Install [Ollama](https://ollama.com/) and pull the model: `ollama pull qwen3:4b`
- Install Python dependencies:
  ```bash
  pip install -r requirements.txt
  python -m playwright install chromium
  ```

### 2. Configuration
Edit `config.py` with your credentials:
- `GEMINI_API_KEY`: Your Google AI Studio key.
- `WHATSAPP_CHANNELS`: List of channel names to monitor.
- `TARGET_BATCH`: e.g., "2026".

### 3. Usage
1. **Initial Login**: Run the scraper once to scan the WhatsApp QR code:
   ```bash
   python whatsapp.py
   ```
2. **Start the Agent**:
   ```bash
   python main.py
   ```

## 📂 Project Structure

- `whatsapp.py`: Handles WhatsApp Web interaction and message scraping.
- `parser.py`: Uses AI to turn chat messages into structured JSON.
- `scraper.py`: Extracts Job Descriptions from URLs.
- `scorer.py`: Calculates fit score (0-100).
- `tailor.py`: Personalizes your resume using Gemini.
- `applier.py`: The automation engine for career pages.
- `pdf.py`: Converts tailored data into a PDF resume.

## ⚠️ Disclaimer
This tool is for educational purposes. Always review automated applications to ensure accuracy and compliance with job board terms of service.
