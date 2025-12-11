from datetime import datetime, timezone
from models.camp import Camp

class SystemNotification:
    def __init__(self, sys_notification_id, to_user, type, content, created_at=None):
        self.sys_notification_id = sys_notification_id
        self.to_user = to_user
        self.type = type
        self.content = content
        self.created_at = created_at if created_at else datetime.now(timezone.utc)

    def to_dict(self):
        return {
            'sys_notification_id': self.sys_notification_id,
            'to_user': self.to_user,
            'type': self.type,
            'content': self.content,
            'created_at': self.created_at.isoformat()
        }

    @staticmethod
    def from_dict(data):
        # Handle backward compatibility if possible, or just expect ISO format now
        try:
            created_at = datetime.fromisoformat(data['created_at'])
        except ValueError:
            # Fallback for old format if necessary, though strict ISO is preferred per plan
             # Assuming we migrate or just start using new format.
             # If strictly creating new objects, this will be fine.
             # If reading old data, might need migration or robust parsing.
             # Proceeding with standard ISO for now as requested.
             pass 
        
        return SystemNotification(
            sys_notification_id=data['sys_notification_id'],
            to_user=data['to_user'],
            type=data['type'],
            content=data['content'],
            created_at=datetime.fromisoformat(data['created_at'])
        )



"""
TODO:
- when food stock goes below threshold, send notification to coordinator 
- 
"""
