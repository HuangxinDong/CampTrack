def get_positive_int(prompt: str) -> int:
    from .input_utils import get_input
    from .console_manager import console_manager
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
