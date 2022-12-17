from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
from django.contrib.auth import get_user_model
# from multiselectfield import MultiSelectField
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

# Create your models here.
@receiver(pre_save, sender=User)
def update_username_from_email(sender, instance, **kwargs):
	"""
	Method taken from stackoverflow to resolve google authentication issue
	Title: "django-allauth set username the same as email"
	URL: https://stackoverflow.com/questions/27348705/django-allauth-set-username-the-same-as-email
	"""
	user_email = instance.email
	username = user_email.split('@')[0]   # edited this from source code
	n = 1
	while User.objects.exclude(pk=instance.pk).filter(username=username).exists():
		n += 1
		username = user_email[:(29 - len(str(n)))] + '-' + str(n)
	instance.username = username
	

# User Profile Data
class UserProfile(models.Model):
	user = models.OneToOneField(User, primary_key=True, verbose_name='user', related_name='profile', on_delete=models.CASCADE)
	name = models.CharField(max_length=30, blank=True, null=True)
	year = models.CharField(max_length=20, blank=True, null=True)   # added this field
	major = models.CharField(max_length=50, blank=True, null=True)   # added this field
	minor = models.CharField(max_length=50, blank=True, null=True)   # added this field 
	bio = models.TextField(max_length=500, blank=True, null=True)
	notes = models.TextField(max_length=500, blank=True, null=True)
	picture = models.ImageField(upload_to='uploads/profile_pictures', default='uploads/profile_pictures/default.png', blank=True)


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
	if created:
		UserProfile.objects.create(user=instance)
	if not instance.is_staff:
		profile = UserProfile.objects.get(user=instance.pk)
		profile.name = instance.username
		profile.save()
		#TimeTable.objects.create(author=instance)

# @receiver(post_save, sender=User)
# def save_user_profile(sender, instance, **kwargs):
# 	instance.profile.save()
# 	#instance.timetable.save()


# Friends
class Friends(models.Model):
	user_id = models.ForeignKey(to=UserProfile, related_name="following", on_delete=models.CASCADE)
	friend_profile = models.ForeignKey(to=UserProfile, related_name="profile", on_delete=models.CASCADE)   # to get friend profile data
	friends_id = models.CharField(max_length = 120, blank=True, null=True)
	friend_username = models.CharField(max_length = 120, blank=True, null=True)
	# friends_id = models.ForeignKey(to=UserProfile, related_name="followers", on_delete=models.CASCADE)
	# status: Can be used when implementing REQUESTS - IDLE/REQUESTED/ACCEPTED/BLOCK
	# status = models.TextField(max_length=15, default="IDLE")
	class Meta:
		unique_together = ('user_id', 'friends_id',)

# schedule data
class TimeTable(models.Model):
	# Store user_id to connect user table to TimeTable
	# user_id = models.CharField(max_length=100, primary_key=True)
	created_on = models.DateTimeField(default=timezone.now)
	author = models.ForeignKey(User, default="", on_delete=models.CASCADE)

# Post Comment Data
class Comment(models.Model):
	author = models.ForeignKey(User, related_name='user_comments', on_delete=models.CASCADE)
	associated_schedule = models.ForeignKey(to=TimeTable, related_name='post_comments', on_delete=models.CASCADE)
	comment_text = models.TextField(max_length=500, default="")
	created_on = models.DateTimeField(default=timezone.now)
 	# timetable = models.ForeignKey('TimeTable', on_delete=models.CASCADE)   <-- probably root of the isse

# individual course data (child relationship to schedule data)
class Course(models.Model):
	timetable = models.ForeignKey(to=TimeTable, related_name='courses', on_delete=models.CASCADE)    # double check if this is the right code for that
	name = models.TextField(max_length=80, default="")
	section = models.TextField(max_length=5, default="")
	topic = models.TextField(max_length=80, default="")
	component = models.TextField(max_length=5, default="")
	units = models.TextField(max_length=1, default="")
	instructor = models.TextField(max_length=30, default="")
	days = models.TextField(max_length=10, default="")
	times = models.TextField(max_length=30, default="")
	location = models.TextField(max_length=30, default="")


@receiver(post_save, sender=get_user_model())
def create_user_timetable(sender, instance, created, **kwargs):
	if created:
		TimeTable.objects.create(author=instance)

# @receiver(post_save, sender=User)
# def save_user_profile(sender, instance, **kwargs):
# 	instance.timetable.save()