# Program entry point
from data.user_manager import UserManager
from session import create_session
from program import run_program

# Required for the registers
import models.users.admin
import models.users.coordinator
import models.users.leader

def main():
    user_manager = UserManager()
    users = user_manager.read_all()
    if not users:
        return # data didn't load correctly

    session = create_session(users)
    if session is None:
        return # session must have failed
    
    run_program(session, users)

    return # session has ended
    
if __name__ == "__main__":
    main()