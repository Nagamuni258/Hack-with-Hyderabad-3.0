import os
import sys
import time
from typing import List
from dotenv import load_dotenv
from groq import Groq

# Ensure UTF-8 output on Windows consoles
if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

load_dotenv()

MODEL_NAME = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")

def _get_groq_client() -> Groq:
    """Initialize and return a Groq client, raising ValueError if the key is missing."""
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key or not api_key.strip():
        raise ValueError(
            "GROQ_API_KEY is not configured in the environment or .env file. "
            "Please add GROQ_API_KEY=gsk_... to your .env file."
        )
    return Groq(api_key=api_key.strip())

def generate_briefing(deal_context: List[str], query: str = "") -> str:
    """
    Given the recalled history of a deal from Hindsight, produces a concise briefing.
    
    Covers:
    - Objections raised
    - Stakeholders involved
    - Competitors mentioned
    - One suggested talking point for the next call
    
    If deal_context is empty, returns a 'new deal with no history yet' briefing.
    
    Args:
        deal_context: List of recalled memory strings for this deal
        query: Optional specific user query or focus area
        
    Returns:
        str: Structured markdown briefing
    """
    clean_context = [c.strip() for c in deal_context if c and c.strip()]
    
    if not clean_context:
        return (
            "### Deal Briefing: New Opportunity\n\n"
            "This is a new deal with no history yet recorded in memory.\n\n"
            "- **Objections:** None recorded yet.\n"
            "- **Stakeholders:** None identified yet.\n"
            "- **Competitors:** Unknown.\n"
            "- **Suggested Next Move:** Conduct a structured discovery call to map business pain points, "
            "budget timeline, and economic buyers."
        )
    
    formatted_context = "\n".join(f"- {c}" for c in clean_context)
    
    user_prompt = f"Recalled deal history:\n{formatted_context}\n\n"
    if query:
        user_prompt += f"Specific focus question: {query}\n\n"
    user_prompt += "Produce a concise sales rep briefing covering objections raised, stakeholders involved, competitors mentioned, and one suggested talking point for the next call."
    
    client = _get_groq_client()
    system_prompt = (
        "You are a sales deal intelligence assistant. Given the recalled history of a deal, "
        "produce a concise briefing covering: objections raised, stakeholders involved, "
        "competitors mentioned, and one suggested talking point for the next call. "
        "If deal_context is empty, say this is a new deal with no history yet. "
        "Format your answer cleanly with bullet points and bold headers."
    )
    
    # Retry logic (max 1 retry)
    for attempt in range(2):
        try:
            response = client.chat.completions.create(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                model=MODEL_NAME,
                temperature=0.2,
                max_tokens=1024,
            )
            return response.choices[0].message.content or ""
        except Exception as e:
            if attempt == 0:
                time.sleep(1)
                continue
            raise RuntimeError(f"Failed to generate briefing via Groq: {e}") from e

def find_pattern(all_deals_context: List[str]) -> str:
    """
    Given recalled memories across ALL deals, identifies ONE concrete repeating pattern
    across deals (e.g., an objection type that correlates with a specific tactic that worked).
    
    If there isn't enough data (fewer than 2 items with objections), returns
    'Not enough data yet to detect a pattern.'
    
    Args:
        all_deals_context: List of recalled memory strings from all deals
        
    Returns:
        str: Synthesized cross-deal intelligence pattern
    """
    clean_context = [c.strip() for c in all_deals_context if c and c.strip()]
    
    # Minimum threshold: need at least 2 distinct memories to observe a pattern
    if len(clean_context) < 2:
        return "Not enough data yet to detect a pattern. Retain more deal interactions to unlock cross-deal intelligence."
    
    formatted_context = "\n".join(f"- {item}" for item in clean_context)
    
    system_prompt = (
        "You are a proactive Sales Intelligence and Revenue Operations AI. "
        "You analyze cross-deal history across multiple sales accounts to uncover hidden trends, "
        "correlations between objections and successful close tactics, or recurring competitive threats.\n"
        "Rules:\n"
        "1. Identify exactly ONE concrete, high-impact repeating pattern observed across multiple deals.\n"
        "2. State the pattern clearly, cite the deals/examples, and recommend an actionable playbook rule.\n"
        "3. If there isn't enough clear correlation, say 'Not enough data yet to detect a pattern.'"
    )
    
    user_prompt = (
        f"Here are the recalled cross-deal interaction memories:\n\n{formatted_context}\n\n"
        "Surface the single most prominent recurring pattern across these deals."
    )
    
    client = _get_groq_client()
    
    # Retry logic (max 1 retry)
    for attempt in range(2):
        try:
            response = client.chat.completions.create(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                model=MODEL_NAME,
                temperature=0.3,
                max_tokens=1024,
            )
            return response.choices[0].message.content or ""
        except Exception as e:
            if attempt == 0:
                time.sleep(1)
                continue
            raise RuntimeError(f"Failed to detect pattern via Groq: {e}") from e

if __name__ == "__main__":
    print("=" * 60)
    print(" Testing Groq LLM Client (openai/gpt-oss-120b)")
    print("=" * 60)
    
    # Test empty context
    empty_brief = generate_briefing([], "status")
    print("\n1. Empty context test:")
    print(empty_brief)
    
    # Test with sample deal context
    test_context = [
        "Customer Acme CFO complained about the $48k/yr cost.",
        "Competitor LegacyCorp was pitching at 20% lower price point.",
        "Rep offered annual upfront billing with a 15% discount and waived onboarding fee.",
        "CFO agreed to proceed with annual contract."
    ]
    print("\n2. Deal Briefing Test:")
    brief = generate_briefing(test_context)
    print(brief)
    
    # Test pattern detection
    pattern_context = test_context + [
        "Customer BetaTech Procurement pushed back hard on budget.",
        "Competitor LegacyCorp pitched cheap renewal.",
        "Rep countered by proposing annual prepaid terms with 15% discount.",
        "BetaTech procurement signed the annual contract."
    ]
    print("\n3. Cross-Deal Pattern Detection Test:")
    pat = find_pattern(pattern_context)
    print(pat)
    print("=" * 60)
