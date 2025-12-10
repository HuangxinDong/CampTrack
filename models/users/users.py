from persistence.dao.user_manager import UserManager
from persistence.dao.camp_manager import CampManager
from persistence.dao.message_manager import MessageManager
from models.message import Message
from utils.conversation_helpers import get_conversations_from_messages
class User:
    def __init__(self, username, password, role=None, enabled=True):
        self.username = username
        self.password = password
        self.role = role
        self.enabled = enabled

        # Base commands available to ALL user types
        self.parent_commands = [
            {"name": "Go To My Messages", "command": self.messages},
        ]
        self.commands = self.parent_commands

        self.user_manager = UserManager()
        self.camp_manager = CampManager()
        self.message_manager = MessageManager()

    def messages(self):
        self.commands = [
            {"name": "Read messages", "command": self.read_messages},
            {"name": "Send message", "command": self.send_message},
        ]

    def read_messages(self):
        messages = self.message_manager.read_all()

        conversations = get_conversations_from_messages(messages, self.username)

        if not conversations:
            print("You have no messages.")
            return

        print(conversations)

    
    def send_message(self):
        recipient_username = input('Enter the username for recipient: ')
        recipient = self.user_manager.find_user(recipient_username)

        if recipient_username == self.username:
            print('You cannot send a message to yourself')
            return

        if not recipient:
            print('This user does not exist, please try again')
            return

        message_content = input('Enter your message: ')

        message = Message('temp_id', self.username, recipient['username'], message_content)

        self.message_manager.add(message.to_dict())




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

    def display_commands(self):
        for i, command in enumerate(self.commands):
            print(str(i + 1) + ". " + command["name"])

    def process_command(self, commandNumber):
        # Assume commandNumber is a number from interface_main

        # Check it maps correctly
        command = self.commands[commandNumber - 1]["command"]

        command()
