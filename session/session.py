from models.users.class_map import user_from_dict
from persistence.dao.user_manager import UserManager

# Not a proper class
class Session:
    def __init__(self):
        self.user_manager = UserManager()

    def login(self):
        users = self.user_manager.read_all()
        
        if not users:
            print('No users found')
            return
        
        while True:
            # Dont tell the user if a username exists or not for security purposes
            error_message = 'Login failed, try again'
            username_input = input("Please enter your username (or q to quit): ")
            if username_input == "q":
                return
            password_input = input("Please enter your password (or q to quit): ")
            if password_input == 'q':
                return
            
            found_user = next((user for user in users if user["username"] == username_input), None)

            if not found_user:
                print(error_message)
                continue

            if found_user["password"] != password_input:
                print(error_message)
                continue
            
            print(f"Welcome {found_user['username']}")

            user_class = user_from_dict(found_user)

            return user_class
