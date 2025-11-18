# src/verify_openrouter.py
import os
import requests
import json
import textwrap
from typing import Dict, Any, Optional

OPENROUTER_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_ENDPOINT = os.getenv("OPENROUTER_ENDPOINT", "https://openrouter.ai/api/v1/chat/completions")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "gpt-4o-mini")
DEFAULT_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.0"))
DEFAULT_MAX_TOKENS = int(os.getenv("LLM_MAX_TOKENS", "400"))

HEADERS = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {OPENROUTER_KEY}"
}

def _build_prompt(article_text: str) -> str:
    snippet = article_text.strip()
    if len(snippet) > 1500:
        snippet = snippet[:1500] + "..."
    prompt = f"""
You are a careful fact-checker. Read the article snippet below and return ONLY a JSON object with these fields:
- claim: the single central factual claim (one sentence).
- label: one of ["Real","Fake","Misleading","Biased"].
- confidence: a number between 0.0 and 1.0.
- explanation: one short sentence explaining the label.
- evidence_urls: an array of up to 2 trustworthy URLs that support or refute the claim (or [] if none).

Output EXACTLY this JSON (no extra text):

{{ 
  "claim": "...",
  "label": "Real|Fake|Misleading|Biased",
  "confidence": 0.00,
  "explanation": "...",
  "evidence_urls": ["https://...", "https://..."]
}}

Article snippet:
{snippet}
"""
    return textwrap.dedent(prompt)

def call_openrouter(prompt: str,
                    model: str = OPENROUTER_MODEL,
                    temperature: float = DEFAULT_TEMPERATURE,
                    max_tokens: int = DEFAULT_MAX_TOKENS) -> str:
    if OPENROUTER_KEY is None:
        raise RuntimeError("OPENROUTER_API_KEY not set in environment.")
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": "You are an expert fact-checker."},
            {"role": "user", "content": prompt}
        ],
        "temperature": temperature,
        "max_tokens": max_tokens,
        "top_p": 1.0,
        "n": 1
    }
    resp = requests.post(OPENROUTER_ENDPOINT, headers=HEADERS, json=payload, timeout=30)
    resp.raise_for_status()
    return resp.json()

def _extract_message_text(api_json: Dict[str, Any]) -> str:
    """
    Try to extract assistant message text from possible shapes of the OpenRouter response.
    """
    # common: data['choices'][0]['message']['content']
    choices = api_json.get("choices") or api_json.get("result") or []
    if isinstance(choices, list) and len(choices) > 0:
        first = choices[0]
        if isinstance(first, dict):
            if 'message' in first and isinstance(first['message'], dict):
                return first['message'].get('content', '')
            if 'text' in first:
                return first.get('text', '')
            if 'content' in first:
                return first.get('content', '')
    # fallback: convert whole json to string
    return json.dumps(api_json)

def _extract_json_from_text(raw_text: str) -> Optional[dict]:
    s = raw_text.strip()
    # remove fenced code blocks
    if s.startswith("```"):
        parts = s.split("```")
        for p in parts:
            if p.strip().startswith("{"):
                s = p
                break
    import re
    m = re.search(r'\{(?:.|\n)*\}', s)
    if not m:
        return None
    try:
        return json.loads(m.group(0))
    except Exception:
        try:
            return json.loads(m.group(0).replace("'", '"'))
        except Exception:
            return None

def verify_article(article_text: str) -> Dict[str, Any]:
    prompt = _build_prompt(article_text)
    api_json = call_openrouter(prompt)
    raw_message = _extract_message_text(api_json)
    parsed = _extract_json_from_text(raw_message) or {}
    out = {
        "claim": parsed.get("claim"),
        "label": parsed.get("label"),
        "confidence": float(parsed.get("confidence")) if parsed.get("confidence") is not None else None,
        "explanation": parsed.get("explanation"),
        "evidence_urls": parsed.get("evidence_urls") if isinstance(parsed.get("evidence_urls"), list) else [],
        "raw_llm_text": raw_message
    }
    return out

