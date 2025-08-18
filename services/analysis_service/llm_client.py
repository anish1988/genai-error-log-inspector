import os
from openai import OpenAI

PROMPT = """You are an on-call engineering assistant.
Given structured log events and optional context, identify:
1) probable root cause,
2) impacted components,
3) severity,
4) immediate fix suggestions,
5) longer-term remediation.

Return concise bullet points.
"""

class LLMClient:
    def __init__(self, api_key: str | None = None, model: str | None = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model = model or os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        self.client = OpenAI(api_key=self.api_key)

    def analyze(self, events, context: str | None):
        text_events = "\n".join(f"- [{e.get('level','?')}] {e.get('msg', e.get('raw',''))}" for e in events)
        prompt = f"{PROMPT}\n\nContext:\n{context or 'N/A'}\n\nEvents:\n{text_events}\n"
        resp = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
        )
        return resp.choices[0].message.content.strip()
