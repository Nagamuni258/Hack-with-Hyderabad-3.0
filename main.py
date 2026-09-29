import os
import sys
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
HINDSIGHT_API_KEY = os.getenv("HINDSIGHT_API_KEY") or os.getenv("HSK_API_KEY")

def verify_setup():
    print("=" * 55)
    print(" 🚀 Deal Intel Agent - Initialization Check")
    print("=" * 55)
    
    if not GROQ_API_KEY:
        print("❌ Error: GROQ_API_KEY is missing from .env")
        return False
    print("✅ GROQ_API_KEY detected:", GROQ_API_KEY[:8] + "..." + GROQ_API_KEY[-4:])
    
    if not HINDSIGHT_API_KEY:
        print("⚠️  Warning: HSK / Hindsight API key is missing from .env")
    else:
        print("✅ HSK / HINDSIGHT_API_KEY detected:", HINDSIGHT_API_KEY[:8] + "..." + HINDSIGHT_API_KEY[-4:])
    
    return True

def run_agent_quickstart():
    if not verify_setup():
        sys.exit(1)
        
    try:
        from groq import Groq
    except ImportError:
        print("\n📦 'groq' package not found. Install dependencies with:")
        print("   pip install -r requirements.txt\n")
        return

    print("\nConnecting to Groq API...")
    client = Groq(api_key=GROQ_API_KEY)
    
    sample_deal_memo = """
    Startup: PayFlow AI
    Sector: B2B FinTech / Automated Cross-Border Settlements
    Ask: $2.5M Seed Round at $15M Post-Money Valuation
    Metrics:
    - ARR: $420k (growing 22% MoM)
    - Net Revenue Retention (NRR): 134%
    - CAC Payback Period: 4.8 months
    - Team: Ex-Stripe and Razorpay infra engineers
    Key Risks: Regulatory licensing in EU & APAC, banking partner dependency.
    """

    print("Analyzing deal sample with Groq LLM (llama-3.3-70b-versatile)...\n")
    try:
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are DealIntelAgent, an expert venture capital and private equity analyst. "
                        "Evaluate deal memos, highlight red flags, valuation reasonableness, and key diligence questions."
                    ),
                },
                {
                    "role": "user",
                    "content": f"Analyze this deal and give a 3-bullet summary with recommendation:\n\n{sample_deal_memo}",
                },
            ],
            model="llama-3.3-70b-versatile",
            temperature=0.3,
        )
        print("--- Deal Analysis Response ---")
        print(chat_completion.choices[0].message.content)
        print("------------------------------")
    except Exception as e:
        print(f"❌ Groq API call failed: {e}")

if __name__ == "__main__":
    run_agent_quickstart()
