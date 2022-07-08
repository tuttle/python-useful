import re

from django.conf import settings
from django.utils.translation import get_language


def get_safe_langcode():
    """
    Returns two-letter code of the active language.
    Is always one of the supported languages. 'en' is expected to exist!
    """
    lang = get_language()[:2].lower()
    return lang if lang in dict(settings.LANGUAGES) else 'en'


def add_language_getter_for(*field_names):
    """
    Class decorator. For each field given as argument, adds a reading property
    with the same name to the wrapped class. When that property is accessed
    in the instance the value of the real field <field_name>_<lang> is
    returned, where lang is the current Django language two-letter code.
    In case the attribute for the current language does not exist
    or its content is empty, the english value is returned as a fallback.
    """
    def get_getter_for(fld):
        def getter(slf):
            value = getattr(slf, fld + '_' + get_safe_langcode(), None)
            if not value:
                value = getattr(slf, fld + '_en')
            return value
        return getter

    def add_language_getter(klass):
        for fld in field_names:
            if not re.match('^[_a-zA-Z][_a-zA-Z0-9]*$', fld):
                raise RuntimeError("Field name %r has not a valid identifier "
                                   "syntax." % fld)
            if not hasattr(klass, '_language_getters'):
                klass._language_getters = set()
            if fld not in klass._language_getters and hasattr(klass, fld):
                raise RuntimeError("add_language_getter: Attribute %s.%s "
                                   "already exists." % (klass.__name__, fld))

            setattr(klass, fld, property(get_getter_for(fld)))
            klass._language_getters.add(fld)
        return klass
    return add_language_getter
