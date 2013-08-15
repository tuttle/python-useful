from .getters import get_object_or_none

from django.contrib.auth.backends import ModelBackend
from django.core.validators import validate_email, ValidationError
from django.utils.crypto import get_random_string

# Django 1.5 swappable model support, backward compatible.
try:
    from django.contrib.auth import get_user_model
except ImportError:
    from django.contrib.auth.models import User as UserModel
else:
    UserModel = get_user_model()


def get_random_password(size=7, cadre='abcdehkmnprstuvxyz2345678923456789'):
    """
    Returns the password composed of the easily readable letters and digits
    by default (digits doubled to increase the occurrence).
    """
    return get_random_string(size, cadre)


def get_unique_username(username):
    """
    Returns the first available username with appended numbering
    (started from 2) that is not yet present in the UserModel table.
    """
    assert username
    base = username
    idx = 2
    while True:
        if not UserModel.objects.filter(username=username).exists():
            break
        username = '%s%d' % (base, idx)
        idx += 1
    return username


class EmailLoginModelBackend(ModelBackend):
    """
    Logs the user in using his/her e-mail (case insensitively by default).
    Set up by the following Django setting::

        AUTHENTICATION_BACKENDS = ('useful.django.auth.EmailLoginModelBackend',)

    """
    EMAIL_CASE_SENSITIVE = False

    def get_user_by_email(self, email):
        try:
            validate_email(email)
            if self.EMAIL_CASE_SENSITIVE:
                user = UserModel.objects.get(email__exact=email)
            else:
                user = UserModel.objects.get(email__iexact=email)
        except (UserModel.DoesNotExist, ValidationError):
            user = None

        return user

    def authenticate(self, username=None, password=None):
        user = self.get_user_by_email(username)
        return user if user and user.check_password(password) else None


class UsernameOrEmailLoginModelBackend(EmailLoginModelBackend):
    """
    Tries to identify the given login-name as username or email
    (both case-insensitive by default).
    Set up by the following Django setting::

        AUTHENTICATION_BACKENDS = ('useful.django.auth.UsernameOrEmailLoginModelBackend',)
    """
    USERNAME_CASE_SENSITIVE = False

    def authenticate(self, username=None, password=None):
        if self.USERNAME_CASE_SENSITIVE:
            user = get_object_or_none(UserModel, username__exact=username)
        else:
            user = get_object_or_none(UserModel, username__iexact=username)

        if user is None:
            user = self.get_user_by_email(username)

        return user if user and user.check_password(password) else None
