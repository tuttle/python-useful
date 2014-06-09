from collections import defaultdict

from django.db import connection
from django.db.models.manager import Manager
from django.db.models.query import QuerySet


def _get_queryset(klass):
    """
    Returns a QuerySet from a Model, Manager, or QuerySet.

    NoDRY: Function copied from __init__ in django.shortcuts to assure stability.
    """
    if isinstance(klass, QuerySet):
        return klass
    elif isinstance(klass, Manager):
        manager = klass
    else:
        manager = klass._default_manager
    return manager.all()


def get_object_or_none(klass, *args, **kwargs):
    """
    Uses get() to return an object, or None if the object does not exist.

    klass may be a Model, Manager, or QuerySet object. All other passed
    arguments and keyword arguments are used in the get() query.

    Note: Like with get(), an MultipleObjectsReturned will be raised if more than one
    object is found.
    """
    queryset = _get_queryset(klass)
    try:
        return queryset.get(*args, **kwargs)
    except queryset.model.DoesNotExist:
        return None


def get_object_or_new(klass, *args, **kwargs):
    """
    Uses get() to return an object. If it does not exist, a new UNSAVED
    object of the given model is returned.

    klass may be a Model, Manager, or QuerySet object. All other passed
    arguments and keyword arguments are used in the get() query.

    Note: Like with get(), an MultipleObjectsReturned will be raised if more than one
    object is found.
    """
    queryset = _get_queryset(klass)
    try:
        return queryset.get(*args, **kwargs)
    except queryset.model.DoesNotExist:
        return queryset.model(*args, **kwargs)


def prefetch_m2m(m2m_field):
    """
    Loads all objects from the target table of the given ManyToManyField,
    then loads the entire intermediary join table.
    Returns the lookup where key is the object id and value is the list
    of target objects.

    Usage example to get comma-separated list of user's groups in template::

        groups_m2m = prefetch_m2m(User.groups)

          {{ groups_m2m|get:user.id|default_if_none:""|join:", " }}
    """
    f = m2m_field.field
    tgt_objs = dict((o.pk, o) for o in f.rel.to.objects.all())

    cursor = connection.cursor()
    cursor.execute("SELECT %s, %s FROM %s" % (f.m2m_column_name(),
                                              f.m2m_reverse_name(),
                                              f.m2m_db_table()))
    lookup = defaultdict(list)
    for src, tgt in cursor.fetchall():
        lookup[src].append(tgt_objs[tgt])

    return lookup


def get_values_map(klass, by, *fields):
    """
    Creates the Python set or dict from data in klass.
    klass may be a Model, Manager, or QuerySet object.
    If no fields are given, the result is the set of all distinct values of 'by'.
    If fields is a single field, the result is dict by->field.
    Otherwise the key of dict is still 'by', the value is tuple of fields.
    """
    queryset = _get_queryset(klass)

    iterator = queryset.values_list(by, *fields).order_by().iterator()

    if len(fields) > 1:
        return dict((tup[0], tup[1:]) for tup in iterator)

    elif len(fields) == 1:
        return dict(iterator)

    else:
        return set(queryset.values_list(by, flat=True).distinct().order_by().iterator())
