import uuid
from datetime import datetime

class LeaderInterface:
    def get_report_text(self):
        print("\nPlease enter daily report text (finish with an empty line):")
        lines = []
        while True:
            line = input()
            if line.strip() == "":
                break
            lines.append(line)
        return "\n".join(lines)

    @staticmethod
    def show_message(msg):
        print(f"[System] {msg}")


    def show_available_camps(self, camps, username):
        print("\nAvailable camps:")
        for idx, camp in enumerate(camps, 1):
            if camp.camp_leader == username:
                status = " (You are the leader)"
            elif camp.camp_leader:
                status = f" (Assigned to {camp.camp_leader})"
            else:
                status = " (Available)"

            print(f"{idx}. {camp.name} - {camp.location}{status}")

    def select_camp(self, camp_list):
        print("\nYour Camps:")
        for idx, camp in enumerate(camp_list, 1):
            print(f"{idx}. {camp.name} ({len(camp.campers)} campers)")

        try:
            choice = int(input("Choose a camp: "))
            return camp_list[choice - 1]
        except:
            return None


    def get_csv_path(self):
        return input("Enter CSV file path: ")


    def get_daily_report_input(self):
        print("\n===== Create Daily Report =====")

        incident = input("Did an incident occur? (y/n): ").strip().lower()
        incident = (incident == "y")

        summary = input("Summary of the day: ")
        injuries = input("Any injuries? (optional): ")
        notes = input("Additional notes (optional): ")

        report_text = (
            f"Incident: {'Yes' if incident else 'No'}\n"
            f"Summary: {summary}\n"
            f"Injuries: {injuries if injuries else '-'}\n"
            f"Notes: {notes if notes else '-'}"
        )

        return report_text, incident

    def show_reports_table(self, camp, reports):
        print("\n-----------------------------------------------------------")
        print(f" DAILY REPORT REVIEW — Camp: {camp.name}")
        print("-----------------------------------------------------------")
        print(" # | Date       | Incident | Summary")
        print("-----------------------------------------------------------")

        for i, r in enumerate(reports, 1):
            text = r["text"]
            lines = text.splitlines()
            summary_line = ""

            for line in lines:
                if line.startswith("Summary:"):
                    summary_line = line.replace("Summary: ", "")
                    break

            incident_flag = "Yes" if "incident: yes" in text.lower() else "No"

            print(f"{str(i).ljust(2)}| {r['date']} | {incident_flag.center(8)} | {summary_line}")

        print("-----------------------------------------------------------")


    def pick_report_to_delete(self, reports):
        try:
            choice = int(input("Enter report number to delete: "))
            if 1 <= choice <= len(reports):
                return reports[choice - 1]
            return None
        except:
            return None

    def show_campers_table(self, camp):
        campers = camp.campers

        print("\n--------------------------------------------------------------")
        print(f" Camp Name: {camp.name}")
        print(f" Total Campers: {len(campers)}")
        print("--------------------------------------------------------------")
        print("| No |      Name      | Age |     Medical Info     | Emergency Contact |")
        print("--------------------------------------------------------------")

        for i, c in enumerate(campers, 1):
            name = getattr(c, "name", "")[:14].ljust(14)
            age = str(getattr(c, "age", ""))[:3].ljust(3)
            medical = getattr(c, "medical_info", "N/A")[:20].ljust(20)
            contact = getattr(c, "emergency_contact", "N/A")[:16].ljust(16)

            print(f"| {str(i).ljust(2)} | {name} | {age} | {medical} | {contact} |")

        print("--------------------------------------------------------------")

    def show_statistics(self, camp, stats):
        print("\n===== Statistics =====")
        print(f"Camp: {camp.name}")
        print(f"- Participants: {stats['participants']}")
        print(f"- Food usage: {stats['food']}")
        print(f"- Incident count: {stats['incidents']}")
        print(f"- Earnings: £{stats['earnings']}")
