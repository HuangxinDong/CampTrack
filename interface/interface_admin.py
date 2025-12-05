from managers.user_manager import UserManager

class AdminUI:
    def __init__(self, data):
        self.user_manager = UserManager(data)

    def handle_create_user(self):
        username = input("Enter username: ")
        password = input("Enter password: ")
        role = input("Enter role (Leader/Coordinator): ")
        
        success, message = self.user_manager.create_user(username, password, role)
        print(message)

    def handle_delete_user(self):
        username = input("Enter username to delete: ")
        success, message = self.user_manager.delete_user(username)
        print(message)
