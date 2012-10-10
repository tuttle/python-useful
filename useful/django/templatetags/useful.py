import re
import urllib

from django import template
from django.template.defaultfilters import stringfilter
from django.utils.encoding import force_unicode
from django.utils.safestring import mark_safe
from django.utils.html import urlize

register = template.Library()


@register.simple_tag
def querydict_set(querydict, param_name, param_value):
    """
    Adds/replaces specific parameter in the querydict.
    For example see the docstring for useful.django.views.paginate.
    """
    # Make it mutable.
    querydict = querydict.copy()
    # Set the value.
    querydict[param_name] = param_value
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


@register.filter(is_safe=True)
def intspace(value):
    """
    Converts an integer to a string containing spaces every three digits.
    For example, 3000 becomes '3 000' and 45000 becomes '45 000'.
    """
    orig = force_unicode(value)
    new = re.sub("^(-?\d+)(\d{3})", '\g<1> \g<2>', orig)
    return new if orig == new else intspace(new)


@register.filter(is_safe=True)
def intspace_r(value):
    """
    Like intspace, but orders groups of 1 or 2 digits to the end
    instead of the beginning.
    """
    return intspace(force_unicode(value)[::-1])[::-1]


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
    Converts URLs into clickable links, truncating URLs to the given character
    limit, and adding 'rel=nofollow' attribute to discourage spamming.
    The target is opened in the blank browser window.

    Argument: Length to truncate URLs to.
    """
    value = value.replace(' ', '%20')
    u = urlize(value, trim_url_limit=int(limit), nofollow=True, autoescape=autoescape)
    if u.startswith('<a '):
        u = '<a target="_blank" ' + u[3:]
    return mark_safe(u)
urlizetruncblank.is_safe = True
urlizetruncblank.needs_autoescape = True


@register.filter
def urlquote_plus(url):
    return force_unicode(urllib.quote_plus(url))


@register.filter
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
