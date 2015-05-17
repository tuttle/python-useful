import re
from functools import wraps
try:
    from urllib.parse import urlparse
except ImportError:     # Python 2
    from urlparse import urlparse

from django.conf import settings
from django.conf.urls import url
from django.contrib.auth import REDIRECT_FIELD_NAME
from django.core.exceptions import PermissionDenied
from django.shortcuts import resolve_url
from django.utils.decorators import available_attrs
from django.utils.encoding import force_str


class UrlPatterns(list):
    """
    Offers to create the standard urlpatterns in views.py instead of in urls.py and supports DRY
    by allowing to not reference the view name and not define the URL name (it can be
    automatically set by the name of the view func). The URL patterns are then closer to the views.

    IMPORTANT::

        As it appends the view to the URLConf, this is the last (outermost) decorator
        able to change the view behavior!

    Example::

        ### views.py (your exams/urls.py is no more)

        from useful.django.urlpatterns import UrlPatterns

        urlpatterns = UrlPatterns()

        @urlpatterns.url(r'^list/$')
        def exams_list(request):
            ...

    In project *root* urls.py::

        url(r'^exams/', include('myproject.apps.exams.views')),

    Now /exams/list/ url lives under the name exams_list as expected::

        {% url 'exams_list' %}

    Permissions:

    Also this class supports unification in permission definition and reference.

    Until now, every time you wanted to test whether the user can see the link to the view,
    you had to test for the same set of conditions the view was decorated with.

    That is not very DRY.

    `can_url' function and `can_url_processor' offer to define even the complex set of permissions
    only once.  All references only use the view spec usually used in the {% url %} tag.

    Example::

        ### models.py
        ...
        class Meta:
            verbose_name = _("Exam")
            verbose_name_plural = _("Exams")
            permissions = (
                ('see_listing', "Can see the listing of exams"),
            )

        ### views.py

        @urlpatterns.url(r'^list/$', perms='exams.see_listing')
        def exams_list(request):
            ...

    Now in template, to *test whether the user can access the view*::

        ### settings.py

        TEMPLATE_CONTEXT_PROCESSORS += (
            ...
            'useful.django.can_url.can_url_processor',
        )

        ### in some template.html

        {% if can_url.exams_list %}
            <a href="{% url 'exams_list' %}">...</a>
        {% endif %}

    Alternatively as dict: {% if 'namespace:exams_list' in can_url %} ...

    Allowed forms of perm definition in the decorator::

        perms='PERM1'                     # the permission must be present
        perms=('PERM1', 'PERM2')          # all these perms must be present
        perms='PERM1 | PERM2'             # user needs PERM1 or PERM2
        perms=('PERM1', 'PERM2 | PERM3')  # PERM1 and (PERM2 or PERM3)

    Each of PERM1, PERM2, PERM3 can be:

        'is_active'
        'is_authenticated'
        'is_staff'
        'is_superuser'
            - these are tests for appropriate attribute of the user

        'app_name.perm_name'
            - if the dot ('.') is present, user.has_perm() is called to test

        Otherwise user.has_module_perms() is called (that usually tests whether
        the user has any permission for the given app).

    Consider these permissions::

        ### models.py
        ...
        class Meta:
            permissions = (
                ('see_own_exams',  "Can SEE OWN submitted exams only"),
                ('see_all_exams',  "Can SEE ALL submitted exams"),
            )

    Each PERM can also be followed by its alias in parentheses::

        ### views.py

        @urlpatterns.url(r'^list/$', perms='exams.see_own_exams | exams.see_all_exams (can_all)')
        def exams_list(request, can_all=False):
            ...
            exams = Exam.objects.all()

            if can_all and request.GET.get('showall'):
                messages.info(request, _("The list of exams of all users."))
            else:
                exams = exams.filter(user=request.user)
                messages.info(request, _("The list of your past exams."))
            ...
            context['can_all'] = can_all  # can be useful in rendered template

    It is required for the view to accept an optional argument can_all that
    is True only when possessing the exams.see_all_exams and can be helpful
    in further DRYing the view behavior.

    It's also easy to indirectly test for permission in Python like you do in template::

        from useful.django.can_url import can_url

        return HttpResponseRedirect(reverse('exams_list') if can_url(request.user, 'exams_list')
                                    else '/')

    """
    # Note: Python 3 will allow all Unicode letters and digits in its identifiers.
    PERM_RE = r'\s*([a-zA-Z_][\w.]*)\s*(\(\s*([a-zA-Z_]\w*)\s*\))?\s*'

    def __init__(self, login_url=None, raise_exception=False, redirect_field_name=None):
        self.login_url = login_url
        self.raise_exception = raise_exception
        self.redirect_field_name = redirect_field_name or REDIRECT_FIELD_NAME

    def url(self, regex, kwargs=None, name=(), perms=None):
        def decorator(view_func):
            if perms is None:
                _wrapped = view_func
            else:
                compiled_anded_perms = self.compile_perms(perms)

                def __can_url(user):
                    return self._can_url(compiled_anded_perms, user)

                _wrapped = self.user_passes_test(__can_url)(view_func)
                _wrapped.can_url_func = __can_url
                _wrapped.can_url_perms = perms
                _wrapped.can_url_perms_compiled = compiled_anded_perms

            # Assigning different name to avoid changing the nonlocal variable.
            url_name = view_func.func_name if name is () else name
            self.append(url(regex, _wrapped, kwargs=kwargs, name=url_name))

            return _wrapped

        return decorator

    def compile_perms(self, perms):
        """
        Accepts the permission definition, returns list of AND-ed tuples.
        Each tuple contains OR-ed pairs (single-perm, alias-value).
        Alias-value is either text from parentheses or True.
        """
        if not isinstance(perms, (list, tuple)):
            perms = (perms,)

        def comp(ored_perms):
            for permdef in ored_perms.split('|'):
                m = re.match(self.PERM_RE, permdef)
                if not m:
                    raise RuntimeError("Cannot parse perm definition: %r" % permdef)
                perm, unused, alias = m.groups()
                yield perm, alias or True

        return [tuple(comp(ored_perms)) for ored_perms in perms]

    def user_passes_test(self, test_func):
        """
        Decorator based on django.contrib.auth.decorators.user_passes_test.
        Extended with passing the resolved aliased permissions to the view.
        """
        def decorator(view_func):
            @wraps(view_func, assigned=available_attrs(view_func))
            def _wrapped_view(request, *args, **kwargs):
                perm_aliases = test_func(request.user)
                if perm_aliases:
                    perm_aliases.discard(True)
                    for alias in perm_aliases:
                        assert alias not in kwargs
                        kwargs[alias] = True
                    return view_func(request, *args, **kwargs)

                # THE FOLLOWING code behaves the same as original:

                path = request.build_absolute_uri()
                # urlparse chokes on lazy objects in Python 3, force to str
                resolved_login_url = force_str(resolve_url(self.login_url or settings.LOGIN_URL))
                # If the login url is the same scheme and net location then just
                # use the path as the "next" url.
                login_scheme, login_netloc = urlparse(resolved_login_url)[:2]
                current_scheme, current_netloc = urlparse(path)[:2]
                if ((not login_scheme or login_scheme == current_scheme) and
                   (not login_netloc or login_netloc == current_netloc)):
                    path = request.get_full_path()
                from django.contrib.auth.views import redirect_to_login
                return redirect_to_login(path, resolved_login_url,
                                         self.redirect_field_name)
            return _wrapped_view
        return decorator

    def _can_url(self, compiled_anded_perms, user):
        res = set()
        for ored_perms in compiled_anded_perms:
            res2 = set(alias for perm, alias in ored_perms if self.test_perm(perm, user))
            if not res2:
                if self.raise_exception:
                    raise PermissionDenied
                return set()
            res |= res2
        return res

    def test_perm(self, perm, user):
        if perm == 'is_active':
            return user.is_active
        if perm == 'is_authenticated':
            return user.is_authenticated()
        if perm == 'is_staff':
            return user.is_staff
        if perm == 'is_superuser':
            return user.is_superuser

        # From now on, active && superuser users have all perms.

        if '.' in perm:
            return user.has_perm(perm)

        return user.has_module_perms(perm)
