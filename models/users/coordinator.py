from models.users.class_map import register
from models.users.users import User

@register("Coordinator")
class Coordinator(User):
    def __init__(self, username, password, role="Coordinator", enabled=True):
        super().__init__(username, password, role, enabled)