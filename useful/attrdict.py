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


try:
    from collections import OrderedDict
except ImportError:
    pass
else:
    class OrderedAttrDictSetCollision(Exception):
        """
        Raised when the OrderedAttrDict refuses to change any OrderedDict's attribute.
        """

    class OrderedAttrDict(OrderedDict):
        """
        Like AttrDict, but remembers ordering in which values were set.
        """
        def __setattr__(self, name, value):
            """
            Needs a fork to allow OrderedDict to establish some private names in constructor.
            """
            if name.startswith('_OrderedDict__'):
                return super(OrderedAttrDict, self).__setattr__(name, value)

            if hasattr(OrderedDict, name):
                raise OrderedAttrDictSetCollision(name)

            self[name] = value

        def __getattr__(self, name):
            """
            While AttrDict.__getattr__ is raising KeyError, this one needs to convert it to
            AttributeError as OrderedDict establishes some names in constructor.
            """
            try:
                return self.__getitem__(name)
            except KeyError, e:
                raise AttributeError(e)
