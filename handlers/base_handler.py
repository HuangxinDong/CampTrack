import uuid
from models.message import Message


class BaseHandler:
    """Handles actions available to ALL user types."""
    
    def __init__(self, user, user_manager, message_manager):
        self.user = user
        self.user_manager = user_manager
        self.message_manager = message_manager

    def get_my_messages(self):
        """Returns list of messages for current user."""
        messages = self.message_manager.read_all()
        return [m for m in messages if m['to_user'] == self.user.username]

    def send_message(self, recipient_username, content):
        """
        Send a message to another user.
        Returns (success: bool, message: str)
        """
        # Validate: can't message yourself
        if recipient_username == self.user.username:
            return False, "You cannot send a message to yourself."

        # Validate: recipient must exist
        recipient = self.user_manager.find_user(recipient_username)
        if not recipient:
            return False, "This user does not exist."

        message = Message(
            str(uuid.uuid4()),
            self.user.username,
            recipient['username'],
            content
        )

        try:
            self.message_manager.add(message.to_dict())
            return True, "Message sent successfully."
        except Exception:
            return False, "Failed to send message. Please try again later."