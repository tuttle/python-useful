from django.urls import include, path

from tests.testapp import views

urlpatterns = [
    path('testapp/', include('tests.testapp.views')),
    path(
        'testapp/simple/',
        views.template_view,
        name='template_view',
    ),
]
