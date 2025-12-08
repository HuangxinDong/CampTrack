def get_positive_int(prompt: str) -> int:
    while True:
        value_str = input(prompt)
        try:
            value = int(value_str)
            if value < 0:
                print("Error: Value must be zero or positive.")
                continue
            return value
        except ValueError:
            print("Error: Please enter a valid integer.")
