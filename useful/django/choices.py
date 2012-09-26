class Choices:
    """
    Encapsulates the choices definitions and conversions.
    Allows for using custom symbols for individual choices and stores
    choices as numbers in the database, instead of 1-letter strings.
    Example::

        class Payment(models.Model):
            STATUS = Choices(initial      = (1, _("Awaiting Payment")),
                             success      = (2, _("Paid OK")),
                             nok_failure  = (3, _("Payment Failed")))
            ...
            status = models.IntegerField(...,
                                         choices=STATUS.choices(),
                                         default=STATUS.initial)

    Second choice can be referred as Payment.STATUS.success throughout
    the code, equals to 2.
    """
    def __init__(self, **defs):
        """
        Takes the dictionary, where keys are short names and values
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
        Example: Choices(...).get('success') -> 2
        """
        return self.defs.get(name, (default,))[0]

    def __getattr__(self, name):
        """
        Example: Choices(...).success -> 2
        """
        if name.startswith('_'):
            raise AttributeError("No attribute %s in Choices class" % name)
        return self.defs[name][0]

    def name_of(self, what):
        """
        Example: name_of(2) -> 'success'
        """
        return self.names[what]

    def text_of(self, what):
        """
        Example: text_of(2) -> 'Paid OK'
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

    this is then possible::

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
