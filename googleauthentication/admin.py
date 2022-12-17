from django.contrib import admin
from .models import TimeTable, UserProfile, Comment, Friends, Course

# Register your models here.
admin.site.register(TimeTable)
admin.site.register(UserProfile)
admin.site.register(Course)
admin.site.register(Comment)
admin.site.register(Friends)