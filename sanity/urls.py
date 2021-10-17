from django.conf.urls import url

from . import views
from . import library
from . import twitter

urlpatterns = [
    # ex: /polls/
    url(r'^$', views.index, name='index'),
    url(r'^login/$', views.login, name='login'),
    url(r'^logout/$', views.logout, name='logout'),
    url(r'^in_library/$', library.in_library, name='in_library'),
    url(r'^toggle_library/$', library.toggle_library, name='toggle_library'),
    url(r'^twitter/$', twitter.twitter, name='twitter'),

    # # ex: /polls/5/
    # url(r'^(?P<question_id>[0-9]+)/$', views.detail, name='detail'),
    # # ex: /polls/5/results/
    # url(r'^(?P<question_id>[0-9]+)/results/$', views.results, name='results'),
    # # ex: /polls/5/vote/
    # url(r'^(?P<question_id>[0-9]+)/vote/$', views.vote, name='vote'),
]
