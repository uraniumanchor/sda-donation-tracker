# Create your views here.
from django.shortcuts import render,render_to_response
from django.db.models import Count,Sum,Max,Avg
from django.db.utils import ConnectionDoesNotExist
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth import authenticate,login as auth_login,logout as auth_logout
from django.contrib.auth.forms import AuthenticationForm
from django.http import HttpResponseRedirect
from django.template import RequestContext
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect
from donations.tracker.models import *
from donations import settings
import django.shortcuts
import locale
import sys

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
	return django.shortcuts.redirect('tracker/')

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
	database = checkdb(db)
	usernames = request.user.has_perm('tracker.view_usernames')
	emails = request.user.has_perm('tracker.view_emails')
	bidtracker = request.user.has_perms([u'tracker.change_challenge', u'tracker.delete_challenge', u'tracker.change_choiceoption', u'tracker.delete_choice', u'tracker.delete_challengebid', u'tracker.add_choiceoption', u'tracker.change_choicebid', u'tracker.add_challengebid', u'tracker.add_choice', u'tracker.add_choicebid', u'tracker.delete_choiceoption', u'tracker.delete_choicebid', u'tracker.add_challenge', u'tracker.change_choice', u'tracker.change_challengebid'])
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
		'form' : AuthenticationForm(request),
		'next' : request.path })
	return render(request, template, dictionary=dict, status=status)
	
def dbindex(request):
	dbs = settings.DATABASES.copy()
	del dbs['default']
	return tracker_response(request, None, 'tracker/dbindex.html', { 'databases' : dbs })

def index(request,db=''):
	try:
		database = checkdb(db)
		locale.setlocale( locale.LC_ALL, '')
		agg = Donation.objects.using(database).filter(amount__gt="0.0").aggregate(Sum('amount'), Max('amount'), Avg('amount'))
		count = Donation.objects.using(database).filter(amount__gt="0.0").count()
		total,mx,av = locale.currency(agg['amount__sum'], grouping=True),locale.currency(agg['amount__max'], grouping=True),locale.currency(agg['amount__avg'], grouping=True)
		return tracker_response(request, db, 'tracker/index.html', { 'count' : count, 'total' : total, 'mx' : mx, 'av' : av })
	except ConnectionDoesNotExist:
		return tracker_response(request, template='tracker/baddatabase.html', status=404)
	
def challengeindex(request,db):
	try:
		database = checkdb(db)
		challenges = Challenge.objects.using(database).values('challengeId', 'name', 'goal', 'speedRun', 'speedRun__name').order_by('speedRun__name').annotate(Sum('challengebid__amount'))
		total = ChallengeBid.objects.using(database).aggregate(Sum('amount'))
		if total:
			total = total['amount__sum']
		return tracker_response(request, db, 'tracker/challengeindex.html', { 'challenges' : challenges, 'total' : total })
	except ConnectionDoesNotExist:
		return tracker_response(request, template='tracker/baddatabase.html', status=404)
	
def challenge(request,id,db):
	try:
		database = checkdb(db)
		challenge = Challenge.objects.get(pk=id)
		bids = ChallengeBid.objects.filter(challenge__exact=id).values('amount', 'donation', 'donation__donorId', 'donation__timeReceived', 'donation__donorId__firstName', 'donation__donorId__lastName', 'donation__donorId__email')
		return tracker_response(request, db, 'tracker/challenge.html', { 'challenge' : challenge, 'bids' : bids })
	except ObjectDoesNotExist:
		return tracker_response(request, db, template='tracker/badobject.html', status=404)
	except ConnectionDoesNotExist:
		return tracker_response(request, template='tracker/baddatabase.html', status=404)
	
def choiceindex(request,db):
	try:
		database = checkdb(db)
		choices = Choice.objects.using(database).values('choiceId', 'name', 'speedRun', 'speedRun__name', 'choiceoption', 'choiceoption__name').annotate(Sum('choiceoption__choicebid__amount')).order_by('speedRun__name','name','-choiceoption__choicebid__amount__sum')
		total = ChoiceBid.objects.using(database).aggregate(Sum('amount'))
		if total:
			total = total['amount__sum']
		return tracker_response(request, db, 'tracker/choiceindex.html', { 'choices' : choices, 'total' : total })
	except ConnectionDoesNotExist:
		return tracker_response(request, template='tracker/baddatabase.html', status=404)
	
def choice(request,id,db='default'):
	try:
		database = checkdb(db)
		choice = Choice.objects.using(database).get(pk=id)
		options = ChoiceOption.objects.using(database).filter(choice__exact=id).annotate(Sum('choicebid__amount'), Count('choicebid__amount'))
		return tracker_response(request, db, 'tracker/choice.html', { 'choice' : choice, 'options' : options })
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
		total = ChoiceBid.objects.using(database).filter(optionId__exact=id).aggregate(Sum('amount'))
		choicebids = ChoiceBid.objects.using(database).values('donationId', 'donationId__donorId', 'donationId__donorId__firstName','donationId__donorId__lastName', 'donationId__donorId__email', 'amount', 'donationId__timeReceived').filter(optionId__exact=id)
		choicebids = fixorder(choicebids, orderdict, sort, order)
		return tracker_response(request, db, 'tracker/choiceoption.html', { 'choiceoption' : choiceoption, 'total' : total['amount__sum'], 'choicebids' : choicebids })
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
		locale.setlocale( locale.LC_ALL, '')
		donors = Donor.objects.using(database).filter(lastName__isnull=False).annotate(Sum('donation__amount'), Count('donation__amount'), Max('donation__amount'), Avg('donation__amount'))
		donors = fixorder(donors, orderdict, sort, order)
		return tracker_response(request, db, 'tracker/donorindex.html', { 'donors' : donors })
	except ConnectionDoesNotExist:
		return tracker_response(request, template='tracker/baddatabase.html', status=404)
	
def donor(request,id,db='default'):
	try:
		database = checkdb(db)
		locale.setlocale( locale.LC_ALL, '')
		donor = Donor.objects.using(database).get(pk=id)
		donations = Donation.objects.using(database).filter(donorId__exact=id)
		agg = donations.aggregate(Sum('amount'), Count('amount'), Max('amount'), Avg('amount'))
		total,mx,av = locale.currency(agg['amount__sum'], grouping=True),locale.currency(agg['amount__max'], grouping=True),locale.currency(agg['amount__avg'], grouping=True)
		return tracker_response(request, db, 'tracker/donor.html', { 'donor' : donor, 'donations' : donations, 'agg' : agg, 'total' : total, 'mx' : mx, 'av' : av })
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
		return tracker_response(request, db, 'tracker/donationindex.html', { 'donations' : donations })
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
		challenges = Challenge.objects.using(database).filter(speedRun__exact=id).annotate(Sum('challengebid__amount'))
		choices = Choice.objects.using(database).filter(speedRun__exact=game).values('choiceId', 'name', 'choiceoption', 'choiceoption__name',).annotate(Sum('choiceoption__choicebid__amount')).order_by('name', '-choiceoption__choicebid__amount__sum')
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
