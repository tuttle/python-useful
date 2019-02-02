from django.contrib import admin
from django.contrib.admin.models import ADDITION, CHANGE, DELETION, LogEntry
from django.contrib.contenttypes.models import ContentType
from django.template.defaultfilters import capfirst
from django.utils.encoding import force_text
from django.utils.safestring import mark_safe
from django.utils.text import get_text_list
from django.utils.translation import ugettext_lazy as _

# Django 1.5 swappable model support, backward compatible.
try:
    from django.contrib.auth import get_user_model
except ImportError:
    from django.contrib.auth.models import User as UserModel
else:
    UserModel = get_user_model()

from .readonly_admin import ReadOnlyModelAdmin


class UILogEntry(object):
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

    def construct_change_message(self, form):
        change_message = []
        if form.changed_data:
            lst = get_text_list(form.changed_data, _('and'))
            change_message.append(_('Changed %s.') % lst)

        change_message = u' '.join(change_message)
        return unicode(change_message or _('No fields changed.'))

    def do_log(self, object_, action_flag, message):
        LogEntry.objects.log_action(
            user_id=self.user.pk,
            content_type_id=ContentType.objects.get_for_model(object_).pk,
            object_id=object_.pk,
            object_repr=force_text(object_),
            action_flag=action_flag,
            change_message=unicode(message),
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


CHTYPES = {admin.models.ADDITION: 'addlink',
           admin.models.CHANGE: 'changelink',
           admin.models.DELETION: 'deletelink'}


class LogEntryAdmin(ReadOnlyModelAdmin):
    """
    This read only ModelAdmin can be presented to the staff users for
    reference.
    Example::

        from django.contrib import admin
        from django.contrib.admin.models import LogEntry
        from useful.django.logentry import LogEntryAdmin

        admin.site.register(LogEntry, LogEntryAdmin)
    """
    list_display = 'action_time_nolink', 'user', 'table', 'action', 'change_message'
    list_filter = (
        'user__is_superuser',
        ('content_type', admin.RelatedOnlyFieldListFilter),
    )
    date_hierarchy = 'action_time'

    def action_time_nolink(self, obj):
        return mark_safe(
            '</a><span style="font-weight: normal">%s</span><a>' % obj.action_time.strftime('%Y-%m-%d %H:%M:%S')
        )
    action_time_nolink.allow_tags = True
    action_time_nolink.short_description = _("Action time")
    action_time_nolink.admin_order_field = 'action_time'

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
            r = '<a href="%s">%s</a>' % (obj.get_admin_url(), r)
        return mark_safe(
            '<span class="%s">%s</span>' % (CHTYPES[obj.action_flag], r)
        )
    action.allow_tags = True
    action.short_description = _("Action, object")
    action.admin_order_field = 'object_repr'

    def queryset(self, request):
        qs = super(LogEntryAdmin, self).queryset(request)
        return qs.select_related('user', 'content_type')
