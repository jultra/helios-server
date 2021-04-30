"""
Authentication URLs

Ben Adida (ben@adida.net)
"""
"""
from django.conf.urls.defaults import *

from views import *
from auth_systems.password import password_login_view, password_forgotten_view
from auth_systems.twitter import follow_view

urlpatterns = patterns('',
    # basic static stuff
    (r'^$', index),
    (r'^logout$', logout),
    (r'^start/(?P<system_name>.*)$', start),
    # weird facebook constraint for trailing slash
    (r'^after/$', after),
    (r'^why$', perms_why),
    (r'^after_intervention$', after_intervention),
    
    ## should make the following modular

    # password auth
    (r'^password/login/$', password_login_view),
    (r'^password/forgot', password_forgotten_view),

    # twitter
    (r'^twitter/follow', follow_view),
)"""

"""
Authentication URLs
Ben Adida (ben@adida.net)
"""

from django.conf.urls import url

from settings import AUTH_ENABLED_SYSTEMS
from . import views, url_names

urlpatterns = [
    # basic static stuff
    url(r'^$', views.index, name=url_names.AUTH_INDEX),
    url(r'^logout$', views.logout, name=url_names.AUTH_LOGOUT),
    url(r'^start/(?P<system_name>.*)$', views.start, name=url_names.AUTH_START),
    # weird facebook constraint for trailing slash
    url(r'^after/$', views.after, name=url_names.AUTH_AFTER),
    url(r'^why$', views.perms_why, name=url_names.AUTH_WHY),
    url(r'^after_intervention$', views.after_intervention, name=url_names.AUTH_AFTER_INTERVENTION),
]

# password auth
if 'password' in AUTH_ENABLED_SYSTEMS:
    from .auth_systems.password import urlpatterns as password_patterns
    urlpatterns.extend(password_patterns)

# twitter
if 'twitter' in AUTH_ENABLED_SYSTEMS:
    from .auth_systems.twitter import urlpatterns as twitter_patterns
    urlpatterns.extend(twitter_patterns)
