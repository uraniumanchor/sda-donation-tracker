from django.db import models
from django.contrib.auth.models import User

# Create your models here.

class Challenge(models.Model):
	speedRun = models.ForeignKey('SpeedRun',db_column='speedRun')
	name = models.CharField(max_length=64)
	goal = models.DecimalField(decimal_places=2,max_digits=20,db_column='goalAmount')
	description = models.TextField(max_length=1024,null=True,blank=True)
	bidState = models.CharField(max_length=255,choices=(('HIDDEN', 'Hidden'), ('OPENED','Opened'), ('CLOSED','Closed')))
	class Meta:
		db_table = 'Challenge'
		unique_together = ('speedRun','name')
	def __unicode__(self):
		return self.speedRun.name + ' -- ' + self.name
		
class ChallengeBid(models.Model):
	challenge = models.ForeignKey('Challenge',db_column='challenge')
	donation = models.ForeignKey('Donation',db_column='donation')
	amount = models.DecimalField(decimal_places=2,max_digits=20)
	class Meta:
		db_table = 'ChallengeBid'
		verbose_name = 'Challenge Bid'
		ordering = [ '-donation__timeReceived' ]
	def __unicode__(self):
		return unicode(self.challenge) + ' -- ' + unicode(self.donation)
		
class Choice(models.Model):
	speedRun = models.ForeignKey('SpeedRun',db_column='speedRun')
	name = models.CharField(max_length=64)
	description = models.TextField(max_length=1024,null=True,blank=True)
	bidState = models.CharField(max_length=255,choices=(('HIDDEN', 'Hidden'), ('OPENED','Opened'), ('CLOSED','Closed')))
	class Meta:
		db_table = 'Choice'
		unique_together = ('speedRun', 'name')
	def __unicode__(self):
		return self.speedRun.name + ' -- ' + self.name
		
class ChoiceBid(models.Model):
	choiceOption = models.ForeignKey('ChoiceOption',db_column='choiceOption')
	donation = models.ForeignKey('Donation',db_column='donation')
	amount = models.DecimalField(decimal_places=2,max_digits=20)
	class Meta:
		db_table = 'ChoiceBid'
		verbose_name = 'Choice Bid'
		ordering = [ 'choiceOption__choice__speedRun__name', 'choiceOption__choice__name' ]
	def __unicode__(self):
		return unicode(self.choiceOption) + ' (' + unicode(self.donation.donor) + ') (' + unicode(self.amount) + ')'

class ChoiceOption(models.Model):
	choice = models.ForeignKey('Choice',db_column='choice')
	name = models.CharField(max_length=64)
	class Meta:
		db_table = 'ChoiceOption'
		verbose_name = 'Choice Option'
		unique_together = ('choice', 'name')
	def __unicode__(self):
		return unicode(self.choice) + ' -- ' + self.name

class Donation(models.Model):
	donor = models.ForeignKey('Donor',db_column='donor')
	domain = models.CharField(max_length=255, choices=(('LOCAL', 'Local'), ('CHIPIN', 'ChipIn')))
	domainId = models.CharField(max_length=160,unique=True)
	bidState = models.CharField(max_length=255, choices=(('PENDING', 'Pending'), ('IGNORED', 'Ignored'), ('PROCESSED', 'Processed'), ('FLAGGED', 'Flagged')))
	readState = models.CharField(max_length=255, choices=(('PENDING', 'Pending'), ('IGNORED', 'Ignored'), ('READ', 'Read'), ('FLAGGED', 'Flagged')))
	commentState = models.CharField(max_length=255, choices=(('PENDING', 'Pending'), ('DENIED', 'Denied'), ('APPROVED', 'Approved'), ('FLAGGED', 'Flagged')))
	amount = models.DecimalField(decimal_places=2,max_digits=20)
	timeReceived = models.DateTimeField()
	comment = models.TextField(max_length=4096,null=True,blank=True)
	class Meta:
		db_table = 'Donation'
		permissions = (
			('view_full_list', 'Can view full donation list'),
		)
		get_latest_by = 'timeReceived'
		ordering = [ '-timeReceived' ]
	def __unicode__(self):
		return unicode(self.donorId) + ' (' + unicode(self.amount) + ') (' + unicode(self.timeReceived) + ')'
		
class Donor(models.Model):
	email = models.EmailField(max_length=128,unique=True)
	alias = models.CharField(max_length=32,unique=True,null=True,blank=True)
	firstName = models.CharField(max_length=32)
	lastName = models.CharField(max_length=32)
	class Meta:
		db_table = 'Donor'
		permissions = (
			('view_usernames', 'Can view full usernames'),
			('view_emails', 'Can view email addresses'),
		)
		ordering = ['lastName', 'firstName', 'email']
	def full(self):
		return unicode(self.email) + ' (' + unicode(self) + ')'
	def __unicode__(self):
		ret = unicode(self.lastName) + ', ' + unicode(self.firstName)
		if self.alias and len(self.alias) > 0:
			ret += ' (' + unicode(self.alias) + ')'
		return ret
		
class Prize(models.Model):
	name = models.CharField(max_length=64,unique=True)
	sortKey = models.IntegerField(db_index=True)
	image = models.URLField(max_length=1024,db_column='imageURL',null=True,blank=True)
	description = models.TextField(max_length=1024,null=True,blank=True)
	minimumBid = models.DecimalField(decimal_places=2,max_digits=20,default=5.0)
	startGame = models.ForeignKey('SpeedRun',db_column='startGame',related_name='prizeStart')
	endGame = models.ForeignKey('SpeedRun',db_column='endGame',related_name='prizeEnd')
	winner = models.ForeignKey('Donor',db_column='winner')
	class Meta:
		db_table = 'Prize'
		ordering = [ 'sortKey', 'name' ]
	def __unicode__(self):
		return unicode(self.name)
		
class SpeedRun(models.Model):
	name = models.CharField(max_length=64,unique=True)
	runners = models.CharField(max_length=1024)
	sortKey = models.IntegerField(db_index=True)
	description = models.TextField(max_length=1024)
	startTime = models.DateTimeField()
	endTime = models.DateTimeField()
	class Meta:
		db_table = 'SpeedRun'
		verbose_name = 'Speed Run'
		ordering = [ 'sortKey' ]
	def __unicode__(self):
		return unicode(self.name)
		
class UserProfile(models.Model):
	user = models.ForeignKey(User, unique=True)
	prepend = models.CharField('Template Prepend', max_length=64,blank=True)
	class Meta:
		verbose_name = 'User Profile'
		permissions = (
			('show_rendertime', 'Can view page render times'),
		)
	def __unicode__(self):
		return unicode(self.user)
	