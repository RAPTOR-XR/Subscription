from django.urls import re_path
from . import views
from .views import Register, Login

urlpatterns = [
    re_path(r'^$', views.index, name='index'),
    re_path(r'^login/$', views.signin, name='login'),
    re_path(r'^home/$', views.index, name='home'),
    re_path(r'^check-mail-ajax/$', views.check_mail_ajax, name='check_mail_ajax'),
    re_path(r'^register/$', Register.as_view(), name='register'),
    re_path(r'login-req', Login.as_view(), name='login_ajax'),

    re_path(r'^subscription/', views.subscription, name='subscription'),
    re_path(r'^subscribe/', views.subscribe, name='subscribe'),
    re_path(r'^subscribed/', views.subscribed, name='subscribed'),
    re_path(r'^sub/', views.end_sub, name='sub'),

    re_path(r'^payment/$', views.call_back_url, name='payment'),
]