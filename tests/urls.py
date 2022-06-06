
from django.urls import include
from django.urls import path

from tests.testapp import views


urlpatterns = [
    path(r'testapp/', include('tests.testapp.views')),
    path(
        r'testapp/simple/',
        views.template_view,
        name='template_view'
    )
]
