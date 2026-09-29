import os
import sys
import json
import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, HTTPException, Path as FastPath
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, FileResponse
from dotenv import load_dotenv

# Ensure UTF-8 output on Windows consoles
if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

load_dotenv()

from app.models import Deal, DealSummary, LogRequest, LogResponse, BriefingResponse, PatternResponse
from app.hindsight import retain_log, recall_deal
from app.llm import generate_briefing, find_pattern

DATA_FILE = Path(__file__).parent / "data" / "deals.json"
STATIC_DIR = Path(__file__).parent.parent / "static"

app = FastAPI(
    title="Deal Intelligence Agent",
    description="AI Sales Deal Intelligence Agent powered by Hindsight persistent memory and Groq LLM",
    version="1.0.0",
)

# CORS middleware allowing all origins for demo/hackathon flexibility
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def _load_deals() -> List[Dict[str, Any]]:
    """Load deals from the flat JSON store."""
    if not DATA_FILE.exists():
        return []
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []

def _save_deals(deals: List[Dict[str, Any]]) -> None:
    """Save deals to the flat JSON store."""
    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(deals, f, indent=2)

# Root status check
@app.get("/health")
def health_check():
    return {"status": "ok", "service": "deal-intel-agent"}

# GET /deals - returns list of deals (id, company, rep_name, deal_value)
@app.get("/deals", response_model=List[DealSummary])
def get_deals():
    deals = _load_deals()
    return [
        DealSummary(
            deal_id=d.get("deal_id", ""),
            company=d.get("company", ""),
            rep_name=d.get("rep_name", ""),
            deal_value=d.get("deal_value", "$0"),
        )
        for d in deals
    ]

# GET /deals/{deal_id} - returns full deal details including logs
@app.get("/deals/{deal_id}")
def get_deal_detail(deal_id: str = FastPath(..., description="The deal identifier")):
    deals = _load_deals()
    for d in deals:
        if d.get("deal_id") == deal_id:
            return d
    raise HTTPException(status_code=404, detail=f"Deal '{deal_id}' not found.")

# POST /deals/{deal_id}/log - logs an interaction to Hindsight & local JSON
@app.post("/deals/{deal_id}/log", response_model=LogResponse)
async def log_deal_interaction(
    req: LogRequest,
    deal_id: str = FastPath(..., description="The deal identifier")
):
    if not req.text or not req.text.strip():
        raise HTTPException(status_code=400, detail="Log text cannot be empty.")

    text = req.text.strip()
    today_str = datetime.date.today().isoformat()

    # 1. Retain into Hindsight Cloud
    try:
        retain_res = await retain_log(deal_id, text)
    except Exception as e:
        raise HTTPException(
            status_code=502,
            detail=f"Hindsight memory retention failed: {str(e)}"
        )

    # 2. Append to local JSON store
    deals = _load_deals()
    matched = False
    for d in deals:
        if d.get("deal_id") == deal_id:
            if "log_entries" not in d:
                d["log_entries"] = []
            d["log_entries"].append({"date": today_str, "text": text})
            matched = True
            break
            
    if not matched:
        # Create a new deal entry if it doesn't exist yet
        deals.append({
            "deal_id": deal_id,
            "company": f"Account {deal_id}",
            "rep_name": "Sales Rep",
            "deal_value": "$50,000",
            "stakeholders": [],
            "log_entries": [{"date": today_str, "text": text}],
        })
    _save_deals(deals)

    return LogResponse(
        status="success",
        deal_id=deal_id,
        message="Interaction retained into persistent memory and logged.",
        hindsight_status="retained" if retain_res.get("success", False) else "unknown"
    )

# GET /deals/{deal_id}/brief - recalls history from Hindsight and generates LLM briefing
@app.get("/deals/{deal_id}/brief", response_model=BriefingResponse)
async def get_deal_briefing(deal_id: str = FastPath(..., description="The deal identifier")):
    deals = _load_deals()
    company_name = None
    for d in deals:
        if d.get("deal_id") == deal_id:
            company_name = d.get("company")
            break

    # 1. Recall deal memory from Hindsight
    try:
        memories = await recall_deal(deal_id, query="full deal history, objections, stakeholders, competitors", scope="deal")
    except Exception as e:
        raise HTTPException(
            status_code=502,
            detail=f"Hindsight memory recall failed: {str(e)}"
        )

    context_texts = [m.get("text", "") for m in memories if m.get("text")]

    # 2. Generate structured briefing via Groq
    try:
        briefing_text = generate_briefing(context_texts, query=f"Briefing for {company_name or deal_id}")
    except Exception as e:
        raise HTTPException(
            status_code=502,
            detail=f"Groq LLM briefing generation failed: {str(e)}"
        )

    return BriefingResponse(
        deal_id=deal_id,
        company=company_name,
        briefing=briefing_text,
        recalled_count=len(context_texts),
    )

# GET /patterns - recalls cross-deal memories and detects recurring pattern
@app.get("/patterns", response_model=PatternResponse)
async def get_cross_deal_patterns():
    # 1. Recall across ALL deals in Hindsight
    try:
        all_memories = await recall_deal(
            deal_id=None,
            query="objections, competitor pricing, discount offers, contract signing, outcomes across all deals",
            scope="all"
        )
    except Exception as e:
        raise HTTPException(
            status_code=502,
            detail=f"Hindsight cross-deal recall failed: {str(e)}"
        )

    all_texts = [m.get("text", "") for m in all_memories if m.get("text")]

    # 2. Identify cross-deal pattern with Groq LLM
    try:
        pattern_text = find_pattern(all_texts)
    except Exception as e:
        raise HTTPException(
            status_code=502,
            detail=f"Groq LLM pattern identification failed: {str(e)}"
        )

    return PatternResponse(
        pattern=pattern_text,
        deals_count=len(all_texts),
    )

# Mount static files for the demo UI at the root AFTER defining API routes
if STATIC_DIR.exists():
    app.mount("/", StaticFiles(directory=str(STATIC_DIR), html=True), name="static")
else:
    @app.get("/")
    def root_fallback():
        return {"status": "ok", "service": "deal-intel-agent", "docs": "/docs"}
