# Based on commit 111397cd41db41b2acec84473649b6f291a9c272 of
# https://github.com/ui/django-cached_authentication_middleware/
# Replaced User with UserModel to support the Django 1.5 swappable model.

"""
Copyright (c) 2012 Selwin Ong

Permission is hereby granted, free of charge, to any person obtaining
a copy of this software and associated documentation files (the
"Software"), to deal in the Software without restriction, including
without limitation the rights to use, copy, modify, merge, publish,
distribute, sublicense, and/or sell copies of the Software, and to
permit persons to whom the Software is furnished to do so, subject to
the following conditions:

The above copyright notice and this permission notice shall be
included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
"""

from django.apps import apps
from django.conf import settings
from django.contrib.auth import SESSION_KEY, get_user, get_user_model
from django.contrib.auth.middleware import AuthenticationMiddleware
from django.core import cache  # Importing this way so debug_toolbar can patch it later.
from django.db.models.signals import post_delete, post_save
from django.utils.functional import SimpleLazyObject

UserModel = get_user_model()

CACHE_KEY = 'cached_auth_middleware_1.5:%s'

# The profile model support have been deprecated in Django long time ago.
# Nevertheless some projects might still be using it.
try:
    app_label, model_name = settings.AUTH_PROFILE_MODULE.split('.')
    profile_model = apps.get_model(app_label, model_name)
except (ValueError, AttributeError):
    profile_model = None


# noinspection PyUnusedLocal
def invalidate_cache(sender, instance, **kwargs):
    if isinstance(instance, UserModel):
        key = CACHE_KEY % instance.id
    else:
        key = CACHE_KEY % instance.user_id

    cache.cache.delete(key)


def get_cached_user(request):
    from django.contrib.auth.models import AnonymousUser

    if not hasattr(request, '_cached_user'):
        try:
            key = CACHE_KEY % request.session[SESSION_KEY]
            user = cache.cache.get(key)
        except KeyError:
            user = AnonymousUser()
        else:
            if user is None:
                user = get_user(request)

                # Try to populate profile cache if profile is installed
                if profile_model:
                    try:
                        user.get_profile()
                    # Handle exception for user with no profile and AnonymousUser
                    except (profile_model.DoesNotExist, AttributeError):
                        pass

                cache.cache.set(key, user)

        request._cached_user = user

    # noinspection PyProtectedMember
    return request._cached_user


class CachedAuthenticationMiddleware(AuthenticationMiddleware):
    """
    A drop-in replacement for django.contrib.auth's built-in
    AuthenticationMiddleware. It tries to populate request.user by fetching
    user and profile data from cache before falling back to the database.

    'django.contrib.auth.middleware.AuthenticationMiddleware' in
    settings.MIDDLEWARE_CLASSES can be replaced with
    'useful.django.cached_auth.CachedAuthenticationMiddleware'.
    """
    def __init__(self, *args, **kwargs):
        post_save.connect(invalidate_cache, sender=UserModel)
        post_delete.connect(invalidate_cache, sender=UserModel)

        if profile_model:
            post_save.connect(invalidate_cache, sender=profile_model)
            post_delete.connect(invalidate_cache, sender=profile_model)

        super().__init__(*args, **kwargs)

    def process_request(self, request):
        assert hasattr(request, 'session'), \
            "The Django authentication middleware requires session middleware to be installed. "\
            "Edit your MIDDLEWARE_CLASSES setting to insert 'django.contrib.sessions.middleware.SessionMiddleware'."

        request.user = SimpleLazyObject(
            lambda: get_cached_user(request)
        )
