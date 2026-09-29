import os
import sys
import asyncio
from typing import Dict, Any, List, Optional
import httpx
from dotenv import load_dotenv

# Ensure UTF-8 output on Windows consoles
if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

load_dotenv()

HINDSIGHT_BASE_URL = os.getenv("HINDSIGHT_BASE_URL", "https://api.hindsight.vectorize.io")
BANK_ID = os.getenv("HINDSIGHT_BANK_ID", "deal-intel")

def _get_api_key() -> str:
    """Retrieve the Hindsight API key from environment, raising ValueError if missing."""
    key = os.getenv("HINDSIGHT_API_KEY") or os.getenv("HSK_API_KEY")
    if not key or not key.strip():
        raise ValueError(
            "HINDSIGHT_API_KEY is not configured in the environment or .env file. "
            "Please add HINDSIGHT_API_KEY=hsk_... to your .env file."
        )
    return key.strip()

def _get_headers() -> Dict[str, str]:
    return {
        "Authorization": f"Bearer {_get_api_key()}",
        "Content-Type": "application/json",
        "User-Agent": "deal-intel-agent/1.0.0"
    }

async def retain_log(deal_id: str, text: str) -> Dict[str, Any]:
    """
    Sends the text to Hindsight's retain endpoint.
    Tags the memory with deal_id as metadata and tags so it can be scoped later.
    
    Args:
        deal_id: Unique identifier for the deal (e.g., 'deal_001')
        text: Log content, interaction summary, or call notes
        
    Returns:
        dict: API response payload from Hindsight
    """
    if not text or not text.strip():
        raise ValueError("Cannot retain empty log text.")
    
    url = f"{HINDSIGHT_BASE_URL.rstrip('/')}/v1/default/banks/{BANK_ID}/memories"
    payload = {
        "items": [
            {
                "content": f"[Deal {deal_id}] {text.strip()}",
                "tags": [deal_id],
                "metadata": {
                    "deal_id": deal_id,
                    "source": "deal-intel-agent"
                }
            }
        ]
    }
    
    async with httpx.AsyncClient(headers=_get_headers(), timeout=30.0) as client:
        try:
            response = await client.post(url, json=payload)
            if response.status_code != 200:
                raise RuntimeError(
                    f"Hindsight retain failed with status {response.status_code}: {response.text}"
                )
            return response.json()
        except httpx.RequestError as exc:
            raise RuntimeError(f"Hindsight network error during retain: {exc}") from exc

async def recall_deal(deal_id: Optional[str], query: str, scope: str = "deal") -> List[Dict[str, Any]]:
    """
    Recalls memories from Hindsight.
    - If scope == 'deal': calls Hindsight recall filtered to that deal_id only.
    - If scope == 'all': calls Hindsight recall across all deals (for cross-deal patterns).
    
    Args:
        deal_id: Unique identifier for the deal (required if scope == 'deal')
        query: Search query for memory retrieval
        scope: 'deal' (scoped to deal_id) or 'all' (unscoped across all memories)
        
    Returns:
        list: List of recalled memory dictionaries (with text, score, and metadata)
    """
    url = f"{HINDSIGHT_BASE_URL.rstrip('/')}/v1/default/banks/{BANK_ID}/memories/recall"
    
    payload: Dict[str, Any] = {
        "query": query,
        "max_tokens": 4096,
        "budget": "high"
    }
    
    if scope == "deal":
        if not deal_id:
            raise ValueError("deal_id must be provided when scope is 'deal'")
        payload["tags"] = [deal_id]
        payload["tags_match"] = "any"
    
    async with httpx.AsyncClient(headers=_get_headers(), timeout=30.0) as client:
        try:
            response = await client.post(url, json=payload)
            if response.status_code != 200:
                raise RuntimeError(
                    f"Hindsight recall failed with status {response.status_code}: {response.text}"
                )
            data = response.json()
            results = data.get("results", [])
            return results
        except httpx.RequestError as exc:
            raise RuntimeError(f"Hindsight network error during recall: {exc}") from exc

if __name__ == "__main__":
    async def main_test():
        print("=" * 60)
        print(" Testing Hindsight Retain & Recall Pipeline")
        print("=" * 60)
        test_deal = "deal_test_999"
        test_text = "Initial discovery call: VP of Engineering worried about SOC2 compliance."
        
        print(f"\n1. Retaining memory for {test_deal}...")
        retain_res = await retain_log(test_deal, test_text)
        print("   ✅ Retain Success:", retain_res.get("success", False))
        
        print(f"\n2. Recalling memory for {test_deal} (scope='deal')...")
        memories = await recall_deal(test_deal, query="security compliance concerns", scope="deal")
        print(f"   ✅ Recalled {len(memories)} memories:")
        for idx, m in enumerate(memories, 1):
            print(f"      [{idx}] {m.get('text')}")
            
        print("\n3. Recalling memory across all deals (scope='all')...")
        all_memories = await recall_deal(None, query="objections across all deals", scope="all")
        print(f"   ✅ Recalled {len(all_memories)} memories across all deals.")
        print("=" * 60)
        print(" Hindsight Pipeline Verification COMPLETE!")
        print("=" * 60)

    asyncio.run(main_test())
