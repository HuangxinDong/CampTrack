#link to camp
#several activities a day

class Activity:
    def __init__(self, name, camp_name, date, start_time, end_time, max_campers, leader_name):
        self.activity_id = f"{camp_name}-{name}-{date}"

        # basic activity info
        self.name = name
        self.camp_name = camp_name
        self.date = date
        self.start_time = start_time
        self.end_time = end_time

        # capacity
        self.max_campers = max_campers

        # leader
        self.leader_name = leader_name

        # dynamic data
        self.campers = []    # list of camper names or IDs
        self.outcomes = ""  # text box for incidents/achievements

    # record outcome/incident/achievement
    def record_outcome(self, text):
        self.outcomes = text

    # check if activity is full by checking how many campers in list and comparing to max
    def is_full(self):
        return len(self.campers) >= self.max_campers

    # ereturn a summary
    def summary(self):
        return (
            f"{self.activity_id} | "
            f"{self.name} | {self.date} {self.start_time}-{self.end_time} | "
            f"{len(self.campers)}/{self.max_campers} campers | "
            f"Leader: {self.leader_name}"
            f"Report: {self.outcomes if self.outcomes else 'None recorded'}"
        )

