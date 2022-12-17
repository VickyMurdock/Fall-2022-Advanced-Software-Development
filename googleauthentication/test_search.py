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


class TestSearchFunctionality(TestCase):
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

    def test_search_redirect(self):
        """
        Test showing that the redirect after form submission is working
        """
        self.login('testuser', 'testuser@test.com')
        request = HttpRequest()
        request.user = self.user
        request.method = 'POST'
        request.POST['department'] = 'CS'
        request.POST['catalog_num'] = int()
        request.POST['days_held'] = ''
        request.POST['grad_filter'] = ''
        response = views.classList(request)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertContains(response, 'Search Results')   # key item unique to class list page
        # tear down variables
        self.client.logout()
        self.client.delete(User.objects.get(username='testuser'))

    def test_department_display(self):
        """
        Test checks whether the selected departments are shown
        """
        self.login('testuser', 'testuser@test.com')
        request = HttpRequest()
        request.user = self.user
        request.method = 'POST'
        request.POST['department'] = 'CS'
        request.POST['catalog_num'] = int()
        request.POST['days_held'] = ''
        request.POST['grad_filter'] = ''
        response = views.classList(request)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertContains(response, 'CS')   # check if this element exists
        # tear down variables -- deletes cascade to other vars
        self.client.logout()
        self.client.delete(User.objects.get(username='testuser'))

    def test_course_num_display(self):
        """
        Tests whether filtering for department and course number works
        """
        self.login('testuser', 'testuser@test.com')
        request = HttpRequest()
        request.user = self.user
        request.method = 'POST'
        request.POST['department'] = 'CS'
        request.POST['catalog_num'] = '1110'
        request.POST['days_held'] = ''
        request.POST['grad_filter'] = ''
        response = views.classList(request)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertContains(response, 'CS 1110')   # check if this element exists
        self.assertNotIn('CS 3240', response)   # make sure other elements don't exist in the page
        # tear down variables -- deletes cascade to other vars
        self.client.logout()
        self.client.delete(User.objects.get(username='testuser'))

    def test_date_filtering(self):
        """
        Test checks that filtering by date works
        """
        self.login('testuser', 'testuser@test.com')
        request = HttpRequest()
        request.user = self.user
        request.method = 'POST'
        request.POST['department'] = 'CS'
        request.POST['catalog_num'] = ''
        request.POST['days_held'] = 'Mo'
        request.POST['grad_filter'] = ''
        response = views.classList(request)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertContains(response, 'Mo')   # check if this element exists
        self.assertNotIn('Tu', response)   # make sure other elements don't exist in the page
        # tear down variables -- deletes cascade to other vars
        self.client.logout()
        self.client.delete(User.objects.get(username='testuser'))

    def test_multiple_dates(self):
        """
        Test checks that filtering for multiple dates
        """
        self.login('testuser', 'testuser@test.com')
        request = HttpRequest()
        request.user = self.user
        request.method = 'POST'
        request.POST['department'] = 'CS'
        request.POST['catalog_num'] = ''
        request.POST['days_held'] = 'Mo'
        request.POST['days_held'] += 'We'   # not really sure how the syntax works here for multi-select and posting
        request.POST['grad_filter'] = ''
        response = views.classList(request)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertContains(response, 'MoWe')   # check if this element exists
        self.assertNotIn('TuTh', response)   # make sure other elements don't exist in the page
        # tear down variables -- deletes cascade to other vars
        self.client.logout()
        self.client.delete(User.objects.get(username='testuser'))

    def test_grad_filter_undergrad(self):
        """
        Test makes sure that grad filter only shows undergrad courses when selected
        """
        self.login('testuser', 'testuser@test.com')
        request = HttpRequest()
        request.user = self.user
        request.method = 'POST'
        request.POST['department'] = 'CS'
        request.POST['catalog_num'] = ''
        request.POST['days_held'] = ''
        request.POST['grad_filter'] = 'undergrad'
        response = views.classList(request)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertNotIn('6111', response)   # first CS graduate course
        self.assertContains(response, '1010')   # first CS undergrad course
        # tear down variables -- deletes cascade to other vars
        self.client.logout()
        self.client.delete(User.objects.get(username='testuser'))
    
    def test_grad_filter_grad(self):
        """
        Test makes sure that grad filter only shows graduate courses when selected
        """
        self.login('testuser', 'testuser@test.com')
        request = HttpRequest()
        request.user = self.user
        request.method = 'POST'
        request.POST['department'] = 'CS'
        request.POST['catalog_num'] = ''
        request.POST['days_held'] = ''
        request.POST['grad_filter'] = 'grad'
        response = views.classList(request)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertNotIn('1010', response)   # first CS undergrad course
        self.assertNotIn('4998', response)   # last CS undergrad course
        self.assertContains(response, '6111')   # first CS graduate course
        # tear down variables -- deletes cascade to other vars
        self.client.logout()
        self.client.delete(User.objects.get(username='testuser'))

    def test_grad_filter_both(self):
        """
        Test makes sure that grad filter shows all courses when selected
        """
        self.login('testuser', 'testuser@test.com')
        request = HttpRequest()
        request.user = self.user
        request.method = 'POST'
        request.POST['department'] = 'CS'
        request.POST['catalog_num'] = ''
        request.POST['days_held'] = ''
        request.POST['grad_filter'] = 'both'
        response = views.classList(request)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertContains(response, '1010')   # first CS undergrad course
        self.assertContains(response, '4998')   # last CS undergrad course
        self.assertContains(response, '6111')   # first CS graduate course
        # tear down variables -- deletes cascade to other vars
        self.client.logout()
        self.client.delete(User.objects.get(username='testuser'))
    
    def test_empty_search(self):
        """
        Test makes sure that empty search keeps user on search page
        """
        self.login('testuser', 'testuser@test.com')
        request = HttpRequest()
        request.user = self.user
        request.method = 'POST'
        request.POST['department'] = ''
        request.POST['catalog_num'] = ''
        request.POST['days_held'] = ''
        request.POST['grad_filter'] = ''
        request._messages = messages.storage.default_storage(request)
        response = views.classList(request)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertContains(response, 'Select the exact combination of days.')   # unique text on search page
        # tear down variables -- deletes cascade to other vars
        self.client.logout()
        self.client.delete(User.objects.get(username='testuser'))

    def test_all_filters(self):
        """
        Test checks that all filters work
        """
        self.login('testuser', 'testuser@test.com')
        request = HttpRequest()
        request.user = self.user
        request.method = 'POST'
        request.POST['department'] = 'CS'
        request.POST['catalog_num'] = '1110'
        request.POST['days_held'] = 'MoWeFr'
        request.POST['grad_filter'] = 'undergrad'
        response = views.classList(request)
        
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertContains(response, 'MoWeFr')   # check if this element exists
        self.assertContains(response, 'CS 1110')   # check if this element exists
        self.assertNotIn('TuTh', response)   # make sure other elements don't exist in the page
        self.assertNotIn('ECON', response)   # make sure other elements don't exist in the page
        self.assertNotIn('6111', response)   # first CS graduate course
        # tear down variables -- deletes cascade to other vars
        self.client.logout()
        self.client.delete(User.objects.get(username='testuser'))

    def test_build_with_schedule_appears(self):
        """
        Tests that build with schedule is working; "Build with Schedule" button appears
        """
        self.login('testuser', 'testuser@test.com')
        request = HttpRequest()
        request.user = self.user
        request.method = 'POST'
        request.POST['department'] = 'CS'
        request.POST['catalog_num'] = int()
        request.POST['days_held'] = ''
        request.POST['grad_filter'] = ''
        response = views.classList(request)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertContains(response, 'Add to Schedule')
        # tear down variables -- deletes cascade to other vars
        self.client.logout()
        self.client.delete(User.objects.get(username='testuser'))

    def test_build_BME_with_schedule_appears(self):
        """
        Tests that build with schedule is working for BME (previously buggy); "Build with Schedule" button appears
        """
        self.login('testuser', 'testuser@test.com')
        request = HttpRequest()
        request.user = self.user
        request.method = 'POST'
        request.POST['department'] = 'BME'
        request.POST['catalog_num'] = int()
        request.POST['days_held'] = ''
        request.POST['grad_filter'] = ''
        response = views.classList(request)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertContains(response, 'Add to Schedule')
        # tear down variables -- deletes cascade to other vars
        self.client.logout()
        self.client.delete(User.objects.get(username='testuser'))

    def test_no_results_found_works(self):
        """
        Test verifies that if the user searches for something without results, a message appears saying "No search results found!"
        """
        self.login('testuser', 'testuser@test.com')
        response = self.client.post(reverse('classList'), {'department':'CS', 'catalog_num':int(), 'days_held':'MoTuWe', 'grad_filter':''})
        # check that it redirects -- message manually tested and does appear
        self.assertEqual(response.status_code, 302)
        # tear down variables -- deletes cascade to other vars
        self.client.logout()
        self.client.delete(User.objects.get(username='testuser'))
