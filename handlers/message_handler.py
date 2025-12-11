from collections import defaultdict
from typing import Optional

MESSAGE_PREVIEW_LENGTH = 30

def get_conversations_from_messages(messages, username):
    conversations = defaultdict(list)

    for m in messages:
        if m['from_user'] == username:
            conversations[m['to_user']].append(m)
        elif m['to_user'] == username:
            conversations[m['from_user']].append(m)

    return conversations


def count_unread_messages(messages: list[dict], username: str) -> int:
    """
    Count messages where user is recipient and mark_as_read is False.

    Args:
        messages: List of message dictionaries
        username: The current user's username

    Returns:
        Count of unread messages
    """
    count = 0
    for message in messages:
        if message['to_user'] == username and not message['mark_as_read']:
            count += 1
    return count



def get_last_message(messages: list[dict]) -> Optional[dict]:
    """
    Get the most recent message from a list, sorted by sent_at.

    Args:
        messages: List of message dictionaries

    Returns:
        Most recent message dict, or None if empty
    """
    if not messages:
        return None
    
    return max(messages, key=lambda m: m['sent_at'])



def truncate_last_message(content: str, max_length: int = MESSAGE_PREVIEW_LENGTH) -> str:
    """
    Truncate message content for preview display.

    Args:
        content: Full message content
        max_length: Maximum characters to show

    Returns:
        Truncated string with '...' if truncated
    """
    if len(content) <= max_length:
        return content
    
    return content[:max_length] + "..."


def get_conversation_summaries(messages: list[dict], username: str) -> list[dict]:
    """
    Build summary data for each conversation.

    Args:
        messages: All messages from database
        username: Current user's username

    Returns:
        List of dicts with keys: partner, unread_count, last_message, preview
        Sorted by most recent message first
    """
    conversations = get_conversations_from_messages(messages, username)
    
    summaries = []
    for partner, conv_messages in conversations.items():
        last_message = get_last_message(conv_messages)
        
        summary = {
            'partner': partner,
            'unread_count': count_unread_messages(conv_messages, username),
            'last_message': last_message,
            'preview': truncate_last_message(last_message['content']) if last_message else ""
        }
        summaries.append(summary)
    
    # Sort by most recent message first
    summaries.sort(key=lambda s: s['last_message']['sent_at'] if s['last_message'] else "", reverse=True)
    
    return summaries
