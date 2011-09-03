# Create your views here.
from django.shortcuts import render_to_response
from django.db.models import Count,Sum,Max,Avg
from donations.tracker.models import *
import django.shortcuts
import locale
import sys

def dv():
	return str(django.VERSION[0]) + '.' + str(django.VERSION[1]) + '.' + str(django.VERSION[2])
	
def pv():
	return str(sys.version_info[0]) + '.' + str(sys.version_info[1]) + '.' + str(sys.version_info[2])

def redirect(request):
	return django.shortcuts.redirect('tracker/')

def index(request):
	usernames = request.user.has_perm("tracker.view_usernames")
	emails = request.user.has_perm("tracker.view_emails")
	locale.setlocale( locale.LC_ALL, '')
	agg = Donation.objects.filter(amount__gt="0.0").aggregate(Sum('amount'), Max('amount'), Avg('amount'))
	count = Donation.objects.filter(amount__gt="0.0").count()
	total,mx,av = locale.currency(agg['amount__sum'], grouping=True),locale.currency(agg['amount__max'], grouping=True),locale.currency(agg['amount__avg'], grouping=True)
	return render_to_response('tracker/index.html', { 'count' : count, 'total' : total, 'mx' : mx, 'av' : av, 'djangoversion' : dv(), 'pythonversion' : pv(), 'usernames' : usernames, 'emails' : emails })
	
def challengeindex(request):
	usernames = request.user.has_perm("tracker.view_usernames")
	emails = request.user.has_perm("tracker.view_emails")
	challenges = Challenge.objects.values('challengeId', 'name', 'goal', 'speedRun__name').order_by('speedRun__name').annotate(Sum('challengebid__amount'))
	return render_to_response('tracker/challengeindex.html', { 'challenges' : challenges, 'djangoversion' : dv(), 'pythonversion' : pv(), 'usernames' : usernames, 'emails' : emails })
	
def challenge(request):
	return index(request)
	
def choiceindex(request):
	usernames = request.user.has_perm("tracker.view_usernames")
	emails = request.user.has_perm("tracker.view_emails")
	choices = Choice.objects.values('choiceId', 'name', 'speedRun__speedRunId', 'speedRun__name', 'choiceoption__optionId', 'choiceoption__name').order_by('speedRun__name','name','choiceoption__name').annotate(Sum('choiceoption__choicebid__amount'))
	return render_to_response('tracker/choiceindex.html', { 'choices' : choices, 'djangoversion' : dv(), 'pythonversion' : pv(), 'usernames' : usernames, 'emails' : emails })
	
def choice(request,id):
	usernames = request.user.has_perm("tracker.view_usernames")
	emails = request.user.has_perm("tracker.view_emails")
	choice = Choice.objects.get(pk=id)
	options = ChoiceOption.objects.filter(choice__exact=id).annotate(Sum('choicebid__amount'), Count('choicebid__amount'))
	print choice
	print options
	return render_to_response('tracker/choice.html', { 'choice' : choice, 'options' : options, 'djangoversion' : dv(), 'pythonversion' : pv(), 'usernames' : usernames, 'emails' : emails })
		
def choiceoption(request,id):
	usernames = request.user.has_perm("tracker.view_usernames")
	emails = request.user.has_perm("tracker.view_emails")
	choiceoption = ChoiceOption.objects.get(pk=id)
	choicebids = ChoiceBid.objects.values('donationId', 'donationId__donorId', 'donationId__donorId__firstName','donationId__donorId__lastName', 'donationId__donorId__email', 'amount', 'donationId__timeReceived').filter(optionId__exact=id).order_by('donationId__timeReceived')
	print choiceoption
	print choicebids
	return render_to_response('tracker/choiceoption.html', { 'choiceoption' : choiceoption, 'choicebids' : choicebids, 'djangoversion' : dv(), 'pythonversion' : pv(), 'usernames' : usernames, 'emails' : emails })
	
def donorindex(request):
	usernames = request.user.has_perm("tracker.view_usernames")
	emails = request.user.has_perm("tracker.view_emails")
	locale.setlocale( locale.LC_ALL, '')
	donors = Donor.objects.all().filter(lastName__isnull=False).order_by('lastName', 'firstName').annotate(Sum('donation__amount'), Count('donation__amount'), Max('donation__amount'), Avg('donation__amount'))
	return render_to_response('tracker/donorindex.html', { 'donors' : donors, 'djangoversion' : dv(), 'pythonversion' : pv(), 'usernames' : usernames, 'emails' : emails })
	
def donor(request,id):
	usernames = request.user.has_perm("tracker.view_usernames")
	emails = request.user.has_perm("tracker.view_emails")
	locale.setlocale( locale.LC_ALL, '')
	donor = Donor.objects.get(pk=id)
	donations = Donation.objects.filter(donorId__exact=id)
	agg = donations.aggregate(Sum('amount'), Count('amount'), Max('amount'), Avg('amount'))
	total,mx,av = locale.currency(agg['amount__sum'], grouping=True),locale.currency(agg['amount__max'], grouping=True),locale.currency(agg['amount__avg'], grouping=True)
	return render_to_response('tracker/donor.html', { 'donor' : donor, 'donations' : donations, 'agg' : agg, 'total' : total, 'mx' : mx, 'av' : av, 'djangoversion' : dv(), 'pythonversion' : pv(), 'usernames' : usernames, 'emails' : emails })
	
def donationindex(request):
	usernames = request.user.has_perm("tracker.view_usernames")
	emails = request.user.has_perm("tracker.view_emails")
	donations = Donation.objects.filter(amount__gt="0.0").values('donationId', 'timeReceived','amount','donorId__donorId','donorId__lastName','donorId__firstName','donorId__email')
	return render_to_response('tracker/donationindex.html', { 'donations' : donations, 'djangoversion' : dv(), 'pythonversion' : pv(), 'usernames' : usernames, 'emails' : emails })

def donation(request,id):
	usernames = request.user.has_perm("tracker.view_usernames")
	emails = request.user.has_perm("tracker.view_emails")
	donation = Donation.objects.get(pk=id)
	donor = donation.donorId
	print donation
	return render_to_response('tracker/donation.html', { 'donation' : donation, 'donor' : donor, 'djangoversion' : dv(), 'pythonversion' : pv(), 'usernames' : usernames, 'emails' : emails })
	
def gameindex(request):
	usernames = request.user.has_perm("tracker.view_usernames")
	emails = request.user.has_perm("tracker.view_emails")
	return index(request)

def game(request,id):
	usernames = request.user.has_perm("tracker.view_usernames")
	emails = request.user.has_perm("tracker.view_emails")
	return index(request)
	
def prizeindex(request):
	usernames = request.user.has_perm("tracker.view_usernames")
	emails = request.user.has_perm("tracker.view_emails")
	return index(request)

def prize(request,id):
	usernames = request.user.has_perm("tracker.view_usernames")
	emails = request.user.has_perm("tracker.view_emails")
	return index(request)