from django.conf.urls.defaults import patterns, include, url

urlpatterns = patterns('tracker.views',
	(r'^$', 'index')
)