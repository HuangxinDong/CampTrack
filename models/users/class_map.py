CLASS_MAP = {}

def register(role):
    def decorator(cls):
        CLASS_MAP[role] = cls
        return cls
    return decorator


def user_from_dict(user_dict):
    """
    Convert a dictionary from JSON into the correct User subclass.
    The user class is expected to construct its own UserManager / CampManager.
    """
    role = user_dict.get("role")
    cls = CLASS_MAP.get(role)

    if cls is None:
        return None

    # Remove any keys not accepted by __init__ to avoid TypeError
    import inspect
    sig = inspect.signature(cls.__init__)
    allowed_keys = set(sig.parameters.keys()) - {"self", "args", "kwargs"}
    filtered_dict = {k: v for k, v in user_dict.items() if k in allowed_keys}

    return cls(**filtered_dict)