# Create your views here.
from django.shortcuts import render_to_response
from django.db.models import Count,Sum,Max,Avg
from django.db.utils import ConnectionDoesNotExist
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
	if database=='': database='default'
	if database[-1:]=='/': database=database[:-1]
	if database not in settings.DATABASES:
		raise ConnectionDoesNotExist
	return database

def redirect(request):
	return django.shortcuts.redirect('tracker/')

def tracker_response(request, db, template, dict):
	dict.update({ 'dbtitle' : settings.DATABASES[checkdb(db)]['COMMENT'], 'usernames' : request.user.has_perm('tracker.view_usernames'), 'emails' : request.user.has_perm("tracker.view_emails"), 'djangoversion' : dv(), 'pythonversion' : pv(), 'db' : db })
	return render_to_response(template, dict)
	
def dbindex(request):
	dbs = settings.DATABASES.copy()
	del dbs['default']
	return render_to_response('tracker/dbindex.html', { 'databases' : dbs })

def index(request,db=''):
	try:
		database = checkdb(db)
		locale.setlocale( locale.LC_ALL, '')
		agg = Donation.objects.using(database).filter(amount__gt="0.0").aggregate(Sum('amount'), Max('amount'), Avg('amount'))
		count = Donation.objects.using(database).filter(amount__gt="0.0").count()
		total,mx,av = locale.currency(agg['amount__sum'], grouping=True),locale.currency(agg['amount__max'], grouping=True),locale.currency(agg['amount__avg'], grouping=True)
		return tracker_response(request, db, 'tracker/index.html', { 'count' : count, 'total' : total, 'mx' : mx, 'av' : av })
	except ConnectionDoesNotExist:
		return render_to_response('tracker/baddatabase.html')
	
def challengeindex(request,db):
	try:
		database = checkdb(db)
		challenges = Challenge.objects.using(database).values('challengeId', 'name', 'goal', 'speedRun__name', 'speedRun__speedRunId').order_by('speedRun__name').annotate(Sum('challengebid__amount'))
		return tracker_response(request, db, 'tracker/challengeindex.html', { 'challenges' : challenges })
	except ConnectionDoesNotExist:
		return render_to_response('tracker/baddatabase.html')
	
def challenge(request,id,db):
	return index(request,db)
	
def choiceindex(request,db):
	try:
		database = checkdb(db)
		choices = Choice.objects.using(database).values('choiceId', 'name', 'speedRun__speedRunId', 'speedRun__name', 'choiceoption__optionId', 'choiceoption__name').order_by('speedRun__name','name','choiceoption__name').annotate(Sum('choiceoption__choicebid__amount'))
		return tracker_response(request, db, 'tracker/choiceindex.html', { 'choices' : choice })
	except ConnectionDoesNotExist:
		return render_to_response('tracker/baddatabase.html')
	
def choice(request,id,db='default'):
	try:
		database = checkdb(db)
		choice = Choice.objects.using(database).get(pk=id)
		options = ChoiceOption.objects.using(database).filter(choice__exact=id).annotate(Sum('choicebid__amount'), Count('choicebid__amount'))
		print choice
		print options
		return tracker_response(request, db, 'tracker/choice.html', { 'choice' : choice, 'options' : options })
	except ConnectionDoesNotExist:
		return render_to_response('tracker/baddatabase.html')
		
def choiceoption(request,id,db='default'):
	try:
		database = checkdb(db)
		choiceoption = ChoiceOption.objects.using(database).get(pk=id)
		choicebids = ChoiceBid.objects.using(database).values('donationId', 'donationId__donorId', 'donationId__donorId__firstName','donationId__donorId__lastName', 'donationId__donorId__email', 'amount', 'donationId__timeReceived').filter(optionId__exact=id).order_by('donationId__timeReceived')
		print choiceoption
		print choicebids
		return tracker_response(request, db, 'tracker/choiceoption.html', { 'choiceoption' : choiceoption, 'choicebids' : choicebids })
	except ConnectionDoesNotExist:
		return render_to_response('tracker/baddatabase.html')

def donorindex(request,db='default'):
	try:
		database = checkdb(db)
		locale.setlocale( locale.LC_ALL, '')
		donors = Donor.objects.using(database).filter(lastName__isnull=False).order_by('lastName', 'firstName').annotate(Sum('donation__amount'), Count('donation__amount'), Max('donation__amount'), Avg('donation__amount'))
		return tracker_response(request, db, 'tracker/donorindex.html', { 'donors' : donors })
	except ConnectionDoesNotExist:
		return render_to_response('tracker/baddatabase.html')
	
def donor(request,id,db='default'):
	try:
		database = checkdb(db)
		locale.setlocale( locale.LC_ALL, '')
		donor = Donor.objects.using(database).get(pk=id)
		donations = Donation.objects.using(database).filter(donorId__exact=id)
		agg = donations.aggregate(Sum('amount'), Count('amount'), Max('amount'), Avg('amount'))
		total,mx,av = locale.currency(agg['amount__sum'], grouping=True),locale.currency(agg['amount__max'], grouping=True),locale.currency(agg['amount__avg'], grouping=True)
		return tracker_response(request, db, 'tracker/donor.html', { 'donor' : donor, 'donations' : donations, 'agg' : agg, 'total' : total, 'mx' : mx, 'av' : av })
	except ConnectionDoesNotExist:
		return render_to_response('tracker/baddatabase.html')
	
def donationindex(request,db='default'):
	try:
		database = checkdb(db)
		usernames = request.user.has_perm("tracker.view_usernames")
		emails = request.user.has_perm("tracker.view_emails")
		donations = Donation.objects.using(database).filter(amount__gt="0.0").values('donationId', 'timeReceived', 'amount', 'comment', 'donorId__donorId','donorId__lastName','donorId__firstName','donorId__email')
		return tracker_response(request, db, 'tracker/donationindex.html', { 'donations' : donations })
	except ConnectionDoesNotExist:
		return render_to_response('tracker/baddatabase.html')

def donation(request,id,db='default'):
	try:
		database = checkdb(db)
		usernames = request.user.has_perm("tracker.view_usernames")
		emails = request.user.has_perm("tracker.view_emails")
		donation = Donation.objects.using(database).get(pk=id)
		donor = donation.donorId
		print donation
		return tracker_response(request, db, 'tracker/donation.html', { 'donation' : donation, 'donor' : donor })
	except ConnectionDoesNotExist:
		return render_to_response('tracker/baddatabase.html')

def gameindex(request,db='default'):
	try:
		database = checkdb(db)
		return index(request,db)
	except ConnectionDoesNotExist:
		return render_to_response('tracker/baddatabase.html')

def game(request,id,db='default'):
	try:
		database = checkdb(db)
		return index(request,db)
	except ConnectionDoesNotExist:
		return render_to_response('tracker/baddatabase.html')
	
def prizeindex(request,db='default'):
	try:
		database = checkdb(db)
		return index(request,db)
	except ConnectionDoesNotExist:
		return render_to_response('tracker/baddatabase.html')

def prize(request,id,db='default'):
	try:
		database = checkdb(db)
		return index(request,db)
	except ConnectionDoesNotExist:
		return render_to_response('tracker/baddatabase.html')
