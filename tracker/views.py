# Create your views here.
from django.shortcuts import render_to_response
from django.db.models import Count,Sum,Max,Avg
from donations.tracker.models import *
import django.shortcuts
import locale

def redirect(request):
	return django.shortcuts.redirect('tracker/')

def index(request):
	locale.setlocale( locale.LC_ALL, '')
	agg = Donation.objects.filter(amount__gt="0.0").aggregate(Sum('amount'), Max('amount'), Avg('amount'))
	count = Donation.objects.filter(amount__gt="0.0").count()
	total,mx,av = locale.currency(agg['amount__sum'], grouping=True),locale.currency(agg['amount__max'], grouping=True),locale.currency(agg['amount__avg'], grouping=True)
	return render_to_response('tracker/index.html', { 'count' : count, 'total' : total, 'mx' : mx, 'av' : av })
	
def challengeindex(request):
	challenges = Challenge.objects.values('challengeId', 'name', 'goal', 'speedRun__name').order_by('speedRun__name').annotate(Sum('challengebid__amount'))
	return render_to_response('tracker/challengeindex.html', { 'challenges' : challenges })
	
def choiceindex(request):
	choices = Choice.objects.values('choiceId', 'name', 'speedRun__speedRunId', 'speedRun__name', 'choiceoption__optionId', 'choiceoption__name').order_by('speedRun__name','name','choiceoption__name').annotate(Sum('choiceoption__choicebid__amount'))
	return render_to_response('tracker/choiceindex.html', { 'choices' : choices })
	
def choice(request,id):
	choice = Choice.objects.get(pk=id)
	options = ChoiceOption.objects.filter(choice__exact=id).annotate(Sum('choicebid__amount'), Count('choicebid__amount'))
	print choice
	print options
	return render_to_response('tracker/choice.html', { 'choice' : choice, 'options' : options })
		
def choiceoption(request,id):
	choiceoption = ChoiceOption.objects.get(pk=id)
	choicebids = ChoiceBid.objects.values('donationId', 'donationId__donorId', 'donationId__donorId__firstName','donationId__donorId__lastName', 'amount', 'donationId__timeReceived').filter(optionId__exact=id).order_by('donationId__timeReceived')
	print choiceoption
	print choicebids
	return render_to_response('tracker/choiceoption.html', { 'choiceoption' : choiceoption, 'choicebids' : choicebids })
	
def donorindex(request):
	locale.setlocale( locale.LC_ALL, '')
	donors = Donor.objects.all().filter(lastName__isnull=False).order_by('lastName', 'firstName').annotate(Sum('donation__amount'), Count('donation__amount'), Max('donation__amount'), Avg('donation__amount'))
	return render_to_response('tracker/donorindex.html', { 'donors' : donors })
	
def donor(request,id):
	locale.setlocale( locale.LC_ALL, '')
	donor = Donor.objects.get(pk=id)
	donations = Donation.objects.filter(donorId__exact=id)
	agg = donations.aggregate(Sum('amount'), Count('amount'), Max('amount'), Avg('amount'))
	total,mx,av = locale.currency(agg['amount__sum'], grouping=True),locale.currency(agg['amount__max'], grouping=True),locale.currency(agg['amount__avg'], grouping=True)
	return render_to_response('tracker/donor.html', { 'donor' : donor, 'donations' : donations, 'agg' : agg, 'total' : total, 'mx' : mx, 'av' : av })
	
def donationindex(request):
	return index(request)

def donation(request,id):
	donation = Donation.objects.get(pk=id)
	return render_to_response('tracker/donation.html', { 'donation' : donation })
	
def gameindex(request):
	return index(request)

def game(request,id):
	return index(request)