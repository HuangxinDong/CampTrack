# Program entry point
from session.session import Session
from program import run_program

# Required for the registers
import models.users.admin
import models.users.coordinator
import models.users.leader

def main():
    session = Session()
    user = session.login()
    if not user:
        return
    
    run_program(user)

    return # session has ended
    
if __name__ == "__main__":
    main()