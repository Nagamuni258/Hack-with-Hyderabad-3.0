from typing import List, Optional
from pydantic import BaseModel, Field

class LogEntry(BaseModel):
    date: str
    text: str
    author: Optional[str] = None

class Deal(BaseModel):
    deal_id: str
    rep_name: str
    company: str
    deal_value: Optional[str] = "$0"
    stakeholders: List[str] = Field(default_factory=list)
    log_entries: List[LogEntry] = Field(default_factory=list)

class DealSummary(BaseModel):
    deal_id: str
    company: str
    rep_name: str
    deal_value: Optional[str] = "$0"

class LogRequest(BaseModel):
    text: str

class LogResponse(BaseModel):
    status: str
    deal_id: str
    message: str
    hindsight_status: Optional[str] = "retained"

class BriefingResponse(BaseModel):
    deal_id: str
    company: Optional[str] = None
    briefing: str
    recalled_count: int

class PatternResponse(BaseModel):
    pattern: str
    deals_count: int
