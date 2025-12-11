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

        message_was_found = False
        for i, message in enumerate(messages):
            if message["message_id"] == updatedMessage["message_id"]:
                messages[i] = updatedMessage
                message_was_found = True
                break
        if not message_was_found:
            messages.append(updatedMessage)
        try:
            with open(self.filepath, "w") as f:
                json.dump(messages, f, indent=4)
        except Exception as e:
            logging.error(f"Error writing messages.json: {e}")
            raise  

    def mark_as_read_batch(self, message_ids: list):
        """
        Mark multiple messages as read in a single batch operation.
        Efficiency: O(N) read + O(N) scan + O(1) write.
        """
        if not message_ids:
            return

        messages = self.read_all()
        ids_set = set(message_ids)
        updated = False

        for message in messages:
            if message["message_id"] in ids_set:
                message["mark_as_read"] = True
                updated = True
        
        if updated:
            try:
                with open(self.filepath, "w") as f:
                    json.dump(messages, f, indent=4)
            except Exception as e:
                logging.error(f"Error updating messages batch: {e}")
                raise  

    # -------------------------------------------------------------------------
    # DATA PROCESSING METHODS (Moved from message_handler.py)
    # -------------------------------------------------------------------------

    def get_unread_message_count(self, username: str) -> int:
        """
        Count messages where user is recipient and mark_as_read is False.
        """
        messages = self.read_all()
        count = 0
        for message in messages:
            if message['to_user'] == username and not message.get('mark_as_read', False):
                count += 1
        return count

    def get_conversation_summaries(self, username: str) -> list:
        """
        Build summary data for each conversation.
        Returns list of dicts: {partner, unread_count, last_message, preview}
        Sorted by most recent message first.
        """
        messages = self.read_all()
        conversations = self._get_conversations_from_messages(messages, username)
        
        summaries = []
        for partner, conv_messages in conversations.items():
            last_message = self._get_last_message(conv_messages)
            
            summary = {
                'partner': partner,
                'unread_count': self._count_unread_messages_in_list(conv_messages, username),
                'last_message': last_message,
                'preview': self._truncate_last_message(last_message['content']) if last_message else ""
            }
            summaries.append(summary)
        
        # Sort by most recent message first
        summaries.sort(key=lambda s: s['last_message']['sent_at'] if s['last_message'] else "", reverse=True)
        return summaries

    # Internal Helpers
    
    def _get_conversations_from_messages(self, messages, username):
        from collections import defaultdict
        conversations = defaultdict(list)
        for m in messages:
            if m['from_user'] == username:
                conversations[m['to_user']].append(m)
            elif m['to_user'] == username:
                conversations[m['from_user']].append(m)
        return conversations

    def _count_unread_messages_in_list(self, messages: list, username: str) -> int:
        count = 0
        for message in messages:
            if message['to_user'] == username and not message.get('mark_as_read', False):
                count += 1
        return count

    def _get_last_message(self, messages: list):
        if not messages:
            return None
        return max(messages, key=lambda m: m['sent_at'])

    def _truncate_last_message(self, content: str, max_length: int = 30) -> str:
        if len(content) <= max_length:
            return content
        return content[:max_length] + "..."  


