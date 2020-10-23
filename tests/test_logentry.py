import json

from django import VERSION
from django.contrib.admin.models import LogEntry
from django.contrib.auth.models import Group, User
from django.forms import ModelForm
from django.http import QueryDict
from django.test import TestCase

from useful.django.logentry import LogEntryAs


class GroupModelForm(ModelForm):
    class Meta:
        model = Group
        fields = 'name',


class LogEntryAsTest(TestCase):

    def setUp(self):
        user = User.objects.create(username='somebody')
        db_logger = LogEntryAs(user, ui=True)

        new_group = Group.objects.create(name='group1')
        db_logger.log_addition(new_group)

        group = Group.objects.get(name='group1')
        form = GroupModelForm(
            data=QueryDict('name=group2'),
            instance=group,
        )
        self.assertTrue(form.is_valid())

        form.save()

        db_logger.log_form_addition_or_change(
            form,
            was_adding=False,
        )

        group = Group.objects.get(name='group2')
        db_logger.log_deletion(group)
        # Not really deleting. :-)

    def test_log_entry(self):
        user = User.objects.get(username='somebody')
        group = Group.objects.get(name='group2')

        self.assertEqual(LogEntry.objects.count(), 3)

        entry1, entry2, entry3 = list(
            LogEntry.objects.order_by('id')
        )

        # Since Django 3.0 the Admin's model history change messages
        # now prefers more readable field labels instead of field names.
        field_desc = "Name" if VERSION[0] >= 3 else "name"
        dash = "\u2014" if VERSION[0] >= 3 else "-"

        self.assertEqual(entry1.user, user)
        self.assertEqual(entry1.object_repr, 'group1')
        self.assertTrue(entry1.is_addition())
        self.assertEqual(
            entry1.change_message,
            json.dumps(
                [{'ui': True}]
            )
        )
        self.assertEqual(str(entry1), 'Added %s.' % s_quote("group1"))
        self.assertEqual(
            entry1.get_change_message(),
            "No fields changed.",
        )
        self.assertEqual(
            entry1.get_edited_object(), group,
        )

        self.assertEqual(entry2.user, user)
        self.assertEqual(entry2.object_repr, 'group2')
        self.assertTrue(entry2.is_change())
        self.assertEqual(
            entry2.change_message,
            json.dumps(
                [{'ui': True}, {'changed': {'fields': [field_desc]}}]
            )
        )
        self.assertEqual(
            str(entry2),
            'Changed %s %s Changed %s.' % (s_quote("group2"), dash, field_desc)
        )
        self.assertEqual(
            entry2.get_change_message(),
            "Changed %s." % field_desc,
        )
        self.assertEqual(
            entry2.get_edited_object(), group,
        )

        self.assertEqual(entry3.user, user)
        self.assertEqual(entry3.object_repr, 'group2')
        self.assertTrue(entry3.is_deletion())
        self.assertEqual(
            entry3.change_message,
            json.dumps(
                [{'ui': True}]
            )
        )
        # Django bug https://code.djangoproject.com/ticket/32136
        self.assertEqual(str(entry3), 'Deleted %s' % s_quote("group2."))
        self.assertEqual(
            entry3.get_change_message(),
            "No fields changed.",
        )
        self.assertEqual(
            entry3.get_edited_object(), group,
        )

        group.delete()


if VERSION[0] >= 3:
    def s_quote(s):
        return '\u201C%s\u201D' % s
else:
    def s_quote(s):
        return '"%s"' % s
