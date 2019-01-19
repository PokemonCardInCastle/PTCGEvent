from django.conf import settings
from django.conf.urls import include, url
from django.contrib import admin
from accounts import views
from django.views.generic.base import RedirectView

from wagtail.admin import urls as wagtailadmin_urls
from wagtail.core import urls as wagtail_urls
from wagtail.documents import urls as wagtaildocs_urls

from search import views as search_views

app_name = 'accounts'

urlpatterns = [
    url(r'^$', RedirectView.as_view(pattern_name='sign_in', permanent=False)),
    url(r'^auth/', include('allauth.urls')),
    url(r'^signin/?(?P<next>.*)?$', views.signin_view, name="signin"),
    url(r'^login/?(?P<next>.*)?$', views.signin_view, name="login"),
    url(r'^signup/?(?P<next>.*)?$', views.signup_view, name="signup"),
    url(r'^signout/?(?P<next>.*)?$', views.signout_view, name="signout"),
    url(r'^logout/?(?P<next>.*)?$', views.signout_view, name="logout"),
]