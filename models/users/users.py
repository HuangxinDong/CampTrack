class User:
    def __init__(self, username, password, role=None, enabled=True):
        self.username = username
        self.password = password
        self.role = role
        self.enabled = enabled

    def to_dict(self):
        """Base to_dict method, can be overridden by subclasses"""
        return {
            "username": self.username,
            "password": self.password,
            "role": self.role,
            "enabled": self.enabled,
        }

    def __repr__(self):
        return f"<{self.role}: {self.username}>"


