import os
import logging
from openai import OpenAI

# Configure logger
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s"
)

PROMPT = """You are an on-call engineering assistant.
Given structured log events and optional context, identify:
1) probable root cause,
2) impacted components,
3) severity,
4) immediate fix suggestions,
5) longer-term remediation.

Return concise bullet points.
"""
LOG_PROMPT_TEMPLATE = """
You are a highly skilled log analysis assistant helping developers troubleshoot and debug backend systems.

You will be given a single log entry (in plain text, JSON, or list format), which may come from any type of backend system including but not limited to:
- MySQL, Apache, NGINX, PHP, Python, Java, Node.js, Laravel, Asterisk, etc.

The log may include warnings, errors, exceptions, deprecation notices, stack traces, or performance issues.

---

🔍 Analyze the log content carefully and perform the following tasks:

1. **Understand the log context**: Use both `message` and `exception` (if present) to infer what went wrong.
2. **Identify the technology or system** involved (e.g. MySQL, PHP, etc.) based on log content , log text or keywords.
3. **Summarize the root cause** in developer-friendly language — rephrase the error clearly.
4. **Suggest a likely fix or mitigation step** that is relevant to the identified system.
5. **Provide a code/config fix example**, if applicable.
6. **Point the developer to where to look** (e.g., a config file, function, database setting).
7. **List 5 reliable and system-specific online resources or docs** that can help solve this problem.

---

📌 **Important Notes**:
- Treat every log entry as a **unique and independent** problem, regardless of similarity to previous logs.
- Do **not** reuse or repeat explanations given for earlier entries.
- Avoid generic or unrelated error explanations.
- Focus on accuracy and relevance to the given log entry.
- If the log is a deprecation warning, do **not** treat it as an exception or crash.
- If the technology is not explicitly stated, infer carefully but do not assume unrelated error types.

---

Return your response as a **well-formatted JSON object** with these exact fields:

{{
  "message": "<Brief, human-readable summary of the log error>",
  "summary": "<Concise root cause explanation>",
  "fix_suggestion": "<Clear, actionable advice for resolving the issue>",
  "code_fix": "<Example code/config adjustment with reasoning, if applicable>",
  "code_location": "<Where to apply or investigate the fix in the code/configuration>",
  "resources": ["<URL or resource title>", "..."]
}}

📌 **Additional Notes**:

- Tailor the solution based on the detected **tech stack** (MySQL, PHP, etc.).
- Do **not assume** Java or NullPointerException unless clearly indicated.
- Do **not invent** error types that don’t match the input.
- Keep explanations concise but technically helpful (2–4 lines max).

---

Log Entry:
{log_entry}
"""

class LLMClient:
    def __init__(self, api_key: str | None = None, model: str | None = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model = model or os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        self.client = OpenAI(api_key=self.api_key)

    def analyze(self, events, context: str | None):

        logger.info("Analyze Function calling...")

        text_events = "\n".join(f"- [{e.get('level','?')}] {e.get('msg', e.get('raw',''))}" for e in events)
           
        logger.info("LLM Raw text events:\n%s", text_events)   
       # prompt = f"{PROMPT}\n\nContext:\n{context or 'N/A'}\n\nEvents:\n{text_events}\n"
        # Interpolate into prompt
        prompt = LOG_PROMPT_TEMPLATE.format(log_entry=text_events)

        # Log payload
        logger.info("Sending request to LLM...")
        logger.info("LLM Payload Prompt:\n%s", prompt)

        resp = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
        )

        # Capture response
        llm_response = resp.choices[0].message.content.strip()

         # Log response
        logger.info("Received response from LLM.")
        logger.debug("LLM Raw Response:\n%s", llm_response)

        return llm_response
        
    
