from django.conf import settings
from django.conf.urls import include, url
from django.contrib import admin


urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^accounts/', include('registration.backends.hmac.urls')),
    url(r'^to/(?P<goal_slug>[\-\w]+)/', include('goal.urls')),
    url(r'^to/(?P<goal_slug>[\-\w]+)/', include('proposal.urls')),
]

if settings.DEBUG:
    urlpatterns += [
        url(
            r'^media/(?P<path>.*)$',
            'django.views.static.serve',
            {
                'document_root': settings.MEDIA_ROOT, 'show_indexes': True
            }
        ),
    ]
