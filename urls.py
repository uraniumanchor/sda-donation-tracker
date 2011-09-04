from django.conf.urls.defaults import patterns, include, url

from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'donations.views.home', name='home'),
    # url(r'^donations/', include('donations.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

	url(r'^$', 'donations.tracker.views.redirect'),
	url(r'^tracker/', include('donations.tracker.urls')),
    url(r'^admin/', include(admin.site.urls)),
	url(r'^login/$', 'donations.tracker.views.login'),
	url(r'^logout/$', 'donations.tracker.views.logout'),
)
