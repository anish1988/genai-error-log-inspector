import os
from openai import OpenAI

class LLMClient:
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    def analyze_error(self, error_context):
        prompt = f"""
        Analyze the following error and suggest a fix in JSON format:
        Error: {error_context}
        """
        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "system", "content": prompt}]
        )
        return response.choices[0].message.content
