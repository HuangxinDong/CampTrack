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
            "enabled": self.enabled
        }

    def __repr__(self):
        return f"<{self.role}: {self.username}>"
    
    def display_commands(self):
        for i, command in enumerate(self.commands):
            print(str(i+1) + '. ' + command['name'])

    def process_command(self, commandNumber):
        # Assume commandNumber is a number from interface_main

        # Check it maps correctly
        command = self.commands[commandNumber-1]['command']

        command()
