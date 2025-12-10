import json

class DailyReportManager:
    def __init__(self, path="persistence/data/daily_reports.json"):
        self.path = path

    def read_all(self):
        """Return all daily reports stored in the JSON file."""
        try:
            with open(self.path, "r") as f:
                return json.load(f)
        except FileNotFoundError:
            return []
        except json.JSONDecodeError:
            print("[WARN] daily_reports.json is not valid JSON.")
            return []


    



