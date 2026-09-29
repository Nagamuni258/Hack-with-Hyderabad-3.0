# Deal Intel Agent 💼🤖

An intelligent deal evaluation and due diligence agent for venture capital, private equity, and M&A deals.

## Features
- **High-Speed Inference**: Powered by **Groq** (`llama-3.3-70b-versatile` / `mixtral-8x7b`).
- **Memory & Intelligence**: Integrated with **Hindsight / HSK** memory engine.
- **Due Diligence Automation**: Quick financial ratios, unit economics check, valuation benchmarks, and risk flags.

## Getting Started

### 1. Setup Virtual Environment

```bash
# Navigate to the repo
cd deal-intel-agent

# Create virtual environment
python -m venv .venv

# Activate virtual environment
# Windows (PowerShell):
.venv\Scripts\Activate.ps1
# macOS/Linux:
source .venv/bin/activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Environment Variables

Your `.env` file is already preconfigured (and excluded from git via `.gitignore`):

```ini
GROQ_API_KEY=gsk_...
HINDSIGHT_API_KEY=hsk_...
HSK_API_KEY=hsk_...
```

### 4. Run the Agent

```bash
python main.py
```
