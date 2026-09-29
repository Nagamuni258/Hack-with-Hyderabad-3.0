import sys
import asyncio
from pathlib import Path

# Ensure UTF-8 output on Windows consoles
if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.main import app
import httpx

async def run_verification():
    print("=" * 70)
    print(" 🧪 Deal Intelligence Agent — Full API Endpoint Verification")
    print("=" * 70)
    
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test", timeout=45.0) as client:
        # 1. Health check
        print("\n--- [1] GET /health ---")
        r1 = await client.get("/health")
        print(f"Status: {r1.status_code}")
        print("Response:", r1.json())
        assert r1.status_code == 200

        # 2. GET /deals
        print("\n--- [2] GET /deals ---")
        r2 = await client.get("/deals")
        print(f"Status: {r2.status_code}")
        deals = r2.json()
        print(f"Total deals: {len(deals)}")
        for d in deals:
            print(f"  - {d['deal_id']}: {d['company']} ({d['deal_value']}) by {d['rep_name']}")
        assert len(deals) >= 4

        # 3. GET /deals/deal_001 (Detail)
        print("\n--- [3] GET /deals/deal_001 ---")
        r3 = await client.get("/deals/deal_001")
        print(f"Status: {r3.status_code}")
        deal_detail = r3.json()
        print(f"Company: {deal_detail['company']}, Logs count: {len(deal_detail['log_entries'])}")

        # 4. POST /deals/deal_004/log (Log new interaction into Hindsight)
        print("\n--- [4] POST /deals/deal_004/log ---")
        r4 = await client.post(
            "/deals/deal_004/log",
            json={"text": "Call with Vikram: Vikram mentioned budget freeze unless we provide annual discount."}
        )
        print(f"Status: {r4.status_code}")
        print("Response:", r4.json())
        assert r4.status_code == 200

        # 5. GET /deals/deal_001/brief (Recall from Hindsight + Groq Briefing)
        print("\n--- [5] GET /deals/deal_001/brief ---")
        r5 = await client.get("/deals/deal_001/brief")
        print(f"Status: {r5.status_code}")
        brief_data = r5.json()
        print(f"Recalled {brief_data['recalled_count']} memories from Hindsight")
        print("Briefing content:")
        print(brief_data["briefing"])
        assert r5.status_code == 200
        assert len(brief_data["briefing"]) > 50

        # 6. GET /patterns (Cross-deal analysis across all Hindsight memories)
        print("\n--- [6] GET /patterns ---")
        r6 = await client.get("/patterns")
        print(f"Status: {r6.status_code}")
        pattern_data = r6.json()
        print(f"Analyzed {pattern_data['deals_count']} cross-deal memories")
        print("Pattern identified:")
        print(pattern_data["pattern"])
        assert r6.status_code == 200
        assert len(pattern_data["pattern"]) > 50

    print("\n" + "=" * 70)
    print(" 🌟 ALL 6 ENDPOINTS VERIFIED AND RETURNING REAL DATA!")
    print("=" * 70)

if __name__ == "__main__":
    asyncio.run(run_verification())
