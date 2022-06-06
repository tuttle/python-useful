from django.contrib import admin
from django.core.exceptions import PermissionDenied


class ReadOnlyModelAdmin(admin.ModelAdmin):
    """
    ModelAdmin class that prevents modifications through the admin.
    The changelist and the detail view work, but a 403 is returned
    if one actually tries to edit an object.

    Influenced by https://gist.github.com/aaugustin/1388243
    """
    actions = None

    list_display_links = None

    # We cannot call super().get_fields(request, obj) because that method calls
    # get_readonly_fields(request, obj), causing infinite recursion. Ditto for
    # super().get_form(request, obj). So we  assume the default ModelForm.
    def get_readonly_fields(self, request, obj=None):
        # noinspection PyProtectedMember
        return self.fields or [f.name for f in self.model._meta.fields]

    def has_add_permission(self, request, obj=None):
        return False
    has_delete_permission = has_add_permission

    # Allow viewing objects but not actually changing them.
    def has_change_permission(self, request, obj=None):
        if request.method in ('GET', 'HEAD'):
            return super(ReadOnlyModelAdmin, self).has_change_permission(request, obj)
        return False

    def save_model(self, request, obj, form, change):  # MUST NOT CHANGE THE VAR NAME
        raise PermissionDenied

    def save_related(self, request, form, formsets, change):
        raise PermissionDenied
