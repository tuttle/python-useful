class Choices:
    """
    Encapsulates the choices definition and conversion, praises the DRY.

    Allows for using custom symbols as individual choices, bundles them with i18n-enabled labels
    and stores choices in a way that usually fits more for processing, such as small integers.

    Example::

        class Payment(models.Model):
            STATUS = Choices(initial      = (100, _("Awaiting Payment")),
                             success      = (200, _("Paid OK")),
                             nok_failure  = (300, _("Payment Failed")))
            ...
            status = models.SmallIntegerField(...,
                                              choices=STATUS.choices(),
                                              default=STATUS.initial)
            ...

    Second choice can be referred as Payment.STATUS.success throughout
    the code, equals to 200.
    """
    def __init__(self, **defs):
        """
        Takes the dictionary, where keys are identifiers and values
        are tuples (db id, human value).
        """
        if [True for k in defs if k.startswith('_')]:
            raise RuntimeError("Programming error: Names starting with "
                               "underscore are not allowed in Choices.")
        self.defs = defs
        self.names = dict((v[0], k) for k, v in defs.iteritems())
        self.texts = dict(defs.values())
        if len(set(self.names.keys())) != len(defs):
            raise RuntimeError("Programming error: Duplicate choices defined!")

    def __add__(self, other):
        """
        Support for Choices(...) + Choices(...)
        """
        defs = self.defs.copy()
        defs.update(other.defs)
        return Choices(**defs)

    def choices(self):
        ch = self.defs.values()
        ch.sort(lambda x, y: cmp(x[0], y[0]))
        return ch

    def get(self, name, default=None):
        """
        Example: Choices(...).get('success') -> 200
        """
        return self.defs.get(name, (default,))[0]

    def __getattr__(self, name):
        """
        Example: Choices(...).success -> 200
        """
        if name.startswith('_'):
            raise AttributeError("No attribute %s in Choices class" % name)
        return self.defs[name][0]

    def name_of(self, what):
        """
        Example: name_of(200) -> 'success'
        """
        return self.names[what]

    def text_of(self, what):
        """
        Example: text_of(200) -> "Paid OK"    # note: a gettext string
        """
        return self.texts[what]

    def tuples(self):
        """
        Generates tuples (db id, short name, human name).
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
        return Choices(**dict((k, self.defs[k])
                       for k in keys if k in self.defs))

    def sql_case_ids_to_names(self, field_name):
        whens = ["WHEN %d THEN '%s'" % (v[0], k) for k, v in self.defs.items()]
        return "CASE %s %s ELSE '?' END" % (field_name, ' '.join(whens))


def create_choices_tests(klass):
    """
    Decorator adds is_<choiceset name>_<choice> properties to class
    for all Choices instances inside.
    For example::

        @create_choices_tests
        class Payment:
             # see the docstring of Choices class for details

    so this is possible::

        p = Payment(status=Payment.STATUS.initial)
        if p.is_status_initial:
            (it's true)
    """
    for chname, attr in klass.__dict__.items():
        if isinstance(attr, Choices):
            for name in attr.defs:
                fn = 'is_%s_%s' % (chname.lower(), name)
                if hasattr(klass, fn):
                    raise RuntimeError("create_choices_tests: Attribute %s.%s "
                                       "already exists." % (klass.__name__, fn))
                f = eval("lambda slf: slf.%s == slf.%s.%s" % (chname.lower(),
                                                              chname, name))
                setattr(klass, fn, property(f))
    return klass
