from django.core import urlresolvers
from django.core.exceptions import PermissionDenied
from django.utils.functional import memoize

# This module requires that you use useful.django.urlpatterns.UrlPatterns
# to decorate your views.

_all_callbacks = {}     # caches the callbacks dicts per URLconf


def get_all_callbacks(urlconf):
    """
    Gets the dict translating the view names to view callables for the entire
    given URLconf. Does not allow duplicate view names. Views in non-empty
    namespaces are prefixed with the namespace(s).
    """
    callbacks = {}

    def add_callbacks(resolver, namespace):
        for pattern in resolver.url_patterns:
            if isinstance(pattern, urlresolvers.RegexURLResolver):
                ns = namespace
                if pattern.namespace:
                    ns += (':' if ns else '') + pattern.namespace
                add_callbacks(pattern, ns)

            elif pattern.name is not None:
                ns_name = namespace + (':' if namespace else '') + pattern.name
                prev_callback = callbacks.get(ns_name)
                if prev_callback:
                    if getattr(pattern.callback, 'can_url_perms', None) != \
                       getattr(prev_callback, 'can_url_perms', None):
                        raise RuntimeError("Found multiple URL patterns named %r with different "
                                           "perms. If you want to decorate single view multiple "
                                           "times with urlpatterns.url, add perms= option to the "
                                           "last decorator only, it will apply to all." % ns_name)
                callbacks[ns_name] = pattern.callback

    add_callbacks(urlresolvers.get_resolver(urlconf), '')
    return callbacks
get_all_callbacks = memoize(get_all_callbacks, _all_callbacks, 1)


def can_url(user, view):
    """
    Tests whether the given user would have access to the view. The view can
    be a callable, importable text path or a view name, possibly with the
    namespace prefix ('namespace:view_name'). The view function must be
    decorated with the can_url_func (that's what UrlPatterns class does).
    """
    view = urlresolvers.get_callable(view, True)

    if not callable(view):
        callbacks = get_all_callbacks(urlresolvers.get_urlconf())
        if view not in callbacks:
            raise urlresolvers.NoReverseMatch("Reverse for '%s' not found." % view)

        view = callbacks[view]

    if not hasattr(view, 'can_url_func'):
        raise urlresolvers.NoReverseMatch("Reverse for '%s' is not decorated with permissions." % view)

    try:
        return view.can_url_func(user)
    except PermissionDenied:
        return False


class CanUrl(object):
    """
    Helper wrapper for can_url in templates. Allows for short and readable
    testing, whether the given view is accessible by the current user.
    """
    def __init__(self, user):
        self.user = user

    def __getitem__(self, view_name):
        """
        Support for::
            {% if can_url.view_name %} ...
        """
        return can_url(self.user, view_name)

    def __contains__(self, view_name):
        """
        Support for::
            {% if 'namespace:view_name' in can_url %} ...
        """
        return can_url(self.user, view_name)


def can_url_processor(request):
    """
    A context processor adding the template helper for querying view-level
    permissions like this::

        ### settings.py

        TEMPLATE_CONTEXT_PROCESSORS += (
            ...
            'useful.django.can_url.can_url_processor',
        )

        ### in some template.html

        {% if can_url.view_name %}
            <a href="{% url 'view_name' %}">...</a>
        {% endif %}
    """
    if hasattr(request, 'user'):
        user = request.user
    else:
        from django.contrib.auth.models import AnonymousUser
        user = AnonymousUser()

    return {'can_url': CanUrl(user)}
