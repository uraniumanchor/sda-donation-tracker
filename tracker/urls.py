from django.conf.urls.defaults import patterns, include, url

urlpatterns = patterns('tracker.views',
	url(r'^$', 'index'),
	url(r'^challenges/$', 'challengeindex'),
	url(r'^choices/$', 'choiceindex'),
	url(r'^choice/(?P<id>-?\d+)/$', 'choice'),
	url(r'^choiceoption/(?P<id>-?\d+)/$', 'choiceoption'),
	url(r'^donors/$', 'donorindex'),
	url(r'^donor/(?P<id>-?\d+)/$', 'donor'),
	url(r'^donations/$', 'donationindex'),
	url(r'^donation/(?P<id>-?\d+)/$', 'donation'),
	url(r'^games/$', 'gameindex'),
	url(r'^game/(?P<id>-?\d+)/$', 'game'),
	url(r'^prizes/$', 'prizeindex'),
	url(r'^prize/(?P<id>-?\d+)/$', 'prize'),
)