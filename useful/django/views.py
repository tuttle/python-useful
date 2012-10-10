import os
import time
import functools

from django.conf import settings
from django.core.paginator import Paginator, EmptyPage, InvalidPage
from django.shortcuts import render_to_response
from django.http import HttpResponse, HttpResponseBadRequest
from django.template import RequestContext

from .crypto import SecretTokenGenerator


def page(template=None, **decorator_args):
    """
    Decorator to make template rendered by Django views dead simple.
    Takes the template path as first argument. See the code comments.
    Example::

        @page('payments/payments_info.html')
        def payment_info(request):
            return { ... context dict ... }
    """
    def page_decorator_wrapper(fn):
        @functools.wraps(fn)
        def page_decorator_inner_wrapper(request, *args, **kw):
            # Take the basic context dictionary from the optional decorator args.
            data = decorator_args.copy()

            # Call the original view.
            d = fn(request, *args, **kw)

            # Return now if it returned some kind of HTTP response itself, no job.
            if isinstance(d, HttpResponse):
                return d

            if d:
                data.update(d)

            # The view can override the template to use.
            template_name = data.get('template',  template)

            # By adding the debug_template parameter we switch to possible
            # debugging template:
            # payments/payments_info.html -> payments/payments_info_debug.html
            if settings.DEBUG and request.GET.get('debug_template'):
                stn = os.path.splitext(template_name)
                template_name = stn[0] + '_debug' + stn[1]

            # The view or the decorator call can override the context
            # instance. Otherwise, use the usual RequestContext.
            context_instance = data.get('context') or RequestContext(request)

            # Render the template.
            response = render_to_response(template_name, data, context_instance)
            return response

        return page_decorator_inner_wrapper
    return page_decorator_wrapper


class JsonResponse(HttpResponse):
    """
    Returns JSON encoded dict as HTTP response.
    """
    def __init__(self, response_dict, **kwargs):
        import json

        kwargs['content'] = json.dumps(response_dict, ensure_ascii=False)
        kwargs['mimetype'] = 'application/json'
        super(JsonResponse, self).__init__(**kwargs)


def protected_redirect(request):
    """
    Redirects to the URL in GET parameter u, but only if protection check passes.
    The 'u' GET parameter should be the target URL. The 't' should be the
    token created by SecretTokenGenerator().check_token(u).
    When the token check passes, the refreshing style redirection HTML page
    is returned. This is useful in hiding the true URL from where the link
    was clicked: The target site will get the redirector URL as referrer.
    """
    u, t = request.GET.get('u'), request.GET.get('t')
    if u and t and SecretTokenGenerator().check_token(u, t):
        return HttpResponse('''<html><head>
<meta http-equiv="refresh" content="1;url=http://%s">
</head>
<body>
    <a href="http://%s">Redirecting to %s</a>
    <script>window.location.replace("http://%s");
    </script>
</body></html>''' % (u, u, u, u))
    else:
        return HttpResponseBadRequest("Bad parameters or protection fault.")


def serve_with_Expires(request, path, cache_timeout=365*24*60*60):
    """
    This view can be used in the development server to add the Expires
    header on the static files protected by the modtime change detection
    in the freshstatic template tag (see there).

    The browsers will stop asking for the file again and again during the
    normal browsing.

    Example in your urls.py::

        urlpatterns += static.static(settings.STATIC_URL, serve_with_Expires)

    By adding a cache_timeout parameter to the above call with the number
    of seconds you will change the deafult expiration of 1 year.
    """
    from django.utils.http import http_date
    from django.contrib.staticfiles.views import serve

    response = serve(request, path)

    if not response.has_header('Expires'):
        response['Expires'] = http_date(time.time() + cache_timeout)

    return response


def paginate(request, objects, per_page=20):
    """
    This is so common Django pagination code...
    Can be used like this in the template::

        {% load i18n useful %}
        <div class="pager">
            <ul>
                {% if objs.has_previous %}
                <li class="first"><a href="?{% querydict_set request.GET 'page' 1 %}" title="{% trans "First page" %}">&lt;&lt;</a></li>
                <li><a href="?{% querydict_set request.GET 'page' objs.previous_page_number %}" title="{% trans "Previous page" %}">&lt;</a></li>
                {% endif %}

                {% for page in objs.paginator.page_range %}
                <li {% ifequal objs.number page %}class="active"{% endifequal %}>
                    <a href="?{% querydict_set request.GET 'page' page %}" title="{% trans "Jump to page">{{ page }}</a>
                </li>
                {% endfor %}

                <span class="current">{% blocktrans with objs.number as num and objs.paginator.num_pages as total %}Page {{ num }} of {{ total }}{% endblocktrans %}</span>

                {% if objs.has_next %}
                <li><a href="?{% querydict_set request.GET 'page' objs.next_page_number %}" title="{% trans "Next page" %}">&gt;</a></li>
                <li class="last"><a href="?{% querydict_set request.GET 'page' objs.paginator.num_pages %}" title="{% trans "Last page" %}">&gt;&gt;</a></li>
                {% endif %}
            </ul>
        </div>
    """
    paginator = Paginator(objects, per_page)

    try:
        page = int(request.GET.get('page', '1'))
    except ValueError:
        page = 1

    try:
        objects = paginator.page(page)
    except (EmptyPage, InvalidPage):
        objects = paginator.page(paginator.num_pages)

    return objects
