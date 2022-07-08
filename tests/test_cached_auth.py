
from django.core.management import call_command
from django.test import TestCase
from django.test import override_settings


MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    # 'django.contrib.auth.middleware.AuthenticationMiddleware',
    'useful.django.cached_auth.CachedAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]


@override_settings(MIDDLEWARE=MIDDLEWARE)
class CachedAuthenticationMiddlewareTest(TestCase):

    def test_passes_checks(self):
        call_command('check', 'admin')
