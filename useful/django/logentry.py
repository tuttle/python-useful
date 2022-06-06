from __future__ import unicode_literals

from django import VERSION
from django.contrib import admin
from django.contrib.admin.models import ADDITION, CHANGE, DELETION, LogEntry
from django.contrib.admin.utils import construct_change_message
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.forms import all_valid
from django.template.defaultfilters import capfirst
from django.utils.safestring import mark_safe
from django.utils.text import get_text_list

from .readonly_admin import ReadOnlyModelAdmin

# Get rid off warnings in Django 3
if VERSION[0] >= 2:
    from django.utils.encoding import force_str as force_text
    from django.utils.translation import gettext_lazy as _

    LogEntry.get_change_message.short_description = _("Changes in detail")
else:
    # @RemoveFromDjangoVersion2
    from django.utils.encoding import force_text
    from django.utils.translation import ugettext_lazy as _


UserModel = get_user_model()


class LogEntryAs(object):
    """
    This creates the LogEntry items for actions on objects.
    Similar to how ModelAdmin does it. This class is more universal to embrace various scenarios.

    Replaces the old-fashioned UILogEntry below.
    """
    def __init__(self, user, **common_message):
        """
        Expects the actioning user as argument.
        Additional parameters will be saved each time to JSON message each time the action occurs.
        """
        self.user = user
        self.common_message_list = [common_message]

    def log_addition(self, object_, message=None):
        """
        Adds a LogEntry recording that the object_ was added.
        The message is either a dict which is appended to the resulting message list.
        Otherwise, it is expected to be an iterable and the resulting message list is extended with it.
        """
        self.log_action(object_, ADDITION, message)

    def log_change(self, object_, message=None):
        """
        Adds a LogEntry recording that the object_ was changed.
        The message is either a dict which is appended to the resulting message list.
        Otherwise, it is expected to be an iterable and the resulting message list is extended with it.
        """
        self.log_action(object_, CHANGE, message)

    def log_deletion(self, object_, message=None):
        """
        Adds a LogEntry recording that the object_ was deleted.
        NOTE that this method must be called before the deletion.
        The message is either a dict which is appended to the resulting message list.
        Otherwise, it is expected to be an iterable and the resulting message list is extended with it.
        """
        self.log_action(object_, DELETION, message)

    def log_action(self, object_, action_flag, message):
        change_message = []
        if self.common_message_list:
            change_message.extend(self.common_message_list)
        if message:
            if isinstance(message, dict):
                change_message.append([message])
            else:
                change_message.extend(message)

        LogEntry.objects.log_action(
            user_id=self.user.pk,
            content_type_id=ContentType.objects.get_for_model(object_, for_concrete_model=False).pk,
            object_id=object_.pk,
            object_repr=force_text(object_),
            action_flag=action_flag,
            change_message=change_message,
        )

    def log_form_addition_or_change(self, form, was_adding, formsets=None):
        """
        Shortcut for logging the addition/deletion made via form. Resembles ModelAdmin too.
        If there are accompanyed formset to the main action, their change could be logged too.
        """
        if not form.is_valid():
            raise ValidationError("Form invalid.")
        if formsets and not all_valid(formsets):
            raise ValidationError("Some of the formsets not valid.")

        message_list = construct_change_message(form, formsets, was_adding)

        if was_adding:
            self.log_addition(form.instance, message_list)
        else:
            self.log_change(form.instance, message_list)


class UILogEntry(object):
    """
    Deprecated, you should migrate to LogEntryAs above.
    """
    def __init__(self, user=None):
        """
        This is similar to how ModelAdmin logs events. Expects the user
        doing the change as argument. When not given, 'admin' is used.
        """
        if user is None:
            user = UserModel.objects.only('id').get(username='admin')
        self.user = user

    def log_addition(self, object_, message='UI'):
        """
        Adds a LogEntry recording that the object_ was added.
        The change detail message defaults to 'UI' to denote the change
        did not originate from admin interface.
        """
        self.do_log(object_, ADDITION, message)

    def log_change(self, object_, message='UI', form=None):
        """
        Adds a LogEntry recording that the object_ was changed.
        If clean form given, the list of changed fields is added to message.
        The change detail message defaults to 'UI' to denote the change
        did not originate from admin interface.
        """
        if form is not None:
            if message:
                message += ' '
            message += self.construct_change_message(form)

        self.do_log(object_, CHANGE, message)

    def log_deletion(self, object_, message='UI'):
        """
        Adds a LogEntry recording that the object_ was deleted.
        The change detail message defaults to 'UI' to denote the change
        did not originate from admin interface.
        """
        self.do_log(object_, DELETION, message)

    @staticmethod
    def construct_change_message(form):
        change_message = []
        if form.changed_data:
            lst = get_text_list(form.changed_data, _('and'))
            change_message.append(_('Changed %s.') % lst)

        change_message = ' '.join(change_message)
        return force_text(change_message or _('No fields changed.'))

    def do_log(self, object_, action_flag, message):
        LogEntry.objects.log_action(
            user_id=self.user.pk,
            content_type_id=ContentType.objects.get_for_model(object_).pk,
            object_id=object_.pk,
            object_repr=force_text(object_),
            action_flag=action_flag,
            change_message=force_text(message),
        )

    def save_form_instance_and_log(self, form):
        """
        Shortcut to saving a clean ModelForm instance + logging
        the addition or deletion.
        """
        existed = form.instance.id

        instance = form.save()

        if existed:
            self.log_change(form.instance, form=form)
        else:
            self.log_addition(form.instance)

        return instance


class LogEntryAdmin(ReadOnlyModelAdmin):
    """
    This read only ModelAdmin can be presented to the staff users for reference.

    Example::

        from django.contrib import admin
        from django.contrib.admin.models import LogEntry
        from useful.django.logentry import LogEntryAdmin

        admin.site.register(LogEntry, LogEntryAdmin)
    """
    list_display = (
        'action_time',
        'user',
        'table',
        'action',
        'get_change_message',
    )
    list_filter = (
        'action_flag',
        'user__is_superuser',
        ('content_type', admin.RelatedOnlyFieldListFilter),
    )
    list_select_related = (
        'user',
        'content_type',
    )
    search_fields = (
        'user__email',
        'object_repr',
        'change_message',
    )
    date_hierarchy = 'action_time'
    list_per_page = 500
    list_max_show_all = 10000

    def table(self, obj):
        if obj.content_type_id:
            cls = obj.content_type.model_class()
            return capfirst(cls._meta.verbose_name_plural) if cls else obj.content_type
        return ''
    table.short_description = _("Table")
    table.admin_order_field = 'content_type'

    def action(self, obj):
        r = obj.object_repr
        if not obj.is_deletion() and obj.get_admin_url():
            r = '<a href="%s">%s</a>' % (
                obj.get_admin_url(),
                r,
            )
        return mark_safe(
            '<span class="%s">%s</span>' % (
                self.link_classes[obj.action_flag],
                r,
            )
        )
    action.short_description = _("Action, object")
    action.admin_order_field = 'object_repr'

    link_classes = {
        admin.models.ADDITION: 'addlink',
        admin.models.CHANGE: 'changelink',
        admin.models.DELETION: 'deletelink',
    }
