from models.users.class_map import user_from_dict
from persistence.dao.user_manager import UserManager

# Not a proper class
class Session:
    def __init__(self):
        self.user_manager = UserManager()

    def login(self):
        from cli.console_manager import console_manager
        
        users = self.user_manager.read_all()
        
        if not users:
            console_manager.print_error('No users found')
            return
        
        while True:
            # Dont tell the user if a username exists or not for security purposes
            error_message = 'Login failed, try again'
            username_input = console_manager.input("Please enter your username (or q to quit): ")
            if username_input == "q":
                return
            password_input = console_manager.input("Please enter your password (or q to quit): ")
            if password_input == 'q':
                return
            
            found_user = next((user for user in users if user["username"] == username_input), None)

            if not found_user:
                console_manager.print_error(error_message)
                continue

            if found_user["password"] != password_input:
                console_manager.print_error(error_message)
                continue
            
            if not found_user.get("enabled", True):
                console_manager.print_error("Account disabled. Please contact admin.")
                continue
            
            console_manager.print_success(f"Welcome {found_user['username']}")

            user_class = user_from_dict(found_user)

            return user_class
