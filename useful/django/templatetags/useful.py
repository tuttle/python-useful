import os
import re

from django import template
from django.template.defaultfilters import stringfilter
from django.utils.encoding import force_text
from django.utils.safestring import mark_safe
from django.utils.html import urlize
from django.utils.http import urlquote_plus as django_urlquote_plus

register = template.Library()


@register.simple_tag
def querydict_set(querydict, param_name, param_value):
    """
    Adds/replaces/deletes specific parameter in the querydict.

    Usage example::

        <a href="?{% querydict_set request.GET 'order' 'code' %}">
    """
    # Make it mutable.
    querydict = querydict.copy()

    # Set or delete the value.
    if force_text(param_value):
        querydict[param_name] = param_value
    else:
        querydict.pop(param_name, None)

    # Encode into the query string.
    return querydict.urlencode()


@register.filter
def get(mapping, key):
    """
    Gets value from mapping or None.
    Example::
        {{ choices.countries|get:item.country_id }}
    """
    return mapping.get(key)


@register.filter
def getfrom(key, mapping):
    """
    Gets value from mapping or None (reversed arguments).
    Example (need to convert the year's value to int first)::
        {{ d.0|get:year|add:0|getfrom:choices.turnover }}
    """
    return mapping.get(key)


INTSPACE_RE = re.compile(r'^(-?\d+)(\d{3})')


@register.filter(is_safe=True)
def intspace(value):
    """
    Converts an integer to a string containing spaces every three digits.
    For example, 3000 becomes '3 000' and 45000 becomes '45 000'.
    """
    orig = force_text(value)
    new = INTSPACE_RE.sub('\g<1> \g<2>', orig)
    return new if orig == new else intspace(new)


@register.filter(is_safe=True)
def intspace_r(value):
    """
    Like intspace, but orders groups of 1 or 2 digits to the end
    instead of the beginning.
    """
    return intspace(force_text(value)[::-1])[::-1]


@register.filter
def startswith(s1, s2):
    """
    Proxy to the startswith method.
    """
    return s1.startswith(s2)


@register.filter
@stringfilter
def urlizetruncblank(value, limit, autoescape=None):
    """
    Converts URLs in text into clickable links, truncating URLs to the given character
    limit, and adding 'rel=nofollow' attribute to discourage spamming.
    The target is opened in the blank browser window.

    Argument: Length to truncate URLs to.
    """
    u = urlize(value, trim_url_limit=int(limit), nofollow=True, autoescape=autoescape)
    u = u.replace('<a ', '<a target="_blank" ')
    return mark_safe(u)
urlizetruncblank.is_safe = True
urlizetruncblank.needs_autoescape = True


@register.filter(is_safe=False)
@stringfilter
def urlquote_plus(value, safe=None):
    """
    Escapes a value for use in a URL, but also replaces spaces by plus signs, as required
    for quoting HTML form values when building up a query string to go into a URL.
    This is a _plus version of the standard Django urlencode defaultfilter.
    """
    kwargs = {}
    if safe is not None:
        kwargs['safe'] = safe
    return django_urlquote_plus(value, **kwargs)


@register.filter
@stringfilter
def middle_truncate(value, size):
    """
    Truncates a string to the given size placing the ellipsis in the middle.
    """
    size = int(size)
    if len(value) > size:
        if size > 3:
            start = (size - 3) / 2
            end = (size - 3) - start
            return value[:start] + u'\u2026' + value[-end:]
        else:
            return value[:size] + u'\u2026'
    else:
        return value


@register.filter
def file_exists(fieldfile):
    """
    Calls the file storage backend to test whether the file physically exists.
    There's no obvious way Django 1.6 offers this.

    Example given your Comment model has `attachment` FileField::

        <a href="{{ comment.attachment.url }}">
            {{ comment.attachment.name|strip_path }}
        </a>
        {% if comment.attachment|file_exists %}
            ({{ comment.attachment.size|filesizeformat }})
        {% endif %}
    """
    return fieldfile.storage.exists(fieldfile.path)


@register.filter
@stringfilter
def strip_path(filepath):
    """
    'same/path/to/filename.jpg' -> 'filename.jpg'

    For example usage see doc of file_exists.
    """
    return os.path.split(filepath)[1]
