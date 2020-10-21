
from django.conf.urls import include
from django.conf.urls import url

from tests.testapp import views


urlpatterns = [
    url(r'testapp/', include('tests.testapp.views')),
    url(
        r'testapp/simple/',
        views.template_view,
        name='template_view'
    )
]
