# Create your views here.
from django.shortcuts import render_to_response
from django.db.models import Sum
from donations.tracker.models import *
import django.shortcuts
import locale

def redirect(request):
	return django.shortcuts.redirect('tracker/')

def index(request):
	locale.setlocale( locale.LC_ALL, '')
	total = locale.currency(Donation.objects.aggregate(Sum('amount'))['amount__sum'], grouping=True)
	return render_to_response('tracker/index.html', { 'total' : total})
	
def challengeindex(request):
	challenges = Challenge.objects.values('challengeId', 'name', 'goal', 'speedRun__name').order_by('speedRun__name').annotate(Sum('challengebid__amount'))
	return render_to_response('tracker/challengeindex.html', { 'challenges' : challenges })
	
def choiceindex(request):
	choices = Choice.objects.values('choiceId', 'name', 'speedRun__name', 'choiceoption__name').order_by('speedRun__name','name','choiceoption__name').annotate(Sum('choiceoption__choicebid__amount'))
	return render_to_response('tracker/choiceindex.html', { 'choices' : choices })
		
