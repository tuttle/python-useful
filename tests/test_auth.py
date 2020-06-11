
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.test import TestCase
from django.test import override_settings


@override_settings(AUTHENTICATION_BACKENDS=['useful.django.auth.EmailLoginModelBackend', ])
class EmailLoginModelBackendTest(TestCase):

    def test_authenticates_using_email(self):
        user = User(
            username='foobar',
            email='foo@bar.baz'
        )
        user.set_password('qwerty321')
        user.save()

        auth_user = authenticate(username='foo@bar.baz', password='qwerty321')
        self.assertEqual(auth_user, user)

        auth_user = authenticate(username='foobar', password='qwerty321')
        self.assertIsNone(auth_user)


@override_settings(AUTHENTICATION_BACKENDS=['useful.django.auth.UsernameOrEmailLoginModelBackend', ])
class UsernameOrEmailLoginModelBackendTest(TestCase):

    def test_authenticates_using_email(self):
        user = User(
            username='foobar',
            email='foo@bar.baz'
        )
        user.set_password('qwerty321')
        user.save()

        auth_user = authenticate(username='foo@bar.baz', password='qwerty321')
        self.assertEqual(auth_user, user)

        auth_user = authenticate(username='foobar', password='qwerty321')
        self.assertEqual(auth_user, user)
