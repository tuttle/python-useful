
import sys

from django.conf import settings
from django.contrib.auth.models import Permission
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.test import TestCase
from django.test import override_settings
from django.urls import reverse

PY2 = sys.version_info[0] == 2

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'useful.django.can_url.can_url_processor',
            ]
        }
    }
]


def test_resolves_view_defined_url():
    result = reverse('testapp:simple_view')
    assert result == '/testapp/url-simple-view/'

    result = reverse('testapp:other_view')
    assert result == '/testapp/other-view/'


@override_settings(TEMPLATES=TEMPLATES)
class CanUrlTest(TestCase):

    def setUp(self):
        super(CanUrlTest, self).setUp()
        content_type = ContentType.objects.get_for_model(User)
        self.permission = Permission.objects.create(
            codename='can_pass',
            name='Can pass',
            content_type=content_type,
        )
        self.user = User.objects.create(
            username='foo',
        )

    def test_redirects_to_login_if_no_perm(self):
        self.client.force_login(self.user)
        response = self.client.get(
            reverse('testapp:restricted_view'),
        )
        self.assertRedirects(
            response,
            '%s?next=%s' % (
                settings.LOGIN_URL,
                reverse('testapp:restricted_view')
            ),
            fetch_redirect_response=False
        )

    def test_returns_rendered_template_if_perm_ok(self):
        self.user.user_permissions.add(self.permission)
        self.client.force_login(self.user)
        response = self.client.get(
            reverse('testapp:restricted_view'),
        )
        content = response.content
        if not PY2:
            content = content.decode('utf-8')

        print("XXX")
        print(type(content))
        self.assertEqual(response.status_code, 200)
        self.assertIn('restricted_view', content)
        self.assertNotIn('another_restricted_view', content)
