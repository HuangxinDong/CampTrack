# Session Manager

from .session import Session
from models import User

def create_session(users: list[User]):
    # 1. Login user against users data
    user = login(users)
    if user is None:
        return None

    print(f"Welcome {user.username}")
    # 2. Create the session object
    session = Session(user)

    return session

def login(users: list[User]):
    valid_input = False
    while not valid_input:
        username_input = input("Please enter your username: ")
        if username_input == "/exit":
            print("Exiting program.")
            return None
        
        found_user = None

        for user in users:
            if user.username == username_input:
                found_user = user
                break

        if found_user is None:
            print("Username not recognised. Please enter a valid username, or type /exit to close the program.")
        else:
            password_input = input("Please enter your password: ")
            if found_user.password == password_input:
                valid_input = True
                return found_user
            else:
                print("Password invalid. Please login with valid credentials, or type /exit to close the program.")