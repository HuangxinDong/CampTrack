from .console_manager import console_manager
from cli.input_utils import get_input, cancellable


def get_positive_int(prompt: str) -> int:
    while True:
        value_str = get_input(prompt)
        try:
            value = int(value_str)
            if value < 0:
                console_manager.print_error("Value must be zero or positive.")
                continue
            return value
        except ValueError:
            console_manager.print_error("Please enter a valid integer.")


def get_valid_date_range(
    start_prompt: str = "Enter start date (yyyy-mm-dd): ",
    end_prompt: str = "Enter end date (yyyy-mm-dd): ",
    allow_past_start: bool = False
):
    """
    Get and validate a date range from user input.

    Args:
        start_prompt: Prompt for start date
        end_prompt: Prompt for end date
        allow_past_start: If False, start date must be today or future

    Returns:
        tuple[date, date]: (start_date, end_date)

    Raises:
        BackException: If user cancels (handled by @cancellable)
    """
    from datetime import datetime
    from .input_utils import get_input
    from .console_manager import console_manager

    while True:
        start_str = get_input(start_prompt)
        end_str = get_input(end_prompt)

        try:
            start_date = datetime.strptime(start_str, "%Y-%m-%d").date()
            end_date = datetime.strptime(end_str, "%Y-%m-%d").date()

            if not allow_past_start and start_date < datetime.now().date():
                console_manager.print_error("Start date cannot be in the past.")
                continue

            if end_date < start_date:
                console_manager.print_error("End date must be on or after start date.")
                continue

            return start_date, end_date

        except ValueError:
            console_manager.print_error("Invalid date format. Please use yyyy-mm-dd.")

@cancellable
def get_index_from_options(title, items):
    listed_items = []
    for i, activity in enumerate(items, 1):
            listed_items.append(f"{i}. {activity}")

    invalid_selection_error_message = "Please select a number from the list"
    
    while(True):
            console_manager.print_menu(title, listed_items)
            selection = get_input("Enter number: ")
            if not selection.isdigit():
                print(invalid_selection_error_message)
                continue
            selected_number = int(selection)
            if not (1 <= selected_number <= len(listed_items)):
                print(invalid_selection_error_message)
                continue
            break
    
    selected_index = selected_number - 1
    
    return selected_index