from django.http import QueryDict
from django.template.loader import render_to_string
from django.test import TestCase


class TemplateTagsTest(TestCase):

    def test_useful_tags(self):
        body_lines = render_to_string(
            'template_for_tags.html',
            context=dict(
                querydict=QueryDict('a=12&b=13'),
                map1={
                    'key1': 'KEY',
                },
                int1=300,
                int2=3000,
                int3=30000,
                int4=300000,
                int1m=-300,
                int2m=-3000,
                int3m=-30000,
                int4m=-300000,
                string1='test',
                string2='TEST',
                begin='te',
                path='/etc/passwd/shadow',
            )
        ).strip().split('\n')

        expected_lines = (
            ('a=newvalue&amp;b=13', 'b=13&amp;a=newvalue'),  # result should be one of these
            'KEY',
            'KEY',
            '300',
            '3 000',
            '30 000',
            '300 000',
            '-300',
            '-3 000',
            '-30 000',
            '-300 000',
            'True',
            'False',
            'shadow',
        )

        for bl, el in zip(body_lines, expected_lines):
            if isinstance(el, tuple):
                self.assertIn(bl, el)
            else:
                self.assertEqual(bl, el)

        self.assertEqual(len(body_lines), len(expected_lines))
