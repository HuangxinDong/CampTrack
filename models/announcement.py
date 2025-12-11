from datetime import datetime

class Announcement:
    def __init__(self, announcement_id, author, content, created_at=None):
        self.announcement_id = announcement_id
        self.author = author
        self.content = content
        self.created_at = created_at if created_at else datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def to_dict(self):
        return {
            'announcement_id': self.announcement_id,
            'author': self.author,
            'content': self.content,
            'created_at': self.created_at
        }

    @staticmethod
    def from_dict(data):
        return Announcement(
            announcement_id=data['announcement_id'],
            author=data['author'],
            content=data['content'],
            created_at=data['created_at']
        )
