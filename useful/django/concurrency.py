import hashlib

from django import forms
from django.utils.translation import ugettext_lazy as _
from django.utils.safestring import mark_safe
from django.utils.encoding import smart_unicode
from django.utils.crypto import salted_hmac, constant_time_compare
from django.contrib import admin
from django.contrib.auth.forms import UserChangeForm

# form_pk ---   pk ---    : no problem
# form_pk ---   pk val    : fail as an obj is already in db
# form_pk val   pk ---    : warn about removal
# form_pk val   pk val    : compare (bogus is mismatch)

def _clean_object_version(slf):
    form_pk, form_hash = _validate_object_version(slf.cleaned_data)

    pk = slf.instance.pk
    if form_pk is None:
        if pk is None:
            return                    # newly created object, nothing to check
        else:
            slf.concurrency_problem = _("In the mean time, someone "
                "<b>created</b> the item in the database.") + ' ' + unicode(RELOAD_MSG)
    else:
        if pk is None:
            slf.concurrency_problem = _("Please note: In the mean time, "
                "someone <b>removed</b> the item from the database.<br /><b>"
                "Submit the form again</b> in case you are sure to create it.")
            slf.data = slf.data.copy()    # make the data dict mutable first
            slf.data['object_version'] = ''

        elif form_pk != unicode(pk):
            raise RuntimeError("Bogus primary key situation.")

    if not slf.concurrency_problem:
        db_obj = slf._meta.model.objects.get(pk=pk)
        db_hash = _gen_object_hash(db_obj)
        if form_hash != db_hash:
            slf.concurrency_problem = _("In the mean time, someone "
                "<b>changed</b> this item in the database.") + ' ' + unicode(RELOAD_MSG)

#            try:
#                modified = db_obj.modified.strftime('%Y-%m-%d %H:%M:%S')
#                slf.concurrency_problem += "<br />" \
#                                 + _("Database item changed at %s.") % modified
#            except AttributeError:
#                pass

    if slf.concurrency_problem:
        errors = slf._errors.setdefault(forms.forms.NON_FIELD_ERRORS,
                                        forms.util.ErrorList())
        errors.append(mark_safe(slf.concurrency_problem))


RELOAD_MSG = _("Please <a href=''>RELOAD</a> and edit again.<br />"
               "<b>WARNING:</b> Your changes are almost LOST now and can't be"
               " saved.<br />But you still have a chance to copy them out.")


class ConcurrencyProtectionModelForm(forms.ModelForm):
    """
    ModelForm based on this protects the object from concurrent user updates.
    When the form is displayed for edition, the hash of its values is created.
    During cleaning, the hash from the current object in database is created
    again and compared. The mismatch reveals that the object has been changed
    in the meantime resulting in the validation error.
    """
    object_version = forms.CharField(required=False, widget=forms.HiddenInput)

    def __init__(self, *args, **kwargs):
        super(ConcurrencyProtectionModelForm, self). __init__(*args, **kwargs)
        self.concurrency_problem = None
        self.fields['object_version'].initial = _gen_object_version(self.instance)

    clean_object_version = _clean_object_version


class ConcurrencyProtectionModelAdmin(admin.ModelAdmin):
    """
    You may want to avoid the situations when the admin user overwrites
    the changes of anybody else. In that case, inherit your model admins from
    this class instead of the usual admin.ModelAdmin.
    The admin form will be monkey patched with the protection field.
    """
    def get_form(self, request, obj=None, **kwargs):
        form = super(ConcurrencyProtectionModelAdmin, self).get_form(request, obj, **kwargs)

        if obj is not None:
            form.concurrency_problem = None
            field = forms.CharField(initial=_gen_object_version(obj),
                                    required=False)
            form.base_fields['object_version'] = field
            form.clean_object_version = _clean_object_version

        return form


class ConcurrencyProtectionUserChangeForm(UserChangeForm):
    """
     UserAdmin can be re-registered like this::

        from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
        from useful.django.concurrency import ConcurrencyProtectionUserChangeForm

        class UserAdmin(DjangoUserAdmin):
            form = ConcurrencyProtectionUserChangeForm

        admin.site.unregister(User)
        admin.site.register(User, UserAdmin)
    """
    object_version = forms.CharField(required=False, widget=forms.HiddenInput)

    def __init__(self, *args, **kwargs):
        super(ConcurrencyProtectionUserChangeForm, self). __init__(*args, **kwargs)
        self.concurrency_problem = None
        self.fields['object_version'].initial = _gen_object_version(self.instance)

    clean_object_version = _clean_object_version


def _gen_hmac(pk, hash):
    pk = smart_unicode(pk).encode('UTF-8')
    hash = smart_unicode(hash).encode('UTF-8')
    return salted_hmac('concurrency prot', '%s %s' % (pk, hash)).hexdigest()


def _gen_object_hash(obj):
    def get_obj_data():
        for k, v in sorted(forms.models.model_to_dict(obj).items()):
            yield u'%s=%s' % (smart_unicode(k), smart_unicode(v))

    data = u' '.join(get_obj_data()).encode('UTF-8')
    return hashlib.sha256(data).hexdigest()


def _gen_object_version(obj):
    """
    Get protected hash of object values.
    """
    # Another approach could be:
    # return obj.modified.strftime('%s.%f')
    if obj.pk is None:
        return ''

    hash = _gen_object_hash(obj)
    return u'%s-%s-%s' % (obj.pk, hash, _gen_hmac(obj.pk, hash))


def _validate_object_version(datadict):
    form_pk, form_hash = None, None
    form_version = datadict.get('object_version', '')
    if form_version:
        try:
            form_pk, form_hash, form_hmac = form_version.split('-', 2)
            if not form_pk or not form_hash or not form_hmac:
                raise ValueError
        except ValueError:
            raise forms.ValidationError("Bad version format.")

        if not constant_time_compare(form_hmac, _gen_hmac(form_pk, form_hash)):
            raise forms.ValidationError(_("Version protection tampered."))

    return form_pk, form_hash
