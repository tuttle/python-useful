def int_or_0(value):
    try:
        return int(value)
    except (ValueError, TypeError):
        return 0


def int_or_None(value):
    try:
        return int(value)
    except (ValueError, TypeError):
        return None
