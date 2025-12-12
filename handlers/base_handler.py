import uuid
from models.message import Message
from cli.input_utils import get_input, cancellable, wait_for_enter
from cli.chat_display import conversation_display
from cli.console_manager import console_manager


class BaseHandler:
    """Handles actions available to ALL user types."""
    
    def __init__(self, user, context):
        self.user = user
        self.context = context

        self.parent_commands = [
            {"name": "View messages", "command": self.view_messages},
            {"name": "Send message", "command": self.send_message},
            {"name": "View announcements", "command": self.view_announcements},
        ]
        self.commands = self.parent_commands.copy()
        self.main_commands = self.commands.copy()

        self.message_view_commands = [
            {"name": "View specific chat", "command": self.view_chat},
            {"name": "Send new message", "command": self.send_message},
            {"name": "Search conversation", "command": self.search_conversation},
        ]
        
        # Optimization: Cache summaries to avoid redundant reads between menus
        self.current_summaries = []

    def search_conversation(self):
        """Search for a user and open chat."""
        partner = self.get_username_with_search("Enter username to search chat", exclude_self=True)
        
        # Check if user exists (get_username_with_search returns a string, we should verify it's a real user if they typed it manually)
        if not self.context.user_manager.find_user(partner):
            console_manager.print_error(f"User '{partner}' not found.")
            return

        self._interact_with_chat(partner)

    def _interact_with_chat(self, partner):
        """Helper to display and interact with a chat thread."""
        try:
            messages = self.context.message_manager.read_all()
            
            chat = []
            for m in messages:
                if (m['from_user'] == self.user.username and m['to_user'] == partner) or \
                   (m['from_user'] == partner and m['to_user'] == self.user.username):
                    chat.append(m)

            if not chat:
                console_manager.print_info(f"No message history with {partner}.")
                if get_input("Start new conversation? (y/n): ").lower() == 'y':
                    self.send_message(recipient_username=partner)
                return

            # Mark unread messages as read
            unread_ids = [m['message_id'] for m in chat 
                         if m['to_user'] == self.user.username and not m.get('mark_as_read', False)]
            
            if unread_ids:
                self.context.message_manager.mark_as_read_batch(unread_ids)

            while True:
                conversation_display.display_chat_thread(partner, chat, self.user.username)
                
                action = get_input("")
                
                if action.lower() == 'r':
                    self.send_message(recipient_username=partner)
                    all_messages = self.context.message_manager.read_all()
                    
                    chat = []
                    for m in all_messages:
                        if (m['from_user'] == self.user.username and m['to_user'] == partner) or \
                           (m['from_user'] == partner and m['to_user'] == self.user.username):
                            chat.append(m)
                    continue
                
                break
            
        except Exception as e:
            from cli.input_utils import QuitException, BackException
            if isinstance(e, BackException):
                return
            if isinstance(e, QuitException):
                raise e
            print(f"Error viewing chat: {e}")

    def get_username_with_search(self, prompt, role_filter=None, exclude_self=False):
        """
        Helper to get a username with an option to search/list users.
        """
        while True:
            user_input = get_input(f"{prompt} (enter 's' to search): ")
            
            if user_input.lower() == 's':
                users = self.context.user_manager.read_all()
                
                # Filter
                if role_filter:
                    users = [u for u in users if u.get('role') == role_filter]
                
                if exclude_self:
                    users = [u for u in users if u['username'] != self.user.username]
                
                if not users:
                    console_manager.print_info("No matching users found.")
                    continue
                
                # Display
                console_manager.print_header("Available Users")
                from rich.table import Table
                table = Table(show_header=True, header_style="bold magenta")
                table.add_column("Username")
                table.add_column("Role")
                
                for u in users:
                    table.add_row(u['username'], u.get('role', 'Unknown'))
                
                console_manager.console.print(table)
                continue
            
            return user_input

    def get_notifications(self):
        notifications = [self.get_unread_message_alert()]
        return notifications

    def get_unread_message_alert(self):
        """Returns notification string if unread messages exist."""
        count = self.context.message_manager.get_unread_message_count(self.user.username)
        if count > 0:
            return f"You have {count} unread messages\n"
        return None

    def get_my_messages(self):
        """Returns list of messages for current user."""
        messages = self.context.message_manager.read_all()
        return [m for m in messages if m['to_user'] == self.user.username]


    @cancellable
    def view_messages(self):
        """
        View all messages for the current user.
        """
        while True:
            # Update cache for view_chat to use
            # Refactored: Use manager method directly
            self.current_summaries = self.context.message_manager.get_conversation_summaries(self.user.username)
            
            if not self.current_summaries:
                print("No conversations.")
                return
            
            conversation_display.display_list(self.current_summaries)
            
            # Dynamic Menu Display
            # Dynamic Menu Display
            menu_options = [f"[bold medium_purple1]{i + 1}.[/bold medium_purple1] {cmd['name']}" for i, cmd in enumerate(self.message_view_commands)]
            console_manager.print_menu("OPTIONS", menu_options)
            console_manager.print_message("\n[bold medium_purple1]Enter number, 'b' to go back, or 'q' to quit[/bold medium_purple1]")
            
            
            choice = get_input("")
            
            # Try to match index
            try:
                idx = int(choice) - 1
                if 0 <= idx < len(self.message_view_commands):
                    self.message_view_commands[idx]['command']()
                else:
                    print("Invalid selection.")
            except ValueError:
                print("Invalid selection.")

    def view_chat(self):
        """
        Ask user for conversation number, validate, and show thread.
        """
        prompt = "Enter conversation number: "
        
        # Optimization: Use cached summaries from view_messages if available
        # This prevents reading the file and calculating summaries twice
        if not self.current_summaries:
             # Fallback if accessed directly (though unlikely in current flow)
             # Refactored: Use manager method directly
             self.current_summaries = self.context.message_manager.get_conversation_summaries(self.user.username)

        if not self.current_summaries:
            print("No conversations to view.")
            return

        try:
            choice = get_input(prompt)
            
            # Helper: Validates if input is a valid index for the list
            if not choice.isdigit():
                print("Invalid selection.")
                return

            idx = int(choice) - 1
            if idx < 0 or idx >= len(self.current_summaries):
                print("Invalid selection.")
                return
            
            # Valid selection -> Show thread
            partner = self.current_summaries[idx]['partner']
            self._interact_with_chat(partner)

        except Exception as e:
            from cli.input_utils import QuitException, BackException
            if isinstance(e, BackException):
                return
            if isinstance(e, QuitException):
                raise e
            print(f"Error viewing chat: {e}")

    @cancellable
    def view_announcements(self):
        """View all announcements."""
        console_manager.print_header("CAMP ANNOUNCEMENTS")
        
        if not self.context.announcement_manager:
              console_manager.print_error("Announcement service unavailable.")
              wait_for_enter()
              return

        announcements = self.context.announcement_manager.read_all()
        
        if not announcements:
             console_manager.print_info("No announcements yet.")
        else:
             # Sort latest first
             announcements.sort(key=lambda x: x['created_at'], reverse=True)
             
             for a in announcements:
                  content = f"[bold]{a['author']}[/bold] ({a['created_at']}):\n{a['content']}"
                  console_manager.print_panel(content, style="blue")
        
        console_manager.print_message("═"*40)
        wait_for_enter()


    @cancellable
    def send_message(self, recipient_username=None):
        # 1. REPLY CONTEXT (Recipient provided)
        if recipient_username:
             # Just check once to be safe, though usually safe from chat context
             if recipient_username == self.user.username:
                 print('You cannot send a message to yourself.')
                 return
             if not self.context.user_manager.find_user(recipient_username):
                 print('This user does not exist.')
                 return

        # 2. NEW MESSAGE CONTEXT (Recipient is None) - Loop until valid
        while recipient_username is None:
            username_input = self.get_username_with_search("Enter the username for recipient or 'b' to go back ", exclude_self=True)
            
            # Validate: can't message yourself
            if username_input == self.user.username:
                print('You cannot send a message to yourself.')
                continue
            
            # Validate: recipient must exist
            recipient = self.context.user_manager.find_user(username_input)
            if not recipient:
                print('This user does not exist, please try again.')
                continue
            
            # Valid!
            recipient_username = username_input

        # At this point, recipient_username is valid
        message_content = get_input('Enter your message: ')

        message = Message(str(uuid.uuid4()), self.user.username, recipient_username, message_content)

        try:
            self.context.message_manager.add(message.to_dict())
            console_manager.print_success("Message sent successfully.")
        except Exception as e:
            print("Failed to send message. Please try again later.")
