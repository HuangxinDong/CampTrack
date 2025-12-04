
import logging
from models.users import parse_users

# Setup logging
logging.basicConfig(level=logging.INFO)

# Test case 1: Valid JSON
print("--- Test Case 1: Valid JSON ---")
valid_json = """
{
    "Admin": {"username": "admin1", "password": "", "role": "admin", "enabled": "true"},
    "Leader": {"username": "leader1", "password": "", "role": "leader", "enabled": "true", "daily_payment_rate": 100},
    "Coordinator": {"username": "coordinator1", "password": "", "role": "coordinator", "enabled": "true"}
}
"""
success, users = parse_users(valid_json)
print(f"Success: {success}")
print(f"Users: {users}")

# Test case 2: Invalid Key (Case mismatch)
print("\n--- Test Case 2: Invalid Key (admin) ---")
invalid_key_json = """
{
    "admin": {"username": "admin1", "password": "", "role": "admin", "enabled": "true"}
}
"""
success, users = parse_users(invalid_key_json)
print(f"Success: {success}")
print(f"Users: {users}")

# Test case 3: Invalid Structure (List instead of Dict)
print("\n--- Test Case 3: Invalid Structure (List) ---")
invalid_structure_json = """
{
    "Admin": [{"username": "admin1", "password": "", "role": "admin", "enabled": "true"}]
}
"""
success, users = parse_users(invalid_structure_json)
print(f"Success: {success}")
print(f"Users: {users}")

# Test case 4: Missing Argument
print("\n--- Test Case 4: Missing Argument (password) ---")
missing_arg_json = """
{
    "Admin": {"username": "admin1", "role": "admin", "enabled": "true"}
}
"""
success, users = parse_users(missing_arg_json)
print(f"Success: {success}")
print(f"Users: {users}")
