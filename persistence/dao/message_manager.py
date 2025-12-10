import json
import logging
import os

class MessageManager:
    def __init__(self, filepath="persistence/data/messages.json"):
        self.filepath = filepath
        self._ensure_file()

    def _ensure_file(self):
        if not os.path.exists(self.filepath):
            os.makedirs(os.path.dirname(self.filepath), exist_ok=True)
            with open(self.filepath, "w") as f:
                f.write("[]")

    def read_all(self):
        with open(self.filepath, "r") as f:
            try:
                data = json.load(f)
            except Exception as e:
                logging.error(f"Error reading messages.json: {e}")
                raise

        if not isinstance(data, list):
            raise ValueError("messages.json must contain a JSON array.")

        return data

    def add(self, message):
        messages = self.read_all()
        messages.append(message)

        try:
            with open(self.filepath, "w") as f:
                json.dump(messages, f, indent=4)
        except Exception as e:
            logging.error(f"Error writing messages.json: {e}")
            raise
        
    def update(self, updatedMessage):
        """
        Read messages from json, find the message to update and insert message into data 
        """
        messages = self.read_all()
        for i, message in enumerate(messages):
            if message.message_id == updatedMessage.message_id:
                messages[i] = updatedMessage
                break
            else:
                messages.append(updatedMessage)

        data = [m.to_dict() for m in messages]
        try:
            with open(self.filepath, "w") as f:
                json.dump(data, f, indent=4)
        except Exception as e:
            logging.error(f"Error writing messages.json: {e}")
            raise  


