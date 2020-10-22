from django.http import HttpResponse
from django.shortcuts import render

from useful.django.urlpatterns import UrlPatterns
from useful.django.views import page

app_name = 'testapp'
urlpatterns = UrlPatterns()


@urlpatterns.url(r'^url-simple-view/$')
def simple_view(request):
    return HttpResponse('View works!')


@urlpatterns.url(r'^other-view/$')
def other_view(request):
    return HttpResponse('Other view works!')


@page('simple_template.html')
def template_view(request):
    return dict(
        foo='bar',
    )


@urlpatterns.url(r'^restricted/$', perms='auth.can_pass')
def restricted_view(request):
    return render(
        request,
        'restricted_template.html',
    )


@urlpatterns.url(r'^restricted2/$', perms='auth.other_perm')
def another_restricted_view(request):
    return render(
        request,
        'restricted_template.html',
    )
