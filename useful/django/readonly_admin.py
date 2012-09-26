from django.contrib import admin
from django.core.exceptions import PermissionDenied
from django.utils.translation import ugettext_lazy as _


class SemiReadOnlyModelAdmin(admin.ModelAdmin):
    """
    Only hides the actions and adding/deleting controls.
    """
    actions = None

    def has_add_permission(self, request, obj=None):  # @UnusedVariable
        return False
    has_delete_permission = has_add_permission
#    has_change_permission = has_add_permission


class ReadOnlyModelAdmin(SemiReadOnlyModelAdmin):
    """
    Not only hides the actions and adding/deleting controls, but really
    forbids the model change. Only change_list browsing is allowed.

    Below are few examples of first items in the list_display the remove
    the detail link.
    """
    def save_model(self, request, obj, form, change):  # @UnusedVariable - MUST NOT CHANGE THE VAR NAME
        raise PermissionDenied

    def id_nolink(self, obj):
        return '</a><span style="font-weight: normal">%s</span><a>' % obj.id
    id_nolink.allow_tags = True
    id_nolink.short_description = "ID"

    def created_nolink(self, obj):
        return '</a><span style="font-weight: normal">%s</span><a>' \
            % obj.created.strftime('%Y-%m-%d %H:%M:%S')
    created_nolink.allow_tags = True
    created_nolink.short_description = _("Created")

    def entered_nolink(self, obj):
        return '</a><span style="font-weight: normal">%s</span><a>' \
            % obj.entered.strftime('%Y-%m-%d %H:%M:%S')
    entered_nolink.allow_tags = True
    entered_nolink.short_description = _("Entered")
