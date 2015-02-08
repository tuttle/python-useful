import os
import stat
import posixpath
import urllib

from django import template
from django.conf import settings
from django.contrib.staticfiles import finders, storage

register = template.Library()

STATIC_URL_CACHE = {}


@register.simple_tag
def freshstatic(path):
    """
    A template tag that returns the URL to a file using staticfiles storage
    backend.

    Example::

        <link rel="stylesheet" type="text/css" href="{% freshstatic "css/reset.css" %}" />

    Note: The staticfiles finder is expected to find the file on which
    os.stat can be run.

    The last modification time is then appended to the resulting URL.
    This has the advantage that the HTTP Expires header can be set to infinite
    and the browsers get different URL each time the file changes.

    Note 2: As the URLs here are cached on the per-process level, it is
    required the Django application is restarted in production each time
    any static file changes the content.
    """
    url = STATIC_URL_CACHE.get(path)
    if url is None:
        # Call the same method the original staticfiles 'static' tag does.
        url = storage.staticfiles_storage.url(path)

        # Get the real file abs path and its timestamp.
        normalized_path = posixpath.normpath(urllib.unquote(path)).lstrip('/')
        absolute_path = finders.find(normalized_path)

        if absolute_path:
            modtime = os.stat(absolute_path)[stat.ST_MTIME]
            url += '?%d' % modtime

        elif not getattr(settings, 'FRESHSTATIC_CAN_BE_MISSING', None):
            raise RuntimeError("Static file %s not found." % path)

        if not settings.DEBUG:
            # Save to cache (only when not developing).
            STATIC_URL_CACHE[path] = url

    return url
