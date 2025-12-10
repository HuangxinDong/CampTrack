import uuid
from models.message import Message
from cli.input_utils import get_input, cancellable
from handlers.message_handler import get_conversation_summaries
from cli.display import conversation_display


class BaseHandler:
    """Handles actions available to ALL user types."""
    
    def __init__(self, user, user_manager, message_manager):
        self.user = user
        self.user_manager = user_manager
        self.message_manager = message_manager

        self.parent_commands = [
        {"name": "Go To My Messages", "command": self.messages}
        ]
        self.commands = self.parent_commands.copy()
        self.main_commands = self.commands.copy()


    def get_my_messages(self):
        """Returns list of messages for current user."""
        messages = self.message_manager.read_all()
        return [m for m in messages if m['to_user'] == self.user.username]
    
    def messages(self):
        self.commands = [
            {"name": "Read messages", "command": self.read_messages},
            {"name": "Send message", "command": self.send_message},
        ]


    @cancellable
    def read_messages(self):
        messages = self.message_manager.read_all()
        summaries = get_conversation_summaries(messages, self.user.username)
        
        if not summaries:
            print("No conversations.")
            return
        
        conversation_display.display_list(summaries)
        choice = get_input("")
        
        if choice == "0":
            return
        
        if not choice.isdigit() or int(choice) < 1 or int(choice) > len(summaries):
            print("Invalid selection.")
            return
        
        selected_partner = summaries[int(choice) - 1]['partner']
        self.view_conversation(selected_partner)

    
    @cancellable
    def send_message(self, recipient_username=None):
        # If no recipient provided, ask for one
        if recipient_username is None:
            recipient_username = get_input('Enter the username for recipient: ')

        # Validate: can't message yourself
        if recipient_username == self.user.username:
            print('You cannot send a message to yourself.')
            return

        # Validate: recipient must exist
        recipient = self.user_manager.find_user(recipient_username)
        if not recipient:
            print('This user does not exist, please try again.')
            return

        message_content = get_input('Enter your message: ')

        message = Message(str(uuid.uuid4()), self.user.username, recipient['username'], message_content)

        try:
            self.message_manager.add(message.to_dict())
            print("Message sent successfully.")
        except Exception as e:
            print("Failed to send message. Please try again later.")
