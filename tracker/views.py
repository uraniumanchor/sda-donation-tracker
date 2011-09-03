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
	
