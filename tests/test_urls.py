
from django.urls import reverse


def test_resolves_view_defined_url():
    result = reverse('testapp:simple_view')
    assert result == '/testapp/url-simple-view/'
