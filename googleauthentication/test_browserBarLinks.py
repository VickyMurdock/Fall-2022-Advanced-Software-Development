import os
os.environ["DJANGO_SETTINGS_MODULE"]= "newlouslist.settings"

import django
django.setup()

from django.test import TestCase
from django.urls import reverse
from http import HTTPStatus
from django.http import HttpRequest
from django.test import override_settings
from django.contrib.auth.models import User
from django.contrib.auth import get_user_model
from django.contrib import messages



from . import views

# Create your tests here.
# received guidance from https://stackoverflow.com/questions/46449463/django-test-client-submitting-a-form-with-a-post-request
# for figuring out how to submit a form in testing suite and verify it works 

# TODO: fix bug


class TestBrowserBarLinks(TestCase):
    def login(self, username, emailtext):
        settings_manager = override_settings(SECURE_SSL_REDIRECT=False)
        settings_manager.enable()
        self.addCleanup(settings_manager.disable)
        # create user, log in
        self.user = User.objects.create_user(username=username, email=emailtext, password='test123', pk=5)
        settings_manager = override_settings(SECURE_SSL_REDIRECT=False)
        settings_manager.enable()
        self.addCleanup(settings_manager.disable)
        self.client.login(username=username, password='test123')
        
    def test_redirect_browser_bar(self):
        """
        Test showing that the redirect after brower bar link click is working
        """
        self.login('testuser', 'testuser@test.com')
        request = HttpRequest()
        request.user = self.user
        request.method = 'POST'
        request.POST['department'] = 'CS'
        response = views.classList(request)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertContains(response, 'Search Results')   # key item unique to class list page
        # tear down variables
        self.client.logout()
        self.client.delete(User.objects.get(username='testuser'))
        
    def test_correct_class_browser_bar(self):
        self.login('testuser', 'testuser@test.com')
        request = HttpRequest()
        request.user = self.user
        request.method = 'POST'
        request.POST['department'] = 'MUSI'
        response = views.classList(request)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertContains(response, 'Basic Musical Skills')   # key item unique to class list page
        # tear down variables
        self.client.logout()
        self.client.delete(User.objects.get(username='testuser'))
        