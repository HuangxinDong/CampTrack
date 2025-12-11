from models.sys_notification import SystemNotification
from models.message import Message
from datetime import datetime
import json

def verify_datetime_standardization():
    print("Verifying SystemNotification and Message Date Handling...")
    
    # 1. SystemNotification Test
    print("\n--- SystemNotification ---")
    sys_notif = SystemNotification(
        sys_notification_id="1",
        to_user="user1",
        type="info",
        content="Test notification"
    )
    
    # Check type
    if isinstance(sys_notif.created_at, datetime):
        print(f"PASS: created_at is a datetime object: {sys_notif.created_at}")
    else:
        print(f"FAIL: created_at is NOT a datetime object: {type(sys_notif.created_at)}")

    # Check timezone awareness
    if sys_notif.created_at.tzinfo is not None:
         print("PASS: created_at is timezone-aware")
    else:
         print("FAIL: created_at is NAIVE (not timezone-aware)")

    # Check to_dict
    sys_dict = sys_notif.to_dict()
    print(f"to_dict output: {sys_dict}")
    if isinstance(sys_dict['created_at'], str):
        print("PASS: serialized created_at is a string")
        # Basic ISO format check (contains 'T')
        if 'T' in sys_dict['created_at']:
             print("PASS: serialized format looks like ISO 8601")
        else:
             print("FAIL: serialized format does not look like ISO 8601")
    else:
         print(f"FAIL: serialized created_at is not string: {type(sys_dict['created_at'])}")

    # Check from_dict
    reconstructed_sys = SystemNotification.from_dict(sys_dict)
    if reconstructed_sys.created_at == sys_notif.created_at:
        print("PASS: reconstructed object matches original")
    else:
        print(f"FAIL: reconstructed object mismatch. Original: {sys_notif.created_at}, Reconstructed: {reconstructed_sys.created_at}")


    # 2. Message Test
    print("\n--- Message ---")
    msg = Message(
        message_id="100",
        from_user="alice",
        to_user="bob",
        content="Hello world"
    )

    # Check type
    if isinstance(msg.sent_at, datetime):
        print(f"PASS: sent_at is a datetime object: {msg.sent_at}")
    else:
        print(f"FAIL: sent_at is NOT a datetime object: {type(msg.sent_at)}")

    # Check timezone awareness
    if msg.sent_at.tzinfo is not None:
         print("PASS: sent_at is timezone-aware")
    else:
         print("FAIL: sent_at is NAIVE (not timezone-aware)")

    # Check to_dict
    msg_dict = msg.to_dict()
    print(f"to_dict output: {msg_dict}")
    if isinstance(msg_dict['sent_at'], str):
        print("PASS: serialized sent_at is a string")
        if 'T' in msg_dict['sent_at']:
             print("PASS: serialized format looks like ISO 8601")
        else:
             print("FAIL: serialized format does not look like ISO 8601")
    else:
         print(f"FAIL: serialized sent_at is not string: {type(msg_dict['sent_at'])}")

    # Check from_dict
    reconstructed_msg = Message.from_dict(msg_dict)
    if reconstructed_msg.sent_at == msg.sent_at:
        print("PASS: reconstructed object matches original")
    else:
        print(f"FAIL: reconstructed object mismatch. Original: {msg.sent_at}, Reconstructed: {reconstructed_msg.sent_at}")

if __name__ == "__main__":
    try:
        verify_datetime_standardization()
        print("\nVerification Complete.")
    except Exception as e:
        print(f"\nVerification FAILED with error: {e}")
        import traceback
        traceback.print_exc()
