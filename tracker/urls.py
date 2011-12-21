from django.conf.urls.defaults import patterns, include, url

urlpatterns = patterns('tracker.views',
	url(r'^challenges/(?P<db>(\w+/|))$', 'challengeindex'),
	url(r'^challenge/(?P<db>(\w+/|))(?P<id>-?\d+)/$', 'challenge'),
	url(r'^choices/(?P<db>(\w+/|))$', 'choiceindex'),
	url(r'^choice/(?P<db>(\w+/|))(?P<id>-?\d+)/$', 'choice'),
	url(r'^choiceoption/(?P<db>(\w+/|))(?P<id>-?\d+)/$', 'choiceoption'),
	url(r'^choicebid/(?P<db>(\w+/|))add/(?P<id>-?\d+)/$', 'choicebidadd'),
	url(r'^donors/(?P<db>(\w+/|))$', 'donorindex'),
	url(r'^donor/(?P<db>(\w+/|))(?P<id>-?\d+)/$', 'donor'),
	url(r'^donations/(?P<db>(\w+/|))$', 'donationindex'),
	url(r'^donation/(?P<db>(\w+/|))(?P<id>-?\d+)/$', 'donation'),
	url(r'^games/(?P<db>(\w+/|))$', 'gameindex'),
	url(r'^game/(?P<db>(\w+/|))(?P<id>-?\d+)/$', 'game'),
	url(r'^prizes/(?P<db>(\w+/|))$', 'prizeindex'),
	url(r'^prize/(?P<db>(\w+/|))(?P<id>-?\d+)/$', 'prize'),
	url(r'^events/$', 'eventlist'),
	url(r'^setusername/$', 'setusername'),
	url(r'^i18n/', include('django.conf.urls.i18n')),
	url(r'^index/(?P<db>(\w+/|))$', 'index'),
	url(r'^$', 'index'),
)
