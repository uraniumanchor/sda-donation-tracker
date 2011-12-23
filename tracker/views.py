# Create your views here.
from django.shortcuts import render,render_to_response
from django.db.models import Count,Sum,Max,Avg,Q
from django.db.utils import ConnectionDoesNotExist
from django.core.exceptions import ObjectDoesNotExist
from django.core.cache import cache
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
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
	queryset = queryset.order_by(*orderdict[sort])
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

@never_cache
def logout(request):
	auth_logout(request)
	return django.shortcuts.redirect(request.META.get('HTTP_REFERER', '/'))	
	
def tracker_response(request, db=None, template='tracker/index.html', dict={}, status=200):
	starttime = datetime.datetime.now()
	database = checkdb(db)
	usernames = request.user.has_perm('tracker.view_usernames') and 'nonames' not in request.GET
	emails = request.user.has_perm('tracker.view_emails') and 'noemails' not in request.GET
	showtime = request.user.has_perm('tracker.show_rendertime')
	canfull = request.user.has_perm('tracker.view_full_list')
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
		'canfull' : canfull,
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
		raise
	
def eventlist(request):
	dbs = settings.DATABASES.copy()
	del dbs['default']
	return tracker_response(request, None, 'tracker/eventlist.html', { 'databases' : dbs })

def index(request,db=''):
	try:
		database = checkdb(db)
		agg = Donation.objects.using(database).filter(amount__gt="0.0").aggregate(amount=Sum('amount'), count=Count('amount'), max=Max('amount'), avg=Avg('amount'))
		count = { 
			'games' : SpeedRun.objects.using(database).count(), 
			'prizes' : Prize.objects.using(database).count(),
			'challenges' : Challenge.objects.using(database).count(),
			'choices' : Choice.objects.using(database).count(),
			'donors' : Donor.objects.using(database).count(),
		}
		return tracker_response(request, db, 'tracker/index.html', { 'agg' : agg, 'count' : count })
	except ConnectionDoesNotExist:
		return tracker_response(request, template='tracker/baddatabase.html', status=404)

@never_cache
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
		challenges = Challenge.objects.using(database).values('id', 'name', 'goal', 'speedRun', 'speedRun__sortKey', 'speedRun__name').order_by('speedRun__sortKey').annotate(amount=Sum('challengebid__amount'), count=Count('challengebid'))
		agg = ChallengeBid.objects.using(database).aggregate(amount=Sum('amount'), count=Count('amount'))
		return tracker_response(request, db, 'tracker/challengeindex.html', { 'challenges' : challenges, 'agg' : agg })
	except ConnectionDoesNotExist:
		return tracker_response(request, template='tracker/baddatabase.html', status=404)
	
def challenge(request,id,db):
	try:
		orderdict = { 
			'name'   : ('donation__donor__lastName', 'donation__donor__firstName'),
			'amount' : ('amount', ),
			'time'   : ('donation__timeReceived', ),
		}
		sort = request.GET.get('sort', 'time')
		if sort not in orderdict:
			sort = 'time'
		try:
			order = int(request.GET.get('order', '-1'))
		except ValueError:
			order = -1
		database = checkdb(db)
		challenge = Challenge.objects.using(database).get(pk=id)
		bids = ChallengeBid.objects.using(database).filter(challenge__exact=id).values('amount', 'donation', 'donation__comment', 'donation__commentState', 'donation__donor', 'donation__timeReceived', 'donation__donor__firstName', 'donation__donor__lastName', 'donation__donor__email').order_by('-donation__timeReceived')
		bids = fixorder(bids, orderdict, sort, order)
		comments = 'comments' in request.GET
		agg = ChallengeBid.objects.using(database).filter(challenge__exact=id).aggregate(amount=Sum('amount'), count=Count('amount'))
		return tracker_response(request, db, 'tracker/challenge.html', { 'challenge' : challenge, 'comments' : comments, 'bids' : bids, 'agg' : agg })
	except ObjectDoesNotExist:
		return tracker_response(request, db, template='tracker/badobject.html', status=404)
	except ConnectionDoesNotExist:
		return tracker_response(request, template='tracker/baddatabase.html', status=404)
	
def choiceindex(request,db):
	try:
		database = checkdb(db)
		choices = Choice.objects.using(database).values('id', 'name', 'speedRun', 'speedRun__sortKey', 'speedRun__name', 'choiceoption', 'choiceoption__name').annotate(amount=Sum('choiceoption__choicebid__amount'), count=Count('choiceoption__choicebid')).order_by('speedRun__sortKey','name','-amount')
		agg = ChoiceBid.objects.using(database).aggregate(amount=Sum('amount'), count=Count('amount'))
		return tracker_response(request, db, 'tracker/choiceindex.html', { 'choices' : choices, 'agg' : agg })
	except ConnectionDoesNotExist:
		return tracker_response(request, template='tracker/baddatabase.html', status=404)
	
def choice(request,id,db='default'):
	try:
		database = checkdb(db)
		choice = Choice.objects.using(database).get(pk=id)
		choicebids = ChoiceBid.objects.using(database).filter(choiceOption__choice=id).values('choiceOption', 'donation', 'donation__donor', 'donation__donor__lastName', 'donation__donor__firstName', 'donation__donor__email', 'donation__timeReceived', 'donation__comment', 'donation__commentState', 'amount').order_by('-donation__timeReceived')
		options = ChoiceOption.objects.using(database).filter(choice=id).annotate(amount=Sum('choicebid__amount'), count=Count('choicebid__amount')).order_by('-amount')
		agg = ChoiceBid.objects.using(database).filter(choiceOption__choice=id).aggregate(amount=Sum('amount'), count=Count('amount'))
		comments = 'comments' in request.GET
		return tracker_response(request, db, 'tracker/choice.html', { 'choice' : choice, 'choicebids' : choicebids, 'comments' : comments, 'options' : options, 'agg' : agg })
	except ObjectDoesNotExist:
		return tracker_response(request, db, template='tracker/badobject.html', status=404)
	except ConnectionDoesNotExist:
		return tracker_response(request, template='tracker/baddatabase.html', status=404)
		
def choiceoption(request,id,db='default'):
	try:
		orderdict = { 
			'name'   : ('donation__donor__lastName', 'donation__donor__firstName'),
			'amount' : ('amount', ),
			'time'   : ('donation__timeReceived', ),
		}
		sort = request.GET.get('sort', 'time')
		if sort not in orderdict:
			sort = 'time'
		try:
			order = int(request.GET.get('order', '-1'))
		except ValueError:
			order = -1
		database = checkdb(db)
		choiceoption = ChoiceOption.objects.using(database).get(pk=id)
		agg = ChoiceBid.objects.using(database).filter(choiceOption=id).aggregate(amount=Sum('amount'))
		bids = ChoiceBid.objects.using(database).values('donation', 'donation__comment', 'donation__commentState', 'donation__donor', 'donation__donor__firstName','donation__donor__lastName', 'donation__donor__email', 'amount', 'donation__timeReceived').filter(choiceOption=id)
		bids = fixorder(bids, orderdict, sort, order)
		comments = 'comments' in request.GET
		return tracker_response(request, db, 'tracker/choiceoption.html', { 'choiceoption' : choiceoption, 'bids' : bids, 'comments' : comments, 'agg' : agg })
	except ObjectDoesNotExist:
		return tracker_response(request, db, template='tracker/badobject.html', status=404)
	except ConnectionDoesNotExist:
		return tracker_response(request, template='tracker/baddatabase.html', status=404)
		

def choicebidadd(request,id,db='default'):
	return index(request,db)
		
