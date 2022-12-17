import os
os.environ["DJANGO_SETTINGS_MODULE"]= "newlouslist.settings"

import django
django.setup()

from django.test import TestCase
from django.test import override_settings
from django.urls import reverse
from django.contrib.auth.models import User

# Create your tests here.
# received guidance from https://stackoverflow.com/questions/46449463/django-test-client-submitting-a-form-with-a-post-request
# for figuring out how to submit a form in testing suite and verify it works 

class TestLogin(TestCase):
    def login(self, user, email):
        settings_manager = override_settings(SECURE_SSL_REDIRECT=False)
        settings_manager.enable()
        self.addCleanup(settings_manager.disable)
        # create user, log in
        self.user = User.objects.create_user(username=user, email=email, password='test123', pk=5)
        settings_manager = override_settings(SECURE_SSL_REDIRECT=False)
        settings_manager.enable()
        self.addCleanup(settings_manager.disable)
        self.client.login(username=user, password='test123')

    def test_google_appears_on_login(self):
        """
        Tests that allauth Google login package is working; sign-in button appears
        """
        settings_manager = override_settings(SECURE_SSL_REDIRECT=False)
        settings_manager.enable()
        self.addCleanup(settings_manager.disable)
        settings_manager = override_settings(SECURE_SSL_REDIRECT=False)
        settings_manager.enable()
        self.addCleanup(settings_manager.disable)
        response = self.client.get('/accounts/login/')
        self.assertContains(response, "Google")

    def test_login(self):
        """
        Tests that upon successful login, user's username appears on home page
        """
        settings_manager = override_settings(SECURE_SSL_REDIRECT=False)
        settings_manager.enable()
        self.addCleanup(settings_manager.disable)
        # create user, log in
        self.user = User.objects.create_user(username='TestUser', email='testuser@test.com', password='test123')
        settings_manager = override_settings(SECURE_SSL_REDIRECT=False)
        settings_manager.enable()
        self.addCleanup(settings_manager.disable)
        self.client.login(username='TestUser', password='test123')

        response = self.client.get(reverse('home'))
        self.assertContains(response, self.user.username)
        # tear down variables
        self.client.logout()
        self.client.delete(self.user)

    def test_not_signed_in(self):
        """
        Test checks that if the user isn't logged in, user has the option to sign in
        """
        # make sure no one is signed in
        settings_manager = override_settings(SECURE_SSL_REDIRECT=False)
        settings_manager.enable()
        self.addCleanup(settings_manager.disable)
        response = self.client.get(reverse('home'))
        self.assertContains(response, 'Login with Google')   # unique element to home page if user not signed in
