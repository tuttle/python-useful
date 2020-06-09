
from django.test import TestCase

from django.urls import reverse


class PageDecoratorTest(TestCase):

    def test_view_returns_template(self):
        response = self.client.get(
            reverse('template_view'),
        )
        self.assertTemplateUsed(
            response,
            'simple_template.html'
        )
