from enum import Enum
class Session(Enum):
    Morning = 0,
    Afternoon = 1,
    Evening = 2,

class Activity:
    def __init__(self, name, date, session: Session):
        self.name = name
        self.date = date
        self.session = session
        self.campers = []

