# CarePilot CN · 慢性病智能管理平台

> **AI-Powered Chronic Disease Management for Mainland China**
>
> Focusing on Type 2 Diabetes (T2DM) + Hypertension longitudinal management

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://streamlit.io/)

---

## 🏗️ Overview

CarePilot CN is a research-grade chronic disease management platform rebuilt as a **Streamlit-native application** deployable to **Streamlit Community Cloud**. It provides:

- **AI-Powered Chat Companion** — Conversation-driven health data recording, dietary analysis, and medication management via an agent orchestration layer (Planner → Executor → Chat)
- **Longitudinal Timeline Engine** — Deterministic, chronological aggregation of health events, meals, reminders, and follow-ups with anomaly detection
- **SOAP Clinical Digest Generator** — Automated pre-visit clinical summaries with evidence traces (Subjective → Objective → Assessment → Plan)
- **State-Machine Workflow Engine** — 5 deterministic clinical workflows (Daily Review, Medication Reconciliation, Pre-visit Digest, Adherence Follow-up, High Risk Escalation)
- **Report Generation & Export** — Patient weekly reports, adherence overviews, and clinician pre-visit summaries exportable as DOCX, PDF, and HTML
- **Research Evaluation Module** — Synthetic benchmark data generation and automated evaluation for meal risk tagging accuracy

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| 🏠 Dashboard | Health metrics overview, coaching tips, weekly insights |
| 💬 AI Chat | Agentic conversation with tool-calling orchestration |
| 🍽️ Meals | Dietary recording, risk analysis (高糖/高碳水/高脂/高盐), nutritional summaries |
| 💊 Medications | Medication CRUD with deactivation tracking |
| ⏰ Reminders | On-demand daily medication reminder generation & tracking |
| 📋 Reports | Multi-format report generation with download buttons |
| ⚙️ Workflows | 5 state-machine workflows with step-by-step execution logs |
| 👤 Patients | Multi-patient support with profile management & follow-up scheduling |
| 📅 Timeline | Unified chronological view across all event categories |
| 🔬 Evaluation | Benchmark data generation & automated meal risk evaluation |
| 🔧 Settings | LLM configuration, system status, deployment guide |

---

## 📂 Project Structure

```
├── streamlit_app.py              # Entry point
├── app/
│   ├── core/
│   │   ├── config.py             # Settings from Streamlit secrets / env vars
│   │   ├── database.py           # SQLAlchemy ORM (13 tables)
│   │   └── theme.py              # Custom CSS injection
│   ├── features/
│   │   ├── companion/            # Dashboard & chat services
│   │   ├── meals/                # Meal analysis & tracking
│   │   ├── medications/          # Medication management
│   │   ├── reminders/            # Reminder generation
│   │   ├── reports/              # Report generation & export
│   │   ├── workflows/            # State-machine engine
│   │   ├── clinician_digest/     # SOAP clinical digest
│   │   ├── health/               # Health event tracking
│   │   └── patients/             # Patient management
│   ├── services/
│   │   ├── llm.py                # ChatAgent, Planner, Executor, Orchestrator
│   │   ├── parser.py             # NLP parsing (BP, glucose, meals)
│   │   ├── repositories.py       # Data access layer (13 repositories)
│   │   ├── timeline.py           # Longitudinal timeline engine
│   │   └── tools.py              # Tool registry (11 agent tools)
│   └── ui/
│       ├── sidebar.py            # Navigation & patient selector
│       ├── state.py              # Session state management
│       └── pages/                # 11 feature pages
├── tests/
│   └── test_core.py              # Unit tests
├── .streamlit/
│   ├── config.toml               # Theme configuration
│   └── secrets.toml.example      # Secrets template
├── requirements.txt
├── packages.txt                  # System dependencies
├── .gitignore
└── README.md
```

---

## 🚀 Local Development

