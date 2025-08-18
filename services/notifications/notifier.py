import os, json, urllib.request

class Notifier:
    def __init__(self, slack_webhook: str | None = None):
        self.webhook = slack_webhook or os.getenv("SLACK_WEBHOOK_URL")

    def notify(self, message: str):
        if not self.webhook:
            # fallback to stdout
            print(f"[NOTIFY] {message}")
            return
        payload = json.dumps({"text": message}).encode("utf-8")
        req = urllib.request.Request(self.webhook, data=payload, headers={"Content-Type":"application/json"})
        with urllib.request.urlopen(req) as _:
            pass
