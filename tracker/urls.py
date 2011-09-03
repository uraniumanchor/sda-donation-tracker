from django.conf.urls.defaults import patterns, include, url

urlpatterns = patterns('tracker.views',
	url(r'^$', 'index'),
	url(r'^challenge/$', 'challengeindex'),
	url(r'^choice/$', 'choiceindex'),
)