import os
import sys
import json
import asyncio
from pathlib import Path
from dotenv import load_dotenv

# Ensure UTF-8 output on Windows consoles
if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

# Ensure parent directory is in sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.hindsight import retain_log
from app.llm import _get_groq_client, MODEL_NAME

load_dotenv()

DATA_FILE = Path(__file__).parent.parent / "app" / "data" / "deals.json"

SYNTHETIC_DEALS = [
    {
        "deal_id": "deal_001",
        "company": "ApexLogistics",
        "rep_name": "Alex Rivera",
        "deal_value": "$72,000",
        "stakeholders": [
            "Elena Rostova, VP of Supply Chain",
            "Marcus Vance, CFO"
        ],
        "log_entries": [
            {
                "date": "2026-08-10",
                "text": "Discovery call with Elena. Strong interest in automated route optimization, but she noted competitor LegacyFreight is pitching at 25% lower price point."
            },
            {
                "date": "2026-08-18",
                "text": "Technical demo for operations team. Feedback was glowing, but Elena mentioned Marcus (CFO) has final veto power on software spend."
            },
            {
                "date": "2026-08-25",
                "text": "Budget review with Marcus (CFO). Marcus pushed back hard on the $6k/mo cost, stating Q3 software budget is constrained."
            },
            {
                "date": "2026-09-02",
                "text": "Counter-offer meeting. Rep offered annual prepaid billing with a 15% discount ($61.2k upfront) and waived implementation fees."
            },
            {
                "date": "2026-09-10",
                "text": "Marcus confirmed budget approval. Stated that annual upfront billing allowed them to capitalize the cost under operational cap. Contract signed!"
            }
        ]
    },
    {
        "deal_id": "deal_002",
        "company": "CloudScale Systems",
        "rep_name": "Jordan Lee",
        "deal_value": "$120,000",
        "stakeholders": [
            "David Chen, CTO",
            "Rachel Adams, Head of Procurement"
        ],
        "log_entries": [
            {
                "date": "2026-08-12",
                "text": "Intro call with David Chen. CloudScale is scaling engineering by 40% and needs our infrastructure monitoring tier."
            },
            {
                "date": "2026-08-20",
                "text": "Architecture review completed. Architecture approved by David, but handed off to Procurement for contract negotiations."
            },
            {
                "date": "2026-08-28",
                "text": "Procurement meeting with Rachel Adams. Rachel presented competitor DataMatrix's lower quote and demanded a 20% rate cut or no deal."
            },
            {
                "date": "2026-09-05",
                "text": "Rep countered by proposing annual upfront billing with a 15% discount and included 2 days of free technical onboarding."
            },
            {
                "date": "2026-09-15",
                "text": "Rachel signed off on the annual prepaid contract. Deal marked Closed Won for $102k annual upfront."
            }
        ]
    },
    {
        "deal_id": "deal_003",
        "company": "HealthPulse Analytics",
        "rep_name": "Sarah Jenkins",
        "deal_value": "$95,000",
        "stakeholders": [
            "Dr. Aris Thorne, Chief Medical Officer",
            "Linda Morales, VP of Healthcare Compliance"
        ],
        "log_entries": [
            {
                "date": "2026-08-15",
                "text": "Initial discovery with Dr. Thorne. HealthPulse needs predictive triage algorithms across 12 regional outpatient centers."
            },
            {
                "date": "2026-08-26",
                "text": "Compliance interrogation with Linda Morales. Linda objected to public cloud hosting, demanding strict HIPAA BAA and dedicated single-tenant VPC."
            },
            {
                "date": "2026-09-08",
                "text": "Security review. Provided Linda with SOC2 Type II report and HIPAA compliance architecture documentation."
            },
            {
                "date": "2026-09-19",
                "text": "Linda approved compliance terms. However, hospital board froze new vendor capital commitments until Q1 next year. Deal stalled."
            }
        ]
    },
    {
        "deal_id": "deal_004",
        "company": "FinVault Security",
        "rep_name": "Maya Patel",
        "deal_value": "$50,000",
        "stakeholders": [
            "Vikram Rao, Head of Infrastructure"
        ],
        "log_entries": [
            {
                "date": "2026-09-22",
                "text": "Initial discovery meeting booked with Vikram Rao for next Thursday. No prior interaction history."
            }
        ]
    }
]

async def seed_data():
    print("=" * 65)
    print(" 🛠️  Deal Intelligence Agent - Synthetic Data Seeder")
    print("=" * 65)

    # 1. Save deals to app/data/deals.json
    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(SYNTHETIC_DEALS, f, indent=2)
    print(f"✅ Saved {len(SYNTHETIC_DEALS)} synthetic deals to {DATA_FILE}")

    # 2. Retain each deal and log entry into Hindsight
    print("\n🧠 Seeding memories into Hindsight Cloud...")
    total_retained = 0
    
    for deal in SYNTHETIC_DEALS:
        deal_id = deal["deal_id"]
        company = deal["company"]
        stakeholders = ", ".join(deal["stakeholders"])
        
        # Seed deal profile overview
        overview_text = (
            f"Deal overview for {company} (ID: {deal_id}). "
            f"Rep: {deal['rep_name']}. Deal value: {deal['deal_value']}. "
            f"Key stakeholders: {stakeholders}."
        )
        print(f"\n[+] Retaining overview for {company} ({deal_id})...")
        await retain_log(deal_id, overview_text)
        total_retained += 1
        
        # Retain each chronological log entry
        for entry in deal["log_entries"]:
            log_text = f"Log ({entry['date']}): {entry['text']}"
            print(f"    -> Retaining log: {entry['date']} - {entry['text'][:55]}...")
            await retain_log(deal_id, log_text)
            total_retained += 1

    print("\n" + "=" * 65)
    print(f" 🎉 SEEDING COMPLETE!")
    print(f" 📊 Summary: {len(SYNTHETIC_DEALS)} deals generated and {total_retained} memories retained in Hindsight.")
    print("=" * 65)

if __name__ == "__main__":
    asyncio.run(seed_data())
