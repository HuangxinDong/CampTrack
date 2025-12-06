# Program entry point
from data.data_manager import UserManager
from session import create_session
from program import run_program

def main():
    user_manager = UserManager()
    data = user_manager.load_data()
    if data is None:
        return # data didn't load correctly

    session = create_session(data.users)
    if session is None:
        return # session must have failed
    
    run_program(session, data)

    return # session has ended
    
if __name__ == "__main__":
    main()