from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

try:
    from django.utils.deprecation import MiddlewareMixin
except ImportError:  # Django < 1.10
    MiddlewareMixin = object


class SetRemoteAddrMiddleware(MiddlewareMixin):
    """
    Request middleware that sets REMOTE_ADDR based on request.META variable
    pointed by settings.REAL_IP_META_VARIABLE_NAME.

    This is intentionally a required setting, although if it is None,
    the feature is disabled. That's useful for local development.

    In production use, for example if nginx is your reverse proxy, you can
    configure it like this::

        proxy_set_header   X-Real-IP        $remote_addr;

    and if you set Django like this::

        REAL_IP_META_VARIABLE_NAME = 'HTTP_X_REAL_IP'

    then will get the real remote IP address to REMOTE_ADDR.
    """
    def process_request(self, request):
        try:
            real_ip_varname = settings.REAL_IP_META_VARIABLE_NAME
        except AttributeError:
            raise ImproperlyConfigured(
                "%s: Missing the required setting REAL_IP_META_VARIABLE_NAME." % self.__class__.__name__
            )

        if real_ip_varname is not None:
            request.META['REMOTE_ADDR'] = request.META[real_ip_varname]
