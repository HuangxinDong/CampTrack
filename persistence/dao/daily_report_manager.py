import json
import os
from datetime import datetime

class DailyReportManager:
    def __init__(self):
        self.file_path = "persistence/data/daily_reports.json"

        if not os.path.exists(self.file_path):
            with open(self.file_path, "w") as f:
                json.dump([], f)

    def read_all(self):
        """Read all reports."""
        with open(self.file_path, "r") as f:
            return json.load(f)

    def save_all(self, reports):
        """Overwrite full JSON file."""
        with open(self.file_path, "w") as f:
            json.dump(reports, f, indent=4)

    def add_report(self, report_dict):
        """Append a new report to storage."""
        reports = self.read_all()
        reports.append(report_dict)
        self.save_all(reports)



    



