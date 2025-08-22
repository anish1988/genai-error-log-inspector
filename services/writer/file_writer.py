import json

class FileWriter:
    def __init__(self, output_path: str):
        self.output_path = output_path

    def write(self, entry: dict, response: dict):
        """
        Append log + LLM response as a JSON object to file.
        """
        with open(self.output_path, "a", encoding="utf-8") as f:
            f.write(json.dumps({
                "log_entry": entry,
                "analysis": response
            }, ensure_ascii=False) + "\n")
