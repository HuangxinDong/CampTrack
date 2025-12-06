# The Session Class

from models.users.class_map import user_from_dict

class Session():
    def __init__(self, user):
        self.user = user_from_dict(user)