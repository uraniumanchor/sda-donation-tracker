# Create your views here.
from django.shortcuts import render,render_to_response
from django.db.models import Count,Sum,Max,Avg
from django.db.utils import ConnectionDoesNotExist
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth import authenticate,login as auth_login,logout as auth_logout
from django.contrib.auth.forms import AuthenticationForm
from django.http import HttpResponse,HttpResponseRedirect
from django.template import RequestContext
from django.template.base import TemplateSyntaxError
from django.utils import translation
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect
from django import template
from donations.tracker.models import *
from donations.tracker.forms import *
from donations import settings
import django.shortcuts
import sys
import datetime
import settings

def dv():
	return str(django.VERSION[0]) + '.' + str(django.VERSION[1]) + '.' + str(django.VERSION[2])
	
def pv():
	return str(sys.version_info[0]) + '.' + str(sys.version_info[1]) + '.' + str(sys.version_info[2])
	
def checkdb(db):
	if db=='default':
		raise ConnectionDoesNotExist
	database = db
	if database=='' or database==None: database='default'
	if database[-1:]=='/': database=database[:-1]
	if database not in settings.DATABASES:
		raise ConnectionDoesNotExist
	return database
	
def fixorder(queryset, orderdict, sort, order):
	if len(orderdict[sort]) == 2:
		queryset = queryset.order_by(orderdict[sort][0], orderdict[sort][1])
	else:
		queryset = queryset.order_by(orderdict[sort][0])
	if order == -1:
		queryset = queryset.reverse()
	return queryset

def redirect(request):
	return django.shortcuts.redirect('/tracker/')

@csrf_protect
@never_cache
def login(request):
	redirect_to = request.REQUEST.get('next', '/')
	if len(redirect_to) == 0 or redirect_to[0] != '/':
		redirect_to = '/' + redirect_to
	while redirect_to[:2] == '//':
		redirect_to = '/' + redirect_to[2:]
	if request.method == 'POST':
		form = AuthenticationForm(data=request.POST)
		if form.is_valid():
			auth_login(request, form.get_user())
	return django.shortcuts.redirect(redirect_to)

def logout(request):
	auth_logout(request)
	return django.shortcuts.redirect(request.META.get('HTTP_REFERER', '/'))	
	
def tracker_response(request, db=None, template='tracker/index.html', dict={}, status=200):
	starttime = datetime.datetime.now()
	database = checkdb(db)
	usernames = request.user.has_perm('tracker.view_usernames') and 'nonames' not in request.GET
	emails = request.user.has_perm('tracker.view_emails') and 'noemails' not in request.GET
	showtime = request.user.has_perm('tracker.show_rendertime')
	bidtracker = request.user.has_perms([u'tracker.change_challenge', u'tracker.delete_challenge', u'tracker.change_choiceoption', u'tracker.delete_choice', u'tracker.delete_challengebid', u'tracker.add_choiceoption', u'tracker.change_choicebid', u'tracker.add_challengebid', u'tracker.add_choice', u'tracker.add_choicebid', u'tracker.delete_choiceoption', u'tracker.delete_choicebid', u'tracker.add_challenge', u'tracker.change_choice', u'tracker.change_challengebid'])
	context = RequestContext(request)
	language = translation.get_language_from_request(request)
	translation.activate(language)
	request.LANGUAGE_CODE = translation.get_language()
	profile = None
	if request.user.is_authenticated():
		try:
			profile = request.user.get_profile()
		except ObjectDoesNotExist:
			profile = UserProfile()
			profile.user = request.user
			profile.save()
	if profile:
		template = profile.prepend + template
	authform = AuthenticationForm(request.POST)
	dict.update({
		'static_url' : settings.STATIC_URL,
		'db' : db,
		'dbtitle' : settings.DATABASES[database]['COMMENT'],
		'usernames' : usernames,
		'emails' : emails,
		'bidtracker' : bidtracker,
		'djangoversion' : dv(),
		'pythonversion' : pv(),
		'user' : request.user,
		'profile' : profile,
		'next' : request.REQUEST.get('next', request.path),
		'showtime' : showtime,
		'starttime' : starttime,
		'authform' : authform })
	try:
		if request.user.username[:10]=='openiduser':
			dict.setdefault('usernameform', UsernameForm())
			return render(request, 'tracker/username.html', dictionary=dict)
		return render(request, template, dictionary=dict, status=status)
	except Exception, e:
		if request.user.is_staff and not settings.DEBUG:
			return HttpResponse(unicode(type(e)) + '\n\n' + unicode(e), mimetype='text/plain', status=500)
		raise e
	
def dbindex(request):
	dbs = settings.DATABASES.copy()
	del dbs['default']
	return tracker_response(request, None, 'tracker/dbindex.html', { 'databases' : dbs })

def index(request,db=''):
	try:
		database = checkdb(db)
		agg = Donation.objects.using(database).filter(amount__gt="0.0").aggregate(Sum('amount'), Count('amount'), Max('amount'), Avg('amount'))
		return tracker_response(request, db, 'tracker/index.html', { 'agg' : agg })
	except ConnectionDoesNotExist:
		return tracker_response(request, template='tracker/baddatabase.html', status=404)
		
def setusername(request):
	if not request.user.is_authenticated or request.user.username[:10]!='openiduser' or request.method != 'POST':
		return redirect(request)
	usernameform = UsernameForm(request.POST)
	if usernameform.is_valid():
		request.user.username = request.POST['username']
		request.user.save()
		return django.shortcuts.redirect(request.POST['next'])
	return tracker_response(request, template='tracker/username.html', dict={ 'usernameform' : usernameform })
	
def challengeindex(request,db):
	try:
		database = checkdb(db)
		challenges = Challenge.objects.using(database).values('challengeId', 'name', 'goal', 'speedRun', 'speedRun__name').order_by('speedRun__name').annotate(Sum('challengebid__amount'), Count('challengebid'))
		agg = ChallengeBid.objects.using(database).aggregate(Sum('amount'), Count('amount'))
		return tracker_response(request, db, 'tracker/challengeindex.html', { 'challenges' : challenges, 'agg' : agg })
	except ConnectionDoesNotExist:
		return tracker_response(request, template='tracker/baddatabase.html', status=404)
	
def challenge(request,id,db):
	try:
		database = checkdb(db)
		challenge = Challenge.objects.get(pk=id)
		bids = ChallengeBid.objects.filter(challenge__exact=id).values('amount', 'donation', 'donation__comment', 'donation__donorId', 'donation__timeReceived', 'donation__donorId__firstName', 'donation__donorId__lastName', 'donation__donorId__email').order_by('-donation__timeReceived')
		comments = 'comments' in request.GET
		agg = ChallengeBid.objects.using(database).filter(challenge__exact=id).aggregate(Sum('amount'), Count('amount'))
		return tracker_response(request, db, 'tracker/challenge.html', { 'challenge' : challenge, 'comments' : comments, 'bids' : bids, 'agg' : agg })
	except ObjectDoesNotExist:
		return tracker_response(request, db, template='tracker/badobject.html', status=404)
	except ConnectionDoesNotExist:
		return tracker_response(request, template='tracker/baddatabase.html', status=404)
	
def choiceindex(request,db):
	try:
		database = checkdb(db)
		choices = Choice.objects.using(database).values('choiceId', 'name', 'speedRun', 'speedRun__name', 'choiceoption', 'choiceoption__name').annotate(Sum('choiceoption__choicebid__amount'), Count('choiceoption__choicebid')).order_by('speedRun__name','name','-choiceoption__choicebid__amount__sum')
		agg = ChoiceBid.objects.using(database).aggregate(Sum('amount'), Count('amount'))
		return tracker_response(request, db, 'tracker/choiceindex.html', { 'choices' : choices, 'agg' : agg })
	except ConnectionDoesNotExist:
		return tracker_response(request, template='tracker/baddatabase.html', status=404)
	
def choice(request,id,db='default'):
	try:
		database = checkdb(db)
		choice = Choice.objects.using(database).get(pk=id)
		choicebids = ChoiceBid.objects.using(database).filter(optionId__choice__exact=id).values('optionId', 'donationId', 'donationId__donorId', 'donationId__donorId__lastName', 'donationId__donorId__firstName', 'donationId__donorId__email', 'donationId__timeReceived', 'donationId__comment', 'amount').order_by('-donationId__timeReceived')
		options = ChoiceOption.objects.using(database).filter(choice__exact=id).annotate(Sum('choicebid__amount'), Count('choicebid__amount'))
		agg = ChoiceBid.objects.using(database).filter(optionId__choice__exact=id).aggregate(Sum('amount'), Count('amount'))
		comments = 'comments' in request.GET
		return tracker_response(request, db, 'tracker/choice.html', { 'choice' : choice, 'choicebids' : choicebids, 'comments' : comments, 'options' : options, 'agg' : agg })
	except ObjectDoesNotExist:
		return tracker_response(request, db, template='tracker/badobject.html', status=404)
	except ConnectionDoesNotExist:
		return tracker_response(request, template='tracker/baddatabase.html', status=404)
		
def choiceoption(request,id,db='default'):
	try:
		orderdict = { 
			'name'   : ('donationId__donorId__lastName', 'donationId__donorId__firstName'),
			'amount' : ('amount', ),
			'time'   : ('donationId__timeReceived', ),
		}
		sort = request.GET.get('sort', 'time')
		if sort not in orderdict:
			sort = 'time'
		order = int(request.GET.get('order', '-1'))
		database = checkdb(db)
		choiceoption = ChoiceOption.objects.using(database).get(pk=id)
		agg = ChoiceBid.objects.using(database).filter(optionId__exact=id).aggregate(Sum('amount'))
		choicebids = ChoiceBid.objects.using(database).values('donationId', 'donationId__comment', 'donationId__donorId', 'donationId__donorId__firstName','donationId__donorId__lastName', 'donationId__donorId__email', 'amount', 'donationId__timeReceived').filter(optionId__exact=id)
		choicebids = fixorder(choicebids, orderdict, sort, order)
		comments = 'comments' in request.GET
		return tracker_response(request, db, 'tracker/choiceoption.html', { 'choiceoption' : choiceoption, 'choicebids' : choicebids, 'comments' : comments, 'agg' : agg })
	except ObjectDoesNotExist:
		return tracker_response(request, db, template='tracker/badobject.html', status=404)
	except ConnectionDoesNotExist:
		return tracker_response(request, template='tracker/baddatabase.html', status=404)
		

def choicebidadd(request,id,db='default'):
	return index(request,db)
		
def donorindex(request,db='default'):
	try:
		orderdict = { 
			'name'  : ('lastName',              'firstName'),
			'total' : ('donation__amount__sum',            ),
			'max'   : ('donation__amount__max',            ),
			'avg'   : ('donation__amount__avg',            )
		}
		sort = request.GET.get('sort', 'name')
		if sort not in orderdict:
			sort = 'name'
		order = int(request.GET.get('order', '1'))
		database = checkdb(db)
		donors = Donor.objects.using(database).filter(lastName__isnull=False).annotate(Sum('donation__amount'), Count('donation__amount'), Max('donation__amount'), Avg('donation__amount'))
		donors = fixorder(donors, orderdict, sort, order)
		agg = Donation.objects.using(database).filter(amount__gt="0.0").aggregate(Count('amount'))
		return tracker_response(request, db, 'tracker/donorindex.html', { 'donors' : donors, 'agg' : agg })
	except ConnectionDoesNotExist:
		return tracker_response(request, template='tracker/baddatabase.html', status=404)
	
def donor(request,id,db='default'):
	try:
		database = checkdb(db)
		donor = Donor.objects.using(database).get(pk=id)
		donations = Donation.objects.using(database).filter(donorId__exact=id)
		comments = 'comments' in request.GET
		agg = donations.aggregate(Sum('amount'), Count('amount'), Max('amount'), Avg('amount'))
		return tracker_response(request, db, 'tracker/donor.html', { 'donor' : donor, 'donations' : donations, 'agg' : agg, 'comments' : comments })
	except ObjectDoesNotExist:
		return tracker_response(request, db, template='tracker/badobject.html', status=404)
	except ConnectionDoesNotExist:
		return tracker_response(request, template='tracker/baddatabase.html', status=404)
	
def donationindex(request,db='default'):
	try:
		orderdict = { 
			'name'   : ('donorId__lastName', 'donorId__firstName'),
			'amount' : ('amount', ),
			'time'   : ('timeReceived', ),
		}
		sort = request.GET.get('sort', 'time')
		if sort not in orderdict:
			sort = 'time'
		order = int(request.GET.get('order', '-1'))
		database = checkdb(db)
		donations = Donation.objects.using(database).filter(amount__gt="0.0").values('donationId', 'domain', 'timeReceived', 'amount', 'comment','donorId','donorId__lastName','donorId__firstName','donorId__email')
		donations = fixorder(donations, orderdict, sort, order)
		if not request.user.has_perm('donations.view_full_list') or 'recent' in request.GET:
			donations = donations[:50]
		agg = Donation.objects.using(database).filter(amount__gt="0.0").aggregate(Sum('amount'), Count('amount'), Max('amount'), Avg('amount'))
		return tracker_response(request, db, 'tracker/donationindex.html', { 'donations' : donations, 'agg' : agg })
	except ConnectionDoesNotExist:
		return tracker_response(request, template='tracker/baddatabase.html', status=404)

def donation(request,id,db='default'):
	try:
		database = checkdb(db)
		donation = Donation.objects.using(database).get(pk=id)
		donor = donation.donorId
		choicebids = ChoiceBid.objects.using(database).filter(donationId__exact=id).values('amount', 'optionId', 'optionId__name', 'optionId__choice', 'optionId__choice__name', 'optionId__choice__speedRun', 'optionId__choice__speedRun__name')
		challengebids = ChallengeBid.objects.using(database).filter(donation__exact=id).values('amount', 'challenge', 'challenge__name', 'challenge__goal', 'challenge__speedRun', 'challenge__speedRun__name')
		return tracker_response(request, db, 'tracker/donation.html', { 'donation' : donation, 'donor' : donor, 'choicebids' : choicebids, 'challengebids' : challengebids })
	except ObjectDoesNotExist:
		return tracker_response(request, db, template='tracker/badobject.html', status=404)
	except ConnectionDoesNotExist:
		return tracker_response(request, template='tracker/baddatabase.html', status=404)

def gameindex(request,db='default'):
	try:
		database = checkdb(db)
		games = SpeedRun.objects.using(database).all()
		return tracker_response(request, db, 'tracker/gameindex.html', { 'games' : games })
	except ConnectionDoesNotExist:
		return tracker_response(request, template='tracker/baddatabase.html', status=404)

def game(request,id,db='default'):
	try:
		database = checkdb(db)
		game = SpeedRun.objects.using(database).get(pk=id)
		challenges = Challenge.objects.using(database).filter(speedRun__exact=id).annotate(Sum('challengebid__amount'), Count('challengebid'))
		choices = Choice.objects.using(database).filter(speedRun__exact=game).values('choiceId', 'name', 'choiceoption', 'choiceoption__name',).annotate(Sum('choiceoption__choicebid__amount'), Count('choiceoption__choicebid')).order_by('name', '-choiceoption__choicebid__amount__sum')
		return tracker_response(request, db, 'tracker/game.html', { 'game' : game, 'challenges' : challenges, 'choices' : choices })
	except ObjectDoesNotExist:
		return tracker_response(request, db, template='tracker/badobject.html', status=404)
	except ConnectionDoesNotExist:
		return tracker_response(request, template='tracker/baddatabase.html', status=404)
	
def prizeindex(request,db='default'):
	try:
		database = checkdb(db)
		prizes = Prize.objects.using(database).values('name', 'description', 'image', 'donor', 'donor__firstName', 'donor__lastName', 'donor__email')
		return tracker_response(request, db, 'tracker/prizeindex.html', { 'prizes' : prizes })
	except ConnectionDoesNotExist:
		return tracker_response(request, template='tracker/baddatabase.html', status=404)
