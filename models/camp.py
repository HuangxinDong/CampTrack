import uuid
from datetime import datetime, timedelta, date


class Camp:
    def __init__(
        self, name: str, location: str, camp_type: str, start_date: date, end_date: date, initial_food_stock_per_day: int
    ):
        self.camp_id = str(uuid.uuid4())
        # generate the uniqueId for a camp
        self.name = name
        self.location = location
        self.camp_type = camp_type
        self.start_date = start_date
        self.end_date = end_date
        self.camp_leader = None
        self.campers = []  # will be an array of "campers class"
        self.initial_food_stock_per_day = initial_food_stock_per_day
        self.food_per_camper_per_day = 1  # default value, can be changes by coordinator
        self.precamp_stock = 0
        self.topups = []  # array of numbers
        self.food_usage = {}  # key is date, value is amount

    def topup_food(self, amount):
        if self.has_camp_started():
            self.topups.append(amount)
        else:
            self.precamp_stock += amount

    def has_camp_started(self):
        now = datetime.now().date()
        return self.start_date <= now
    
    def has_camp_finished(self):
        now = datetime.now().date()
        return now > self.end_date

    def set_food_per_camper_per_day(self, amount):
        self.food_per_camper_per_day = amount

    # Used by coordinator to see how much is required based on current campers
    # They can then set the precamp_stock
    def total_food_required(self):
        total_campers = len(self.campers)
        days = (self.end_date - self.start_date).days + 1

        return total_campers * self.food_per_camp_per_day * days

    def is_food_shortage(self):
        if self.has_camp_finished():
            return False

        today = datetime.now().date()
        total_campers = len(self.campers)
        total_stock = self.precamp_stock + sum(self.topups)
        used_so_far = sum(self.food_usage.values())

        if not self.has_camp_started():
            total_days = (self.end_date - self.start_date).days + 1
            total_required = total_campers * self.food_per_camper_per_day * total_days
            return total_stock < total_required

        remaining_days = (self.end_date - today).days + 1
        remaining_required = total_campers * self.food_per_camper_per_day * remaining_days
        remaining_stock = total_stock - used_so_far
        return remaining_stock < remaining_required


    def add_camper(self, camper):
        self.campers.append(camper)

    def remove_camper(self, camper_id):
        for camper in self.campers:
            if camper.camper_id == camper_id:
                self.campers.remove(camper)
                break

    def assign_leader(self, username):
        self.camp_leader = username

    def add_food_usage(self, amount: int, day: date):
        if not (self.start_date <= day <= self.end_date):
            raise ValueError("Food usage date must be within the camp start and end dates.")
        self.food_usage[day.strftime("%Y-%m-%d")] = amount

    def to_dict(self):
        return {
            "camp_id": self.camp_id,
            "name": self.name,
            "location": self.location,
            "camp_type": self.camp_type,
            "start_date": self.start_date.strftime("%Y-%m-%d"),
            "end_date": self.end_date.strftime("%Y-%m-%d"),
            "initial_food_stock_per_day": self.initial_food_stock_per_day,
            "camp_leader": self.camp_leader,
            "campers": [camper.to_dict() for camper in self.campers],
        }

    @classmethod
    def from_dict(cls, data):
        start_date = datetime.strptime(data["start_date"], "%Y-%m-%d").date()
        end_date = datetime.strptime(data["end_date"], "%Y-%m-%d").date()
        camp = cls(
            name=data["name"],
            location=data["location"],
            camp_type=data["camp_type"],
            start_date=start_date,
            end_date=end_date,
            initial_food_stock_per_day=data["initial_food_stock_per_day"],
        )

        camp.camp_id = data["camp_id"]
        camp.camp_leader = data["camp_leader"]

        return camp
