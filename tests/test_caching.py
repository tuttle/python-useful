from django.test import TestCase
from django.utils.crypto import get_random_string

from tests.testapp.utils import expensive_function


# @override_settings(AUTHENTICATION_BACKENDS=['useful.django.auth.EmailLoginModelBackend', ])
class CachedFunctionTest(TestCase):

    def test_returns_result(self):
        # counts provided arguments
        result = expensive_function(
            1, 'foo', None, 3.123, True,
        )
        self.assertEqual(result, 5)

    def test_returns_result_for_long_arguments(self):
        result = expensive_function(
            1, 'foo', None, 3.123, True,
            get_random_string(200),
            get_random_string(300),
        )
        self.assertEqual(result, 7)

    def test_bytestring(self):
        b_text = b'\xc4\xbe\xc5\xa1\xc4\x8d\xc5\xa5\xc5\xbe\xc3\xbd\xc3\xa1\xc3\xad\xc3\xa9' * 10
        result = expensive_function(
            b_text, b_text.decode('utf-8')
        )
        self.assertEqual(result, 2)
