import json

def make_message(msg_type, content):
    """
    Create a JSON-encoded message for sending over the socket.
    msg_type: 'chat', 'move', etc.
    content: dictionary with message data
    """
    return json.dumps({'type': msg_type, 'content': content}).encode()

def parse_message(data):
    """
    Parse a JSON-encoded message received from the socket.
    Returns a dictionary with 'type' and 'content'.
    """
    try:
        return json.loads(data)
    except Exception:
        return {'type': 'invalid', 'content': {}}
