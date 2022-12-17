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


class TestPersonalInformation(TestCase):
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
    
    def test_default_info_shows(self):
        """
        Test case tests that default information (username, email) is shown on the page, regardless of whether other information has been added
            to the UserProfile database
        """
        self.login('testuser', 'testuser@test.com')   # logs in to page with username='testuser' and email='testuser@test.com'
        response = self.client.get(reverse('myInfo'))
        self.assertContains(response, "testuser")
        self.assertContains(response, 'testuser@test.com')
        # tear down variables
        self.client.logout()
        self.client.delete(User.objects.get(username='testuser'))

    def test_year_update_updates_UserProfile(self):
        """
        Test case tests that in the case the user updates their year from the dropdown menu, that year is populated to the database and shows up on the 
            personal information page
        """
        self.login('testuser', 'testuser@test.com')
        response = self.client.post(reverse('myInfo'), {'year':'Fourth Year', 'major':"", 'minor':"", 'bio':""})
        profile = UserProfile.objects.get(user=5)
        self.assertContains(response, 'Fourth Year')   # checks that fourth year appears on site
        self.assertEquals(profile.year, 'Fourth Year')  # checks that database was updated
        # tear down variables
        self.client.logout()
        self.client.delete(User.objects.get(username='testuser'))
    
    def test_major_update_updates_UserProfile(self):
        """
        Test case tests that in the case the user updates their major as text input, that major is populated to the database and shows up on the 
            personal information page
        """
        self.login('testuser', 'testuser@test.com')
        response = self.client.post(reverse('myInfo'), {'year':"", 'major':"Computer Science", 'minor':"", 'bio':""})
        profile = UserProfile.objects.get(user=5)
        self.assertContains(response, 'Computer Science')   # checks that 'Computer Science' appears on site
        self.assertEquals(profile.major, 'Computer Science')  # checks that database was updated
        # tear down variables
        self.client.logout()
        self.client.delete(User.objects.get(username='testuser'))

    def test_minor_update_updates_UserProfile(self):
        """
        Test case tests that in the case the user updates their minor as text input, that minor is populated to the database and shows up on the 
            personal information page
        """
        self.login('testuser', 'testuser@test.com')
        response = self.client.post(reverse('myInfo'), {'year':"", 'major':"", 'minor':"Art History", 'bio':""})
        profile = UserProfile.objects.get(user=5)
        self.assertContains(response, 'Art History')   # checks that 'Art History' appears on site
        self.assertEquals(profile.minor, 'Art History')  # checks that database was updated
        # tear down variables
        self.client.logout()
        self.client.delete(User.objects.get(username='testuser'))

    def test_bio_update_updates_UserProfile(self):
        """
        Test case tests that in the case the user updates their bio as text input, that bio is populated to the database and shows up on the 
            personal information page
        """
        self.login('testuser', 'testuser@test.com')
        response = self.client.post(reverse('myInfo'), {'year':"", 'major':"", 'minor':"", 'bio':"sample student biography"})
        profile = UserProfile.objects.get(user=5)
        self.assertContains(response, 'sample student biography')   # checks that 'sample student biography' appears on site
        self.assertEquals(profile.bio, 'sample student biography')  # checks that database was updated
        # tear down variables
        self.client.logout()
        self.client.delete(User.objects.get(username='testuser'))

    def test_input_saved_logging_back_in(self):
        """
        Test case tests that in the case the user updates their personal information and logs back in, their personal information is saved
        """
        self.login('testuser', 'testuser@test.com')
        response = self.client.post(reverse('myInfo'), {'year':"", 'major':"", 'minor':"", 'bio':"sample student biography"})
        self.client.logout()
        self.client.login(username='testuser', password='test123')
        profile = UserProfile.objects.get(user=5)
        self.assertContains(response, 'sample student biography')   # checks that 'sample student biography' appears on site
        self.assertEquals(profile.bio, 'sample student biography')  # checks that database retains updates
        # tear down variables
        self.client.logout()
        self.client.delete(User.objects.get(username='testuser'))

    def test_modal_updates_data(self):
        """
        Test case tests that in the case the user updates their personal information on the page, the database and page are updated accordingly
            (validates modal(s)) -- this should reflect all of them working because they are copies of their original code and reside in the HTML
        """
        self.login('testuser', 'testuser@test.com')
        response = self.client.post(reverse('myInfo'), {'year':"", 'major':"Computer Science", 'minor':"", 'bio':""})
        profile = UserProfile.objects.get(user=5)
        self.assertContains(response, 'Computer Science')   # checks that 'Computer Science' appears on site
        self.assertEquals(profile.major, 'Computer Science')  # checks that database was updated
        self.client.logout()
        self.login('testuser', 'testuser@test.com')
        response = self.client.post(reverse('myInfo'), {'year':"", 'major':"Psychology", 'minor':"", 'bio':""})
        profile = UserProfile.objects.get(user=5)
        self.assertContains(response, 'Psychology')   # checks that 'Computer Science' appears on site
        self.assertEquals(profile.major, 'Psychology')  # checks that database was updated
        # tear down variables
        self.client.logout()
        self.client.delete(User.objects.get(username='testuser'))

        
    def test_empty_update_input(self):
        """
        Test verifies that when user provides empty input, warning message appears.
        """
        self.login('testuser', 'testuser@test.com')
        response = self.client.post(reverse('myInfo'), {'year':"", 'major':"", 'minor':"", 'bio':""})
        profile = UserProfile.objects.get(user=5)
        self.assertContains(response, 'Empty input: If updating, please enter items into an input field.')   # checks that warning banner appears on site
        # tear down variables
        self.client.logout()
        self.client.delete(User.objects.get(username='testuser'))