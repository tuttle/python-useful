from collections import defaultdict

from django.db import connection
from django.shortcuts import get_object_or_404
from django.http import Http404


def get_object_or_none(klass, **kwargs):
    """
    Gets the object of the model/manager/queryset by kwargs.
    None if not found.
    """
    try:
        return get_object_or_404(klass, **kwargs)
    except Http404:
        return None


def get_object_or_new(klass, **kwargs):
    """
    Gets the object of the model/manager/queryset by kwargs.
    Creates new using the keywords, but does not save it.
    """
    try:
        return get_object_or_404(klass, **kwargs)
    except Http404:
        return klass(**kwargs)


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