def donorindex(request,db='default'):
	try:
		orderdict = { 
			'name'  : ('lastName', 'firstName'),
			'total' : ('amount',   ),
			'max'   : ('max',      ),
			'avg'   : ('avg',      )
		}
		try:
			page = int(request.GET.get('page', 1))
		except ValueError:
			page = 1
		sort = request.GET.get('sort', 'name')
		if sort not in orderdict:
			sort = 'name'
		try:
			order = int(request.GET.get('order', 1))
		except ValueError:
			order = 1
		database = checkdb(db)
		donors = Donor.objects.using(database).filter(lastName__isnull=False).annotate(amount=Sum('donation__amount'), count=Count('donation__amount'), max=Max('donation__amount'), avg=Avg('donation__amount'))
		print donors
		donors = fixorder(donors, orderdict, sort, order)
		fulllist = request.user.has_perm('tracker.view_full_list') and 'full' in request.GET
		paginator = Paginator(donors,50)
		if fulllist:
			pageinfo = { 'paginator' : paginator, 'has_previous' : False, 'has_next' : False, 'num_pages' : paginator.num_pages }
			page = 0
		else:
			try:
				pageinfo = paginator.page(page)
			except PageIsNotAnInteger:
				pageinfo = paginator.page(1)
			except EmptyPage:
				pageinfo = paginator.page(paginator.num_pages)
			donors = pageinfo.object_list
		agg = Donation.objects.using(database).filter(amount__gt="0.0").aggregate(count=Count('amount'))
		return tracker_response(request, db, 'tracker/donorindex.html', { 'donors' : donors, 'pageinfo' : pageinfo, 'page' : page, 'fulllist' : fulllist, 'agg' : agg, 'sort' : sort, 'order' : order })
	except ConnectionDoesNotExist:
		return tracker_response(request, template='tracker/baddatabase.html', status=404)
	
def donor(request,id,db='default'):
	try:
		database = checkdb(db)
		donor = Donor.objects.using(database).get(pk=id)
		donations = Donation.objects.using(database).filter(donor__exact=id)
		comments = 'comments' in request.GET
		agg = donations.aggregate(amount=Sum('amount'), count=Count('amount'), max=Max('amount'), avg=Avg('amount'))
		return tracker_response(request, db, 'tracker/donor.html', { 'donor' : donor, 'donations' : donations, 'agg' : agg, 'comments' : comments })
	except ObjectDoesNotExist:
		return tracker_response(request, db, template='tracker/badobject.html', status=404)
	except ConnectionDoesNotExist:
		return tracker_response(request, template='tracker/baddatabase.html', status=404)
	
def donationindex(request,db='default'):
	try:
		orderdict = { 
			'name'   : ('donor__lastName', 'donor__firstName'),
			'amount' : ('amount', ),
			'time'   : ('timeReceived', ),
		}
		try:
			page = int(request.GET.get('page', 1))
		except ValueError:
			page = 1
		sort = request.GET.get('sort', 'time')
		if sort not in orderdict:
			sort = 'time'
		try:
			order = int(request.GET.get('order', -1))
		except ValueError:
			order = -1
		database = checkdb(db)
		donations = Donation.objects.using(database).filter(amount__gt="0.0").values('id', 'domain', 'timeReceived', 'amount', 'comment','donor','donor__lastName','donor__firstName','donor__email')
		donations = fixorder(donations, orderdict, sort, order)
		fulllist = request.user.has_perm('tracker.view_full_list') and 'full' in request.GET
		paginator = Paginator(donations,50)
		if fulllist:
			pageinfo = { 'paginator' : paginator, 'has_previous' : False, 'has_next' : False }
			page = 0
		else:
			try:
				pageinfo = paginator.page(page)
			except PageIsNotAnInteger:
				pageinfo = paginator.page(1)
			except EmptyPage:
				pageinfo = paginator.page(paginator.num_pages)
			donations = pageinfo.object_list
		agg = Donation.objects.using(database).filter(amount__gt="0.0").aggregate(amount=Sum('amount'), count=Count('amount'), max=Max('amount'), avg=Avg('amount'))
		return tracker_response(request, db, 'tracker/donationindex.html', { 'donations' : donations, 'pageinfo' :  pageinfo, 'agg' : agg, 'fulllist' : fulllist, 'sort' : sort, 'order' : order, 'page' : page })
	except ConnectionDoesNotExist:
		return tracker_response(request, template='tracker/baddatabase.html', status=404)

def donation(request,id,db='default'):
	try:
		database = checkdb(db)
		donation = Donation.objects.using(database).get(pk=id)
		donor = donation.donor
		choicebids = ChoiceBid.objects.using(database).filter(donation__exact=id).values('amount', 'choiceOption', 'choiceOption__name', 'choiceOption__choice', 'choiceOption__choice__name', 'choiceOption__choice__speedRun', 'choiceOption__choice__speedRun__name')
		challengebids = ChallengeBid.objects.using(database).filter(donation__exact=id).values('amount', 'challenge', 'challenge__name', 'challenge__goal', 'challenge__speedRun', 'challenge__speedRun__name')
		return tracker_response(request, db, 'tracker/donation.html', { 'donation' : donation, 'donor' : donor, 'choicebids' : choicebids, 'challengebids' : challengebids })
	except ObjectDoesNotExist:
		return tracker_response(request, db, template='tracker/badobject.html', status=404)
	except ConnectionDoesNotExist:
		return tracker_response(request, template='tracker/baddatabase.html', status=404)

def gameindex(request,db='default'):
	try:
		database = checkdb(db)
		games = SpeedRun.objects.using(database).all().annotate(choices=Sum('choice'), challenges=Sum('challenge'))
		return tracker_response(request, db, 'tracker/gameindex.html', { 'games' : games })
	except ConnectionDoesNotExist:
		return tracker_response(request, template='tracker/baddatabase.html', status=404)

def game(request,id,db='default'):
	try:
		database = checkdb(db)
		game = SpeedRun.objects.using(database).get(pk=id)
		challenges = Challenge.objects.using(database).filter(speedRun=id).annotate(amount=Sum('challengebid__amount'), count=Count('challengebid'))
		choices = Choice.objects.using(database).filter(speedRun=id).values('id', 'name', 'choiceoption', 'choiceoption__name',).annotate(amount=Sum('choiceoption__choicebid__amount'), count=Count('choiceoption__choicebid')).order_by('name', '-amount')
		return tracker_response(request, db, 'tracker/game.html', { 'game' : game, 'challenges' : challenges, 'choices' : choices })
	except ObjectDoesNotExist:
		return tracker_response(request, db, template='tracker/badobject.html', status=404)
	except ConnectionDoesNotExist:
		return tracker_response(request, template='tracker/baddatabase.html', status=404)
		
def prizeindex(request,db='default'):
	try:
		database = checkdb(db)
		# there has to be a better way to do this
		prizes1 = Prize.objects.using(database).values('id', 'name', 'sortKey', 'image', 'minimumBid', 'startGame', 'startGame__name', 'endGame', 'endGame__name', 'winner', 'winner__firstName', 'winner__lastName', 'winner__email')
		prizes2 = Prize.objects.using(database).values('id', 'name', 'sortKey', 'image', 'minimumBid').filter(winner__isnull=True,startGame__isnull=True)
		prizes3 = Prize.objects.using(database).values('id', 'name', 'sortKey', 'image', 'minimumBid', 'startGame', 'startGame__name', 'endGame', 'endGame__name').filter(winner__isnull=True)
		prizes4 = Prize.objects.using(database).values('id', 'name', 'sortKey', 'image', 'minimumBid', 'winner', 'winner__firstName', 'winner__lastName', 'winner__email').filter(startGame__isnull=True)
		prizes = list(prizes1) + list(prizes2) + list(prizes3) + list(prizes4)
		prizes.sort(key=lambda x: x['sortKey'])
		return tracker_response(request, db, 'tracker/prizeindex.html', { 'prizes' : prizes })
	except ConnectionDoesNotExist:
		return tracker_response(request, template='tracker/baddatabase.html', status=404)

def prize(request,id,db='default'):
	try:
		database = checkdb(db)
		prize = Prize.objects.using(database).filter(id=id).values('name', 'image', 'description', 'minimumBid', 'startGame', 'endGame', 'winner')[0]
		games = None
		winner = None
		if prize['startGame']:
			startGame = SpeedRun.objects.using(database).get(pk=prize['startGame'])
			endGame = SpeedRun.objects.using(database).get(pk=prize['endGame'])
			games = SpeedRun.objects.using(database).filter(sortKey__gte=startGame.sortKey,sortKey__lte=endGame.sortKey)
		if prize['winner']:
			winner = Donor.objects.using(database).get(pk=prize['winner'])
		return tracker_response(request, db, 'tracker/prize.html', { 'prize' : prize, 'games' : games, 'winner' : winner })
	except ObjectDoesNotExist:
		return tracker_response(request, db, template='tracker/badobject.html', status=404)
	except ConnectionDoesNotExist:
		return tracker_response(request, template='tracker/baddatabase.html', status=404)
