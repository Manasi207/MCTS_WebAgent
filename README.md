# Web AI Agent

A Chrome extension powered by an AI agent backend with MCTS planning, supporting general queries, e-commerce search, web scraping, and email operations.

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

```cmd
cd backend
uvicorn main:app --reload
```

### 4. Install Extension

1. Open `chrome://extensions/`
2. Enable "Developer mode"
3. Click "Load unpacked"
4. Select `extension` folder

