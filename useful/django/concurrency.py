import hashlib

from django import forms
from django.utils.translation import ugettext_lazy as _
from django.utils.safestring import mark_safe
from django.utils.encoding import smart_text, force_text
from django.utils.crypto import salted_hmac, constant_time_compare
from django.contrib.auth.forms import UserChangeForm


CONCURRENCY_EDIT_MESSAGE = _(
    "<br><b>WARNING:</b> Your changes are almost LOST now and can't be saved.<br><em>But you still can copy the values "
    "out manually now.</em><br>Then you can <a href=''>RELOAD</a> and edit again."
)


def _clean_object_version(slf):
    form_pk, form_hash = _validate_object_version(slf.cleaned_data)

    # form_pk ---  &&  pk ---    : ok, unsaved object
    # form_pk ---  &&  pk val    : fail as object_version is missing
    # form_pk val  &&  pk ---    : warn about removal
    # form_pk val  &&  pk val    : compare (validation error if mismatch)

    pk = slf.instance.pk

    if form_pk is None:
        if pk is None:
            # newly created object, nothing to check
            return
        slf.concurrency_problem = _("The form is missing the object version check field.")

    elif pk is None:
        slf.concurrency_problem = _("In the mean time, someone <b>removed</b> the item from "
                                    "the database.<br><b>Submit the form again</b> in case "
                                    "you are sure to create it.")
        slf.data = slf.data.copy()    # make the data dict mutable first
        slf.data['object_version'] = ''

    elif form_pk != force_text(pk):
        raise RuntimeError(_("Found not matching primary key in object_version field."))

    if not slf.concurrency_problem:
        db_obj = slf._meta.model.objects.get(pk=pk)
        db_hash = _gen_object_hash(db_obj)
        if form_hash != db_hash:
            slf.concurrency_problem = \
                _("In the mean time, someone <b>changed</b> this item in the database.") \
                + ' ' + force_text(slf._CONCURRENCY_EDIT_MESSAGE)

    if slf.concurrency_problem:
        errors = slf._errors.setdefault(forms.forms.NON_FIELD_ERRORS, forms.utils.ErrorList())
        errors.append(mark_safe(slf.concurrency_problem))


class ConcurrencyProtectionModelForm(forms.ModelForm):
    """
    ModelForm based on this protects the object from concurrent user updates.
    When the form is displayed for edition, the hash of its values is created.
    During cleaning, the hash from the current object in database is created
    again and compared. The mismatch reveals that the object has been changed
    in the meantime -- then the validation error is raised.

    Example::

        class MyModelForm(ConcurrencyProtectionModelForm):
            class Meta:
                model = MyModel

    Use this also in your ModelAdmin descendants::

        class QuestionSetAdmin(admin.ModelAdmin):
            form = ConcurrencyProtectionModelForm

    This way concurrent updates will be watched from both your UI and django.contrib.admin.
    """
    object_version = forms.CharField(required=False, widget=forms.HiddenInput)

    def __init__(self, *args, **kwargs):
        super(ConcurrencyProtectionModelForm, self). __init__(*args, **kwargs)
        self.concurrency_problem = None
        self.fields['object_version'].initial = _gen_object_version(self.instance)

    clean_object_version = _clean_object_version

    _CONCURRENCY_EDIT_MESSAGE = CONCURRENCY_EDIT_MESSAGE


# DEPRECATED -- it does not work in Django 1.6.
#               Use 'form = ConcurrencyProtectionModelForm' instead.
#
# class ConcurrencyProtectionModelAdmin(admin.ModelAdmin):
#     """
#
#     You may want to avoid the situations when the admin user overwrites
#     the changes of anybody else. In that case, inherit your model admins from
#     this class instead of the usual admin.ModelAdmin.
#     The admin form will be monkey patched with the protection field.
#     """
#     def get_form(self, request, obj=None, **kwargs):
#         form = super(ConcurrencyProtectionModelAdmin, self).get_form(request, obj, **kwargs)
#
#         if obj is not None:
#             form.concurrency_problem = None
#             field = forms.CharField(initial=_gen_object_version(obj), required=False)
#             form.base_fields['object_version'] = field
#             form.clean_object_version = _clean_object_version
#         return form


class ConcurrencyProtectionUserChangeForm(UserChangeForm):
    """
    UserAdmin can be re-registered like this::

        from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
        from useful.django.concurrency import ConcurrencyProtectionUserChangeForm

        class UserAdmin(DjangoUserAdmin):
            form = ConcurrencyProtectionUserChangeForm

            fieldsets = (
                ...,
                (None, {'fields': ('object_version',)}),
            )

        admin.site.unregister(User)
        admin.site.register(User, UserAdmin)
    """
    object_version = forms.CharField(required=False, widget=forms.HiddenInput)

    def __init__(self, *args, **kwargs):
        super(ConcurrencyProtectionUserChangeForm, self). __init__(*args, **kwargs)
        self.concurrency_problem = None
        self.fields['object_version'].initial = _gen_object_version(self.instance)

    clean_object_version = _clean_object_version

    _CONCURRENCY_EDIT_MESSAGE = CONCURRENCY_EDIT_MESSAGE


def _gen_hmac(pk, hash_):
    pk = smart_text(pk).encode('UTF-8')
    hash_ = smart_text(hash_).encode('UTF-8')
    return salted_hmac('concurrency prot', '%s %s' % (pk, hash_)).hexdigest()


def _gen_object_hash(obj):
    def get_obj_data():
        for k, v in sorted(forms.models.model_to_dict(obj).items()):
            yield u'%s=%s' % (smart_text(k), smart_text(v))

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

    hash_ = _gen_object_hash(obj)
    return u'%s-%s-%s' % (obj.pk, hash_, _gen_hmac(obj.pk, hash_))


def _validate_object_version(datadict):
    form_pk, form_hash = None, None
    form_version = datadict.get('object_version', '')
    if form_version:
        try:
            form_pk, form_hash, form_hmac = form_version.split('-', 2)
            if not form_pk or not form_hash or not form_hmac:
                raise ValueError
        except ValueError:
            raise forms.ValidationError("Bad object_version format.")

        if not constant_time_compare(form_hmac, _gen_hmac(form_pk, form_hash)):
            raise forms.ValidationError(_("Version protection tampered."))

    return form_pk, form_hash
