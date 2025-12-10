from datetime import datetime


class Message:
    def __init__(
        self, message_id, from_user, to_user, content, sent_at = None, mark_as_read=False
    ):
        if sent_at is None:
            sent_at = datetime.now()
            
        self.message_id = message_id    
        self.from_user = from_user
        self.to_user = to_user
        self.content = content
        self.sent_at = sent_at
        self.mark_as_read = mark_as_read

    def to_dict(self):
        return {
            "message_id": self.message_id,
            "from_user": self.from_user,
            "to_user": self.to_user,
            "content": self.content,
            "sent_at": self.sent_at.isoformat(),
            "mark_as_read": self.mark_as_read,
        }

    @classmethod
    def from_dict(cls, data):
        sent_at = datetime.fromisoformat(data["sent_at"])
        message = cls(
            message_id=data["message_id"],
            from_user=data["from_user"],
            to_user=data["to_user"],
            content=data["content"],
            sent_at=sent_at,
            mark_as_read=data["mark_as_read"],
        )

        return message