```bash
# 1. Clone the repo
git clone <your-repo-url>
cd carepilot-cn

# 2. Create virtual environment
python -m venv .venv
# Windows: .venv\Scripts\activate
# Unix: source .venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. (Optional) Configure LLM — copy and edit secrets
cp .streamlit/secrets.toml.example .streamlit/secrets.toml

# 5. Run the app
streamlit run streamlit_app.py
```

The app will open at `http://localhost:8501`. SQLite database auto-initializes on first run.

---

## ☁️ Streamlit Community Cloud Deployment

1. **Push to GitHub** — Push the entire repository to a GitHub repo
2. **Go to** [share.streamlit.io](https://share.streamlit.io/)
3. **Create New App**:
   - Repository: `your-username/carepilot-cn`
   - Branch: `main`
   - Main file path: `streamlit_app.py`
4. **Configure Secrets**:
   - Go to App Settings → Secrets
   - Paste your secrets:

   ```toml
   [llm]
   provider = "openai"
   api_key = "sk-your-key-here"
   base_url = "https://api.openai.com"
   model = "gpt-4o-mini"

   [app]
   enable_fake_llm = false
   default_window_days = 14
   ```

5. **Deploy** — The app will build and deploy automatically

> **Note:** Without LLM secrets, the app runs in **rule-based mode** (fully functional for demo purposes).

---

## 🔑 Secrets Configuration

| Key | Description | Required |
|-----|-------------|----------|
| `llm.provider` | `"openai"` or `"google"` | No (default: openai) |
| `llm.api_key` | Your LLM API key | No (falls back to rules) |
| `llm.base_url` | OpenAI-compatible base URL | No |
| `llm.model` | Model name (e.g. `gpt-4o-mini`) | No |
| `app.enable_fake_llm` | `true` to use rule engine | No (default: true) |

---

## ⚠️ Limitations

| Limitation | Explanation |
|-----------|-------------|
| **SQLite on Streamlit Cloud** | Data resets on redeployment. Suitable for demo/light usage. For persistence, consider external DB. |
| **No Background Workers** | Original worker loop replaced by on-demand reminder generation via UI buttons. |
| **PDF Font Rendering** | ReportLab PDF export uses basic ASCII fonts; Chinese characters may not render correctly in PDFs. HTML/DOCX exports handle Chinese properly. |
| **Single-user per session** | No multi-user authentication. Each session operates independently. |

---

## 🔄 Migration Notes (from chronic_agent_super)

| Original Component | Migration Strategy |
|---|---|
| FastAPI + uvicorn | Replaced with Streamlit entry point |
| Docker + nginx | Removed; uses Streamlit Cloud deployment |
| Background Worker (polling loop) | Replaced with on-demand UI-triggered generation |
| API routes | Converted to internal service calls |
| pydantic-settings + .env | Replaced with Streamlit secrets + env fallback |
| Bearer token auth | Removed (not needed for Streamlit Cloud) |
| File system exports | Replaced with in-memory byte generation for download buttons |
| All 13 DB models | Preserved identically |
| All 13 repositories | Preserved identically |
| All feature services | Preserved identically |
| Agent orchestrator (Planner→Executor→Chat) | Preserved identically |
| Timeline engine | Preserved identically |
| Evaluation module | Preserved with Streamlit UI |
| Clinician digest (SOAP) | Preserved identically |
| 5 workflow definitions | Preserved identically |
| Report generation (DOCX/PDF/HTML) | Preserved with in-memory export |

---

## 🧪 Testing

```bash
# Run tests locally
python tests/test_core.py

# Or with pytest
pip install pytest
pytest tests/ -v
```

---

## 🔮 Future Extensions

- [ ] PostgreSQL adapter for persistent cloud storage
- [ ] Multi-user authentication via Streamlit `st.login`
- [ ] Google Gemini native tool-calling integration
- [ ] Real-time WebSocket notifications
- [ ] Expanded evaluation: digest quality scoring, parsing F1
- [ ] Chinese PDF font support (CJK fonts in ReportLab)
- [ ] Dashboard data visualizations with Plotly charts

---

## 📄 License

This project is for research and educational purposes.

---

*Built with ❤️ using Streamlit, SQLAlchemy, and Python*
