from collections import defaultdict

def get_conversations_from_messages(messages, username):
    conversations = defaultdict(list)

    for m in messages:
        if m['from_user'] == username:
            conversations[m['to_user']].append(m)
        elif m['to_user'] == username:
            conversations[m['from_user']].append(m)

    return conversations

