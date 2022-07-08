from django.contrib.auth.models import Group, User
from django.test import TestCase

from useful.django.getters import prefetch_m2m


class PrefetchM2MTest(TestCase):

    def test_returns_dict_of_lists(self):
        user1 = User.objects.create(
            username='foobar',
            email='foo@bar.baz'
        )
        user2 = User.objects.create(
            username='foobar2',
            email='foo2@bar.baz'
        )
        group1 = Group.objects.create(name='Foo')
        group2 = Group.objects.create(name='Bar')
        group3 = Group.objects.create(name='Baz')
        user1.groups.set([group1, group2])
        user2.groups.set([group2, group3])

        groups_m2m = prefetch_m2m(User.groups)

        self.assertEqual(
            list(groups_m2m.keys()),
            [user1.id, user2.id]
        )
        self.assertEqual(groups_m2m[user1.id], [group1, group2])
        self.assertEqual(groups_m2m[user2.id], [group2, group3])
