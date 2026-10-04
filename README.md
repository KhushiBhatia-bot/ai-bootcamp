# ResearchMate 🔬🤖

ResearchMate is an AI-powered conversational research assistant built with **FastAPI**, **Django**, and local LLMs (via **Ollama** and **DuckDuckGo Web Search**). It autonomously decides when web research is necessary to answer user queries with up-to-date sources, citations, and markdown formatting.

---

## 🌟 Features

- 📄 **Document Upload & Analysis**: Upload PDFs, DOCX, TXT, MD, CSV, or code files and ask complex research questions with full context awareness.
- 📌 **Pin Chats & Organize by Tags**: Pin important conversations to the top and organize chats into categories (e.g. *AI*, *Economics*, *Biology*, *General*).
- ✏️ **Chat Renaming**: Rename any conversation session dynamically.
- ⚡ **Real-Time Token Streaming (SSE)**: Character-by-character response streaming directly from the local LLM.
- 🔄 **Live Agent Status Badges**: Real-time feedback indicators (e.g. `🔍 Searching the web for "..."`, `✍️ Synthesizing research report...`).
- 🌙 **Dark / Light Mode**: Seamless theme switching with saved preference state.
- 📥 **Export to Markdown**: Download research reports and chat sessions as `.md` files.
- 📋 **Sleek Toast Notifications**: Instant, unobtrusive floating copy and action feedback (no intrusive browser alert dialogs).
- 🔐 **Passwordless Email OTP Authentication**: Secure 6-digit OTP delivery using Gmail SMTP App Password & JWT.
- 💬 **Persistent Multi-Chat History**: Create, view, switch between, and delete chat sessions.
- 🗑️ **Message Management**: Delete individual messages within conversations.
- 🧠 **Local LLM Intelligence**: Powered by Ollama (`qwen2.5:8b` / `qwen3:8b` or any Ollama model).
- 🌐 **Autonomous Web Research**: DuckDuckGo integration triggered automatically when live data is required.
- 📚 **Source Citations**: Displays clickable web references and snippets alongside AI answers.

---

## 🏗️ Architecture

- **Backend**: FastAPI (Python 3.10+), SQLAlchemy + SQLite, Pydantic, Python-Jose (JWT), Python `smtplib` (Gmail SMTP).
- **Frontend**: Django (Templates & Static Assets), Vanilla JavaScript (Async Fetch + Server-Sent Events stream reader), Marked.js, CSS3 Variables.
- **AI / LLM Engine**: Local Ollama instance running Qwen with DuckDuckGo Search integration.

---

## 🚀 Getting Started

### 1. Prerequisites

- Python 3.10+
- [Ollama](https://ollama.com/) installed and running locally.
- A [Resend](https://resend.com/) API key for sending email OTPs.

Pull your desired model in Ollama:
```bash
ollama run qwen2.5:8b
# or
ollama run qwen3:8b
```

---

### 2. Backend Setup (FastAPI)

1. Navigate to the project root and activate your virtual environment:
   ```bash
   cd /path/to/ResearchMate_backup
   source .venv/bin/activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   # (or ensure fastapi, uvicorn, httpx, python-dotenv, duckduckgo-search, python-jose, resend are installed)
   ```

3. Create or configure your `.env` file in the root directory:
   ```env
   # Gmail SMTP Configuration
   DEFAULT_FROM_EMAIL=your_sending_gmail@gmail.com
   EMAIL_HOST_PASSWORD=your_16_digit_app_password
   
   # JWT & LLM Configuration
   JWT_SECRET_KEY=your_secure_random_jwt_secret_key
   OLLAMA_URL=http://localhost:11434/api/chat
   LLM_MODEL_NAME=qwen2.5:8b
   ```

4. Start the FastAPI backend server:
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```
   *FastAPI will run at `http://127.0.0.1:8000` with Swagger docs available at `http://127.0.0.1:8000/docs`.*

---

### 3. Frontend Setup (Django)

1. In a new terminal window, activate the virtual environment and navigate to `frontend`:
   ```bash
   cd /path/to/ResearchMate_backup/frontend
   source ../.venv/bin/activate
   ```

2. Run migrations (if needed):
   ```bash
   python3 manage.py migrate
   ```

3. Start the Django development server:
   ```bash
   python3 manage.py runserver 8080
   ```

---

### 4. Usage

1. Open your browser and navigate to: **`http://127.0.0.1:8080`**
2. Enter your email address to receive a 6-digit OTP.
3. Enter the OTP code to log in.
4. Start a new conversation, ask research questions, view web sources, and manage your chat sessions!
5. Use the **Logout** button in the top right corner to sign out.

---

## 📂 Project Structure

```
ResearchMate_backup/
├── app/                        # FastAPI Backend Application
│   ├── api/v1/                 # API Routes (auth, chats, messages)
│   ├── core/                   # Core security & database setup
│   ├── models/                 # Database models
│   ├── schemas/                # Pydantic schemas
│   ├── services/               # LLM, Search, & Email services
│   ├── config.py               # Environment configuration
│   └── main.py                 # FastAPI entry point & CORS
├── frontend/                   # Django Frontend Application
│   ├── chat/                   # Chat app (templates, static JS/CSS)
│   ├── frontend/               # Django project settings & URLs
│   └── manage.py
├── .env                        # Environment variables
├── README.md                   # Project documentation
└── researchmate.db             # SQLite database
```
