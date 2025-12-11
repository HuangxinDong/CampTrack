import uuid
from handlers.base_handler import BaseHandler
from cli.input_utils import get_input, cancellable, wait_for_enter
from cli.console_manager import console_manager
from models.announcement import Announcement
from persistence.dao.system_notification_manager import SystemNotificationManager
from views import display_user_table



class AdminHandler(BaseHandler):
    """Handles Admin-specific actions."""
    def __init__(self, user, context):

        super().__init__(user, context)

        self.commands = self.parent_commands + [
            {"name": "Create User", "command": self.handle_create_user},
            {"name": "Delete User", "command": self.handle_delete_user},
            {"name": "Enable/Disable User", "command": self.handle_toggle_status},
            {"name": "Update User Info", "command": self.handle_update_user_info},
            {"name": "Post announcement", "command": self.post_announcement},
            {"name": "View Audit Logs", "command": self.view_audit_logs},
            {"name": "View Users", "command": self.view_users},
        ]

        self.main_commands = self.commands.copy()

    def restore_main_commands(self):
        self.commands = self.main_commands


    def view_users(self):
        """Fetches all users from the user manager and displays them in a table."""
        console_manager.console.print("[bold medium_purple1]Fetching user data...[/bold medium_purple1]")
        
        user_list = self.context.user_manager.read_all()
        
        display_user_table(user_list)

        wait_for_enter()


    @cancellable 
    def handle_create_user(self):
        while True:
            username = get_input("Enter username (letters and numbers only): ")
            if not username.strip():
                console_manager.print_error("Username cannot be empty.")
                continue
            if not username.isalnum():
                console_manager.print_error("Username must contain only letters and numbers.")
                continue
            break

        password = get_input("Enter password: ")
        
        # Role is restricted to Leader only
        role = "Leader"
        console_manager.print_info(f"Creating user with role: {role}")
        
        kwargs = {}
        try:
            rate_str = get_input("Enter daily payment rate: ")
            rate = float(rate_str)
            kwargs['daily_payment_rate'] = rate
        except ValueError:
            console_manager.print_warning("Invalid rate, defaulting to 0.0")
            kwargs['daily_payment_rate'] = 0.0

        success, message = self.context.user_manager.create_user(username, password, role=role, **kwargs)
        if success:
            console_manager.print_success(message)
            self.context.audit_log_manager.log_event(self.user.username, "Create User", f"Created user {username} as {role}")
            wait_for_enter()
        else:
            console_manager.print_error(message)
            wait_for_enter()


    @cancellable 
    def handle_delete_user(self):
        while True:
            username = get_input("Enter username to delete: ")
            user = self.context.user_manager.find_user(username)
            if user:
                break
            console_manager.print_error(f"User '{username}' not found. Please try again.")

        confirm = get_input(f"Are you sure you want to delete user '{username}'? (y/n): ")
        if confirm.lower() != 'y':
            console_manager.print_info("Deletion cancelled.")
            return

        success, message = self.context.user_manager.delete_user(username)
        if success:
            console_manager.print_success(message)
            self.context.audit_log_manager.log_event(self.user.username, "Delete User", f"Deleted user {username}")
            wait_for_enter()
        else:
            console_manager.print_error(message)
            wait_for_enter()

    @cancellable
    def handle_toggle_status(self):
        while True:
            username = get_input("Enter username: ")
            user = self.context.user_manager.find_user(username)
            if user:
                break
            console_manager.print_error(f"User '{username}' not found. Please try again.")
            
        if user['username'] == self.user.username:
            console_manager.print_error("You cannot disable your own account.")
            return

        current_status = user.get('enabled', True)
        status_str = "Enabled" if current_status else "Disabled"
        console_manager.print_info(f"Current status for {username}: {status_str}")
        
        if current_status:
            confirm = get_input("Disable user? (y/n): ")
            new_status = False if confirm.lower() == 'y' else True
        else:
            confirm = get_input("Enable user? (y/n): ")
            new_status = True if confirm.lower() == 'y' else False
            
        if new_status != current_status:
            success, message = self.context.user_manager.toggle_user_status(username, new_status)
            console_manager.print_success(message)
            self.context.audit_log_manager.log_event(self.user.username, "Toggle Status", f"Set {username} to {'Enabled' if new_status else 'Disabled'}")
        else:
            console_manager.print_info("No changes made.")
        
        wait_for_enter()

    @cancellable 
    def handle_update_user_info(self):
        console_manager.print_header("Update User Info")
        options = [
            "1. Update Password",
            "2. Update Daily Rate (Leader only)",
            "3. Change Username",
            "4. Change Role"
        ]
        console_manager.print_menu("Options", options)
        
        choice = get_input("Select option: ")
        
        if choice == '1':
            while True:
                username = get_input("Enter username: ")
                if self.context.user_manager.find_user(username):
                    break
                console_manager.print_error(f"User '{username}' not found. Please try again.")

            new_password = get_input("Enter new password: ")
            success, msg = self.context.user_manager.update_password(username, new_password)
            if success: 
                console_manager.print_success(msg)
                self.context.audit_log_manager.log_event(self.user.username, "Update Password", f"Updated password for {username}")
            else: console_manager.print_error(msg)
            wait_for_enter()
        elif choice == '2':
            while True:
                username = get_input("Enter username: ")
                user = self.context.user_manager.find_user(username)
                if user:
                    break
                console_manager.print_error(f"User '{username}' not found. Please try again.")

            if user.get('role') != 'Leader':
                console_manager.print_error(f"User '{username}' is not a Leader.")
                wait_for_enter()
                return
                
            try:
                rate = float(get_input("Enter new daily rate: "))
                success, msg = self.context.user_manager.update_daily_payment_rate(username, rate)
                if success: 
                    console_manager.print_success(msg)
                    self.context.audit_log_manager.log_event(self.user.username, "Update Rate", f"Updated rate for {username} to {rate}")
                else: console_manager.print_error(msg)
            except ValueError:
                console_manager.print_error("Invalid rate.")
            wait_for_enter()
        elif choice == '3':
            while True:
                old_username = get_input("Enter current username: ")
                if self.context.user_manager.find_user(old_username):
                    break
                console_manager.print_error(f"User '{old_username}' not found. Please try again.")

            while True:
                new_username = get_input("Enter new username (letters and numbers only): ")
                if not new_username.strip():
                    console_manager.print_error("Username cannot be empty.")
                    continue
                if not new_username.isalnum():
                    console_manager.print_error("Username must contain only letters and numbers.")
                    continue
                break

            success, msg = self.context.user_manager.update_username(old_username, new_username)
            if success: 
                console_manager.print_success(msg)
                self.context.audit_log_manager.log_event(self.user.username, "Update Username", f"Changed {old_username} to {new_username}")
            else: console_manager.print_error(msg)
            wait_for_enter()
        elif choice == '4':
            while True:
                username = get_input("Enter username: ")
                if self.context.user_manager.find_user(username):
                    break
                console_manager.print_error(f"User '{username}' not found. Please try again.")

            new_role = get_input("Enter new role (Leader/Coordinator): ")
            success, msg = self.context.user_manager.update_role(username, new_role)
            if success: 
                console_manager.print_success(msg)
                self.context.audit_log_manager.log_event(self.user.username, "Update Role", f"Changed {username} role to {new_role}")
            else: console_manager.print_error(msg)
            wait_for_enter()
        else:
            console_manager.print_error("Invalid selection")
            wait_for_enter()

    @cancellable
    def post_announcement(self):
        """Post a new global announcement."""
        console_manager.print_info("Posting new announcement (visible to all users).")
        content = get_input("Enter content: ")
        
        announcement = Announcement(
            announcement_id=str(uuid.uuid4()),
            author=self.user.username,
            content=content
        )
        
        try:
            if self.context.announcement_manager:
                self.context.announcement_manager.add(announcement.to_dict())
                console_manager.print_success("Announcement posted successfully.")
                self.context.audit_log_manager.log_event(self.user.username, "Post Announcement", f"Content: {content[:20]}...")
            else:
                console_manager.print_error("Error: Announcement manager not initialized.")
        except Exception as e:
            console_manager.print_error(f"Error posting announcement: {e}")

    @cancellable
    def view_audit_logs(self):
        logs = self.context.audit_log_manager.read_all()
        if not logs:
            console_manager.print_info("No audit logs found.")
            return

        # Sort by timestamp descending
        logs.sort(key=lambda x: x['timestamp'], reverse=True)

        columns = ["Timestamp", "User", "Action", "Details"]
        rows = []
        for log in logs:
            rows.append([
                log.get("timestamp", ""),
                log.get("username", ""),
                log.get("action", ""),
                log.get("details", "")
            ])
        
        console_manager.print_table("System Audit Logs", columns, rows)
        wait_for_enter()