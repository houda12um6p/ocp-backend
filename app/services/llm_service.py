import httpx
import os
from dotenv import load_dotenv

load_dotenv()  # reads .env into os.environ so os.getenv picks it up
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL = "meta-llama/llama-3.3-70b-instruct:free"

SYSTEM_PROMPT = """You are a code review severity classifier. Classify the comment into exactly one category.

Categories:
- 0: suggestion (style, naming, readability — no functional impact)
- 1: minor issue (missing check, small bug, non-critical)
- 3: correctness bug (wrong logic, incorrect behavior, bad data handling)
- 5: critical issue (security flaw, crash risk, data loss, breaking change)

Examples:
"rename this variable for clarity" → 0
"missing null check here" → 1
"this calculation is wrong, off-by-one error" → 3
"API key exposed in plaintext" → 5

Respond with ONLY the number: 0, 1, 3, or 5. No explanation."""


async def classify_comment(comment_body: str) -> int:
    # call OpenRouter with LLaMA to get severity weight
    if not OPENROUTER_API_KEY:
        return 1  # default fallback if no API key

    async with httpx.AsyncClient() as client:
        response = await client.post(
            OPENROUTER_URL,
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": MODEL,
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": comment_body},
                ],
                "max_tokens": 5,
            },
            timeout=15.0,
        )
        result = response.json()
        if "choices" not in result:
            return 1  # API error (rate-limit, quota, etc.) — safe fallback
        raw = result["choices"][0]["message"]["content"].strip()
        weight = int(raw) if raw in ("0", "1", "3", "5") else 1
        return weight
