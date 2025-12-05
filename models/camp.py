import uuid
from datetime import datetime, timedelta

class Camp:
    # 1. Camp will be defined by the logistics coordinator
    # 2. Class contains information like
    #     1. Name
    #     2. Location
    #     3. Dates of availability
    #     4. Type of the camp (day, overnight etc)
    #     5. Food stock information
    #     6. Leader information
    #     7. Campers data information

    def __init__(
        self, name: str, location: str, camp_type: str, start_date: str, end_date: str, intial_food_stock_per_day: int
    ):
        self.camp_id = str(uuid.uuid4())
        # generate the uniqueId for a camp
        self.name = name
        self.location = location
        self.camp_type = camp_type
        self.start_date = start_date
        self.end_date = end_date
        self.intial_food_stock_per_day = intial_food_stock_per_day
        self.food_stock_information = {}
        self.camp_leader = None  # needs to be set, initially no leader by default
        self.campers = []  # will be an array of "campers class"
        self.intialize_food_information()

    def intialize_food_information(self):
        # camps mayb running across multiple days
        # we need to go through each of those days and initialize the food amount
        start = datetime.strptime(self.start_date, "%Y-%m-%d")  # convert date time to a propper format
        end = datetime.strptime(self.end_date, "%Y-%m-%d")

        current = start
        while current <= end:
            date_str = current.strftime("%Y-%m-%d")
            self.food_stock_information[date_str] = self.intial_food_stock_per_day
            current += timedelta(days=1)  # increment by one day

    def topup_food(self, amount):
        for date in self.food_stock_information:
            self.food_stock_information[date] += amount

    # Caluclate the total food requirements for the camp
    def total_food_required(self, food_per_camp_per_day):
        total_campers = len(self.campers)
        start = datetime.strptime(self.start_date, "%Y-%m-%d")
        end = datetime.strptime(self.end_date, "%Y-%m-%d")
        days = (end - start).days + 1

        return total_campers * food_per_camp_per_day * days

    def is_food_shortage(self):
        total_campers = len(self.campers)
        for date, stock in self.food_stock_information.items():
            if stock < total_campers:
                return True

        return False

    def add_camper(self, camper):
        self.campers.append(camper)

    def remove_camper(self, camper_id):
        for camper in self.campers:
            if camper.camper_id == camper_id:
                self.campers.remove(camper)
                break

    def assign_leader(self, username):
        self.camp_leader = username

    def to_dict(self):
        return {
            "camp_id": self.camp_id,
            "name": self.name,
            "location": self.location,
            "camp_type": self.camp_type,
            "start_date": self.start_date,
            "end_date": self.end_date,
            "intial_food_stock_per_day": self.intial_food_stock_per_day,
            "food_stock_information": self.food_stock_information,
            "camp_leader": self.camp_leader,
            "campers": [camper.to_dict() for camper in self.campers],  # if camper has to_dict()
        }
    @classmethod
    def from_dict(cls, data):
        camp = cls(
            name=data["name"],
            location=data["location"],
            camp_type=data["camp_type"],
            start_date=data["start_date"],
            end_date=data["end_date"],
            intial_food_stock_per_day=data["intial_food_stock_per_day"]
        )

        camp.camp_id = data["camp_id"]
        camp.food_stock_information = data["food_stock_information"]
        camp.camp_leader = data["camp_leader"]

        return camp
