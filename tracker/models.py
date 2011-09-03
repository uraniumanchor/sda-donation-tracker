from django.db import models

# Create your models here.

class BidState(models.Model):
	bidStateId = models.CharField(primary_key=True,max_length=16,unique=True,db_column='bidStateId')
	class Meta:
		db_table = 'BidState'
		verbose_name = 'Bid State'
	def __unicode__(self):
		return str(self.bidStateId)

class Challenge(models.Model):
	challengeId = models.IntegerField(primary_key=True,editable=False)
	speedRun = models.ForeignKey('SpeedRun',db_column='speedRunId')
	name = models.CharField(max_length=64)
	goal = models.DecimalField(decimal_places=2,max_digits=20,db_column='goalAmount')
	description = models.TextField(max_length=1024)
	#bidState = models.ForeignKey('BidState',db_column='bidState')
	class Meta:
		db_table = 'Challenge'
		unique_together = ('speedRun','name')
	def __unicode__(self):
		return self.speedRun.name + ' -- ' + self.name
		
class ChallengeBid(models.Model):
	challengeBidId = models.IntegerField(primary_key=True,editable=False)
	challenge = models.ForeignKey('Challenge',db_column='challengeId')
	donation = models.ForeignKey('Donation',db_column='donationId')
	amount = models.DecimalField(decimal_places=2,max_digits=20)
	class Meta:
		db_table = 'ChallengeBid'
		verbose_name = 'Challenge Bid'
		ordering = [ '-donation__timeReceived' ]
	def __unicode__(self):
		return str(self.challenge) + ' -- ' + str(self.donation)
		
class Choice(models.Model):
	choiceId = models.IntegerField(primary_key=True,editable=False)
	speedRun = models.ForeignKey('SpeedRun',db_column='speedRunId')
	name = models.CharField(max_length=64)
	description = models.TextField(max_length=1024)
	#bidState = models.ForeignKey('BidState',db_column='bidState')
	class Meta:
		db_table = 'Choice'
		unique_together = ('speedRun', 'name')
	def __unicode__(self):
		return self.speedRun.name + ' -- ' + self.name
		
class ChoiceBid(models.Model):
	choiceBidId = models.IntegerField(primary_key=True,editable=False)
	optionId = models.ForeignKey('ChoiceOption',db_column='optionId')
	donationId = models.ForeignKey('Donation',db_column='donationId')
	amount = models.DecimalField(decimal_places=2,max_digits=20)
	class Meta:
		db_table = 'ChoiceBid'
	def __unicode__(self):
		return str(self.optionId) + ' ' + str(self.donationId) + ' (' + str(self.amount) + ')'

class ChoiceOption(models.Model):
	optionId = models.IntegerField(primary_key=True,editable=False)
	choice = models.ForeignKey('Choice',db_column='choiceId')
	name = models.CharField(max_length=64)
	class Meta:
		db_table = 'ChoiceOption'
		verbose_name = 'Choice Option'
		unique_together = ('choice', 'name')
	def __unicode__(self):
		return str(self.choice) + ' -- ' + self.name

class Donation(models.Model):
	donationId = models.IntegerField(primary_key=True,editable=False)
	donorId = models.ForeignKey('Donor',db_column='donorId')
	domain = models.ForeignKey('DonationDomain',db_column='domain')
	domainId = models.CharField(max_length=160,unique=True)
	bidState = models.ForeignKey('DonationBidState',db_column='bidState')
	readState = models.ForeignKey('DonationReadState',db_column='readState')
	amount = models.DecimalField(decimal_places=2,max_digits=20)
	timeReceived = models.DateTimeField()
	comment = models.TextField(max_length=4096)
	class Meta:
		db_table = 'Donation'
		get_latest_by = 'timeReceived'
		ordering = [ '-timeReceived' ]
	def __unicode__(self):
		return str(self.donorId) + ' (' + str(self.amount) + ') (' + str(self.timeReceived) + ')'
		
class DonationBidState(models.Model):
	donationBidStateId = models.CharField(primary_key=True,max_length=16,unique=True)
	class Meta:
		db_table = 'DonationBidState'
		verbose_name = 'Donation Bid State'
	def __unicode__(self):
		return self.donationBidStateId
		
class DonationDomain(models.Model):
	donationDomainId = models.CharField(primary_key=True,max_length=16,unique=True)
	class Meta:
		db_table = 'DonationDomain'
		verbose_name = 'Donation Domain'
	def __unicode__(self):
		return self.donationDomainId
		
class DonationReadState(models.Model):
	donationReadStateId = models.CharField(primary_key=True,max_length=16,unique=True)
	class Meta:
		db_table = 'DonationReadState'
		verbose_name = 'Donation Read State'
	def __unicode__(self):
		return self.donationReadStateId
		
class Donor(models.Model):
	donorId = models.IntegerField(primary_key=True,editable=False)
	email = models.EmailField(max_length=128,unique=True)
	alias = models.CharField(max_length=32,unique=True)
	firstName = models.CharField(max_length=32)
	lastName = models.CharField(max_length=32)
	class Meta:
		db_table = 'Donor'
	def full(self):
		return str(self.email) + ' (' + str(self) + ')'
	def __unicode__(self):
		return str(self.lastName) + ', ' + str(self.firstName)
		
class Prize(models.Model):
	prizeId = models.IntegerField(primary_key=True,editable=False)
	name = models.CharField(max_length=64,unique=True)
	image = models.URLField(max_length=1024,db_column='imageURL')
	description = models.TextField(max_length=1024)
	donor = models.ForeignKey('Donor',db_column='donorId')
	class Meta:
		db_table = 'Prize'
	def __unicode__(self):
		return str(self.name)
		
class SpeedRun(models.Model):
	speedRunId = models.IntegerField(primary_key=True,editable=False)
	name = models.CharField(max_length=64,unique=True)
	description = models.TextField(max_length=1024)
	class Meta:
		db_table = 'SpeedRun'
		verbose_name = 'Speed Run'
	def __unicode__(self):
		return str(self.name)