from django import VERSION
from django.contrib import admin
from django.core.exceptions import PermissionDenied
from django.utils.safestring import mark_safe

# Get rid off warnings in Django 3
if VERSION[0] >= 2:
    from django.utils.translation import gettext_lazy as _
else:
    # @RemoveFromDjangoVersion2
    from django.utils.translation import ugettext_lazy as _


class SemiReadOnlyModelAdmin(admin.ModelAdmin):
    """
    Only hides the actions and adding/deleting controls.
    """
    actions = None

    def has_add_permission(self, request, obj=None):
        return False
    has_delete_permission = has_add_permission
#    has_change_permission = has_add_permission


class ReadOnlyModelAdmin(SemiReadOnlyModelAdmin):
    """
    Not only hides the actions and adding/deleting controls, but really
    forbids the model change. Only change_list browsing is allowed.

    Below are few examples of first items in the list_display that remove
    the detail link.
    """
    def save_model(self, request, obj, form, change):  # MUST NOT CHANGE THE VAR NAME
        raise PermissionDenied

    def id_nolink(self, obj):
        return mark_safe(
            '</a><span style="font-weight: normal">%s</span><a>' % obj.id
        )
    id_nolink.short_description = "ID"

    def created_nolink(self, obj):
        return mark_safe(
            '</a><span style="font-weight: normal">%s</span><a>' % (
                obj.created.strftime('%Y-%m-%d %H:%M:%S'),
            )
        )
    created_nolink.short_description = _("Created")

    def entered_nolink(self, obj):
        return mark_safe(
            '</a><span style="font-weight: normal">%s</span><a>' % (
                obj.entered.strftime('%Y-%m-%d %H:%M:%S'),
            )
        )
    entered_nolink.short_description = _("Entered")
