class Choices:
    """
    Encapsulates the choices definition and conversion. Praises the DRY.

    Allows for using custom symbols as individual choices, bundles them with i18n-enabled labels
    and stores choices in a way that usually fits more for processing, such as small integers.

    Example::

        class Payment(models.Model):
            STATUSES = Choices(
                initial      = (100, _("Awaiting Payment")),
                success      = (200, _("Paid OK")),
                nok_failure  = (300, _("Payment Failed")),
            )
            ...
            STATUSES = models.SmallIntegerField(
                ...,
                choices=STATUSES.choices(),
                default=STATUSES.initial,
            )
            ...

    Second choice can be referred to as Payment.STATUSES.success throughout the code, equals to 200.
    """
    reserved_choice_names = {
        'contribute_to_class',
    }

    def __init__(self, **defs):
        """
        Takes the dictionary, where keys are identifiers and values are tuples (db id, text).
        """
        if any(k.startswith('_') for k in defs):
            raise ValueError("Names started by _ are not allowed in Choices.")

        unallowed = set(defs) & self.reserved_choice_names
        if unallowed:
            raise ValueError("Not allowed choice names defined: %s" % ', '.join(unallowed))

        self.defs = defs
        self.names = {v[0]: k for k, v in defs.items()}
        self.texts = dict(defs.values())

        if len(set(self.names)) != len(defs):
            raise ValueError("Duplicate choices defined.")

    def __add__(self, other):
        """
        Support for Choices(...) + Choices(...) by shallow copy.
        """
        defs = self.defs.copy()
        defs.update(other.defs)
        return Choices(**defs)

    def choices(self):
        ch = list(
            self.defs.values()
        )
        ch.sort(
            key=lambda x: x[0],
        )
        return ch

    def get(self, name, default=None):
        """
        Example: Choices(...).get('success') -> 200
        """
        return self.defs.get(
            name,
            (default,)
        )[0]

    def __getattr__(self, name):
        """
        Example: Choices(...).success -> 200
        """
        if name.startswith('_') or name in self.reserved_choice_names:
            raise AttributeError("No such attribute %r in Choices class." % name)

        return self.defs[name][0]

    def name_of(self, what):
        """
        Example: name_of(200) -> 'success'
        """
        return self.names[what]

    def text_of(self, what):
        """
        Example: text_of(200) -> "Paid OK"
        """
        return self.texts[what]

    def tuples(self):
        """
        Generates tuples (db id, short name, text).
        """
        for k, v in self.defs.items():
            # Enforcing i18n by unicode()
            yield v[0], k, unicode(v[1])

    def select(self, keys):
        """
        Returns new Choice object with subset of choices.
        """
        if not isinstance(keys, (list, tuple)):
            keys = [keys]

        return Choices(
            **dict((k, self.defs[k])
                   for k in keys if k in self.defs)
        )
