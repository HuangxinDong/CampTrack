class MainUI:
    def __init__(self):
        pass

# Process User Commands
#
# For Each Command, pass in session and data if these are needed
# This ensures that all data is accessible without the need for global scope

def process_user_command(session, data):
    user_input = input("Please enter a valid command\n> ")
    if not user_input.startswith("/"):
        print("Unrecognised command. Please type /help for a list of valid commands.")
        return True
    user_input = user_input[1:]
    user_input = user_input.split(" ")
    match user_input[0]:
        case "exit":
            return False
        case "help":
            print("This would call the help commands")
            return True
        case "admin":
            print("This would call the admin commands")
            return True
        case "leader":
            print("This would call the leader commands")
            return True
        case "coordinator" | "coord":
            print("This would call the coordinator commands")
            return True
        case _:
            print("Unrecognised command. Please type /help for a list of valid commands.")
            return True