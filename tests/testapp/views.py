
from django.http import HttpResponse

from useful.django.urlpatterns import UrlPatterns
from useful.django.views import page


app_name = 'testapp'
urlpatterns = UrlPatterns()


@urlpatterns.url(r'^url-simple-view/$')
def simple_view(request):
    return HttpResponse('View works!')


@page('simple_template.html')
def template_view(request):
    return dict(
        foo='bar',
    )
