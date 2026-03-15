# Web AI Agent

A Chrome extension powered by an AI agent backend with MCTS (Monte Carlo Tree Search) for intelligent web scraping, supporting e-commerce price comparison, web data extraction, and general queries.

## Features

- 🤖 **MCTS-Driven Web Scraping**: Intelligent retry logic for robust data extraction
- 💰 **E-commerce Price Comparison**: Real-time prices from Amazon, Flipkart, Myntra
- 🌐 **Web Data Extraction**: Scrape any URL with structured content parsing
- 📧 **Email Operations**: Send and fetch emails (optional)
- 🔄 **Offline Operation**: Works with local Ollama LLM (llama3.2)

## Quick Start

### 1. Backend Setup

```cmd
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure Email (Optional)

Edit `backend/.env`:
```env
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
```

Get Gmail App Password: https://myaccount.google.com/apppasswords

### 3. Start Backend

**Method 1: Direct Python (Recommended for offline)**
```cmd
cd backend
python main.py
```

**Method 2: Uvicorn CLI**
```cmd
cd backend
uvicorn main:app --reload
```

**Difference:**
- `python main.py`: Simpler, works offline, auto-configures server
- `uvicorn main:app --reload`: More control, manual configuration

### 4. Install Extension

1. Open `chrome://extensions/`
2. Enable "Developer mode"
3. Click "Load unpacked"
4. Select `extension` folder

