import os
os.environ["DJANGO_SETTINGS_MODULE"]= "newlouslist.settings"

import django
django.setup()

from django.test import TestCase
from django.test import override_settings
from django.urls import reverse
from django.contrib.auth.models import User
from django.utils import timezone
from http import HTTPStatus
from django.http import HttpRequest
from . import views
from .models import TimeTable, UserProfile

# Create your tests here.
# received guidance from https://stackoverflow.com/questions/46449463/django-test-client-submitting-a-form-with-a-post-request
# for figuring out how to submit a form in testing suite and verify it works 

# TODO: make this test access to pages
class TestScheduleView(TestCase):
    def test_file(self):
        assert 1==1