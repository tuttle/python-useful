class AttrDictSetCollision(Exception):
    """
    Raised when the AttrDict refuses to change any dict's attribute.
    """


class AttrDict(dict):
    """
    This is a dict whose values can be accessed also as attributes.
    Setting attribute occuring in the original dict class is forbidden.
    """
    def __setattr__(self, name, value):
        if hasattr(dict, name):
            raise AttrDictSetCollision(name)

        self[name] = value

    __getattr__ = dict.__getitem__
