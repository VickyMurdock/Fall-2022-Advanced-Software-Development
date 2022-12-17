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
from .models import TimeTable, UserProfile, Comment, Course, Friends
from django.contrib.auth import get_user_model
from django.contrib import messages



from . import views

# Create your tests here.
# received guidance from https://stackoverflow.com/questions/46449463/django-test-client-submitting-a-form-with-a-post-request
# for figuring out how to submit a form in testing suite and verify it works 

class TestFriendsFunctionality(TestCase):
    def login(self, username, emailtext, pk):
        settings_manager = override_settings(SECURE_SSL_REDIRECT=False)
        settings_manager.enable()
        self.addCleanup(settings_manager.disable)
        # create user, log in
        self.user = User.objects.create_user(username=username, email=emailtext, password='test123', pk=pk)
        settings_manager = override_settings(SECURE_SSL_REDIRECT=False)
        settings_manager.enable()
        self.addCleanup(settings_manager.disable)
        self.client.login(username=username, password='test123')
    
    def test_friends_appear_in_search(self):
        """
        Test confirms that all users are included in friends' search dropdown menu
        """
        self.login('testuser', 'testuser@test.com', 3)
        self.client.logout()
        self.login('testuser2', 'testuser2@test.com', 4)
        self.client.logout()
        self.login('testuser3', 'testuser3@test.com', 5)

        response = self.client.get(reverse('friends'))
        for profile in UserProfile.objects.all():
            self.assertContains(response, profile.name)   # check that all users are included in list 

        self.client.logout()
        # tear down variables - should remove associated variables
        self.client.delete(User.objects.get(username='testuser')) 
        self.client.delete(User.objects.get(username='testuser2'))
        self.client.delete(User.objects.get(username='testuser3'))

    def test_added_friends_appear(self):
        """
        Test validates that friends who are added appear in the "My Friends" list
        """
        # create users
        self.login('testuser', 'testuser@test.com', 3)
        self.client.logout()
        self.login('testuser2', 'testuser2@test.com', 4)
        self.client.logout()
        self.login('testuser3', 'testuser3@test.com', 5)
        response = self.client.post(reverse('friends'), {'current_user': 'testuser3', 'friend_search': 'testuser2'})
        self.assertContains(response, 'testuser2') 
        self.client.logout()
        # tear down variables - should remove associated variables
        self.client.delete(User.objects.get(username='testuser')) 
        self.client.delete(User.objects.get(username='testuser2'))
        self.client.delete(User.objects.get(username='testuser3'))

    def test_friends_schedule_link_works(self):
        """
        Test verifies that clicking on an added friend button navigates the user to that friend's schedule page and comment section
        """
        self.login('testuser', 'testuser@test.com', 3)
        self.client.logout()
        self.login('testuser2', 'testuser2@test.com', 4)
        # have test user register for a course
        response = self.client.post(reverse('schedule'), {'course_name':"CS 1110: Intro to Programming", "course_section":"001", 
            "course_component":"LEC", "course_units":3, "course_instructor":"Raymond Pettit", "days":"MoWeFr", "times":"02:00-02:50PM", "location":"Gilmer Hall 301"})  
        self.client.logout()
        self.login('testuser3', 'testuser3@test.com', 5)
        self.client.post(reverse('friends'), {'current_user': 'testuser3', 'friend_search': 'testuser2'})  # add friend 
        response = self.client.post(reverse('friends_schedule'), {'friend_username':'testuser2'})   # navigate to friend's schedule page
        # assert statements
        self.assertContains(response, "testuser2's schedule")   # checks that unique text appears
        self.assertContains(response, "CS 1110: Intro to Programming")   # checks that added course appears
        self.assertContains(response, "Comments")   # checks that comment section appears
        self.client.logout()
        # tear down variables - should remove associated variables
        self.client.delete(User.objects.get(username='testuser')) 
        self.client.delete(User.objects.get(username='testuser2'))
        self.client.delete(User.objects.get(username='testuser3'))

    def test_comment_on_friends(self):
        """
        Test verifies that adding a comment to a friend's schedule is posted and saved to the database
        """
        self.login('testuser', 'testuser@test.com', 3)
        self.client.logout()
        self.login('testuser2', 'testuser2@test.com', 4)
        # have test user register for a course
        response = self.client.post(reverse('schedule'), {'course_name':"CS 1110: Intro to Programming", "course_section":"001", 
            "course_component":"LEC", "course_units":3, "course_instructor":"Raymond Pettit", "days":"MoWeFr", "times":"02:00-02:50PM", "location":"Gilmer Hall 301"})  
        self.client.logout()
        self.login('testuser3', 'testuser3@test.com', 5)
        self.client.post(reverse('friends'), {'current_user': 'testuser3', 'friend_search': 'testuser2'})  # add friend 
        self.client.post(reverse('friends_schedule'), {'friend_username':'testuser2'})   # navigate to friend's schedule page
        response = self.client.post(reverse('friends_schedule'), {'friend_username':'testuser2', 'posted_comment':'test comment!'})  # add comment
        # assert statement
        self.assertContains(response, 'test comment!')
        # tear down variables - should remove associated variables
        self.client.logout()
        self.client.delete(User.objects.get(username='testuser')) 
        self.client.delete(User.objects.get(username='testuser2'))
        self.client.delete(User.objects.get(username='testuser3'))


    def test_personal_schedule_comments(self):
        """
        Test verifies that comments posted to personal schedule page are posted and saved to the database.
        """
        self.login('testuser2', 'testuser2@test.com', 4)
        self.client.logout()
        self.login('testuser', 'testuser@test.com', 3)
        response = self.client.get(reverse('schedule'))
        # checks condition where no comments are made yet
        self.assertContains(response, "No comments here yet!")
        response = self.client.post(reverse('schedule'), {'friend_username':'testuser2', 'posted_comment':'Posting a comment here!'})
        # checks that comments show up
        self.assertContains(response, 'Posting a comment here!')
        # tear down variables - should remove associated variables
        self.client.logout()
        self.client.delete(User.objects.get(username='testuser')) 
        self.client.delete(User.objects.get(username='testuser2'))

    def test_commenter_to_schedule_form(self):
        """
        Test verifies that user who clicks on a commenter's username is navigated to their schedule
        """
        self.login('testuser2', 'testuser2@test.com', 4)
        self.client.logout()
        self.login('testuser', 'testuser@test.com', 3)
        response = self.client.get(reverse('schedule'))
        # post a comment
        self.client.post(reverse('schedule'), {'friend_username':'testuser2', 'posted_comment':'Posting a comment here!'})
        # go to commenter's schedule page
        self.client.logout()
        self.client.login(username='testuser2', password='test123')
        response = self.client.post(reverse('friends_schedule'), {'friend_username':'testuser'})
        self.assertContains(response, "testuser's schedule")   # check that we navigated to the correct page
        self.client.logout()
        # tear down variables - should remove associated variables
        self.client.delete(User.objects.get(username='testuser')) 
        self.client.delete(User.objects.get(username='testuser2'))

    def test_filter_info_message(self):
        """
        Test verifies that, when providing an empty search on the friends page, the user is notified that the empty search shows all friended users.
        """
        self.login('testuser', 'testuser@test.com', 3)
        response = self.client.post(reverse('friends'), {'current_user':'testuser', 'major':'', 'minor':'', 'year':''})
        self.assertContains(response, "An empty search will display all friends.")   # check that we navigated to the correct page
        #tear down
        self.client.logout()
        self.client.delete(User.objects.get(username='testuser')) 

    def test_filter_major(self):
        """
        Test verifies that the search results of friends are filtered by major when selected.
        """
        # create two users with different majors
        self.login('testuser', 'testuser@test.com', 3)
        firstprofile = UserProfile.objects.get(pk=3)
        firstprofile.major = 'Computer Science'
        firstprofile.save()
        self.client.logout()
        self.login('testuser2', 'testuser2@test.com', 4)
        secondprofile = UserProfile.objects.get(pk=4)
        secondprofile.major = 'Art History'
        secondprofile.save()
        # create user that will be checking
        self.login('testuser3', 'testuser3@test.com', 5)
        # add friends
        self.client.post(reverse('friends'), {'current_user': 'testuser3', 'friend_search': 'testuser'})
        self.client.post(reverse('friends'), {'current_user': 'testuser3', 'friend_search': 'testuser2'})
        # test input
        response = self.client.post(reverse('friends'), {'current_user':'testuser3', 'major':'Computer Science', 'minor':'', 'year':''})
        self.assertContains(response, "Computer Science")
        self.assertNotContains(response, "Art History")
        # tear down 
        self.client.logout()
        self.client.delete(User.objects.get(username='testuser')) 
        self.client.delete(User.objects.get(username='testuser2')) 
        self.client.delete(User.objects.get(username='testuser3')) 
    
    def test_filter_minor(self):
        """
        Test verifies that the search results of friends are filtered by minor when selected.
        """
        # create two users with different majors
        self.login('testuser', 'testuser@test.com', 3)
        firstprofile = UserProfile.objects.get(pk=3)
        firstprofile.minor = 'Environmental Science'
        firstprofile.save()
        self.client.logout()
        self.login('testuser2', 'testuser2@test.com', 4)
        secondprofile = UserProfile.objects.get(pk=4)
        secondprofile.minor = 'English'
        secondprofile.save()
        # create user that will be checking
        self.login('testuser3', 'testuser3@test.com', 5)
        # add friends
        self.client.post(reverse('friends'), {'current_user': 'testuser3', 'friend_search': 'testuser'})
        self.client.post(reverse('friends'), {'current_user': 'testuser3', 'friend_search': 'testuser2'})
        # test input
        response = self.client.post(reverse('friends'), {'current_user':'testuser3', 'major':'', 'minor':'English', 'year':''})
        self.assertContains(response, "English")
        self.assertNotContains(response, "Environmental Science")
        # tear down 
        self.client.logout()
        self.client.delete(User.objects.get(username='testuser')) 
        self.client.delete(User.objects.get(username='testuser2')) 
        self.client.delete(User.objects.get(username='testuser3')) 

    def test_filter_year(self):
        """
        Test verifies that the search results of friends are filtered by year when selected.
        """
        # create two users with different majors
        self.login('testuser', 'testuser@test.com', 3)
        firstprofile = UserProfile.objects.get(pk=3)
        firstprofile.year = 'First Year'
        firstprofile.save()
        self.client.logout()
        self.login('testuser2', 'testuser2@test.com', 4)
        secondprofile = UserProfile.objects.get(pk=4)
        secondprofile.year = 'Second Year'
        secondprofile.save()
        # create user that will be checking
        self.login('testuser3', 'testuser3@test.com', 5)
        # add friends
        self.client.post(reverse('friends'), {'current_user': 'testuser3', 'friend_search': 'testuser'})
        self.client.post(reverse('friends'), {'current_user': 'testuser3', 'friend_search': 'testuser2'})
        # test input
        response = self.client.post(reverse('friends'), {'current_user':'testuser3', 'major':'', 'minor':'', 'year':'Second Year'})
        self.assertContains(response, "Second Year\n")
        self.assertNotContains(response, "First Year\n")
        # tear down 
        self.client.logout()
        self.client.delete(User.objects.get(username='testuser')) 
        self.client.delete(User.objects.get(username='testuser2')) 
        self.client.delete(User.objects.get(username='testuser3')) 

    def test_combination_all(self):
        """
        Test verifies that outputs match all inputs
        """
        self.login('testuser', 'testuser@test.com', 3)
        firstprofile = UserProfile.objects.get(pk=3)
        firstprofile.major = 'Undeclared'
        firstprofile.minor = 'Art History'
        firstprofile.year = 'First Year'
        firstprofile.save()
        self.client.logout()
        self.login('testuser2', 'testuser2@test.com', 4)
        secondprofile = UserProfile.objects.get(pk=4)
        secondprofile.major = 'Computer Science'
        secondprofile.minor = 'Data Science'
        secondprofile.year = 'Second Year'
        secondprofile.save()
        # create user that will be checking
        self.login('testuser3', 'testuser3@test.com', 5)
        # add friends
        self.client.post(reverse('friends'), {'current_user': 'testuser3', 'friend_search': 'testuser'})
        self.client.post(reverse('friends'), {'current_user': 'testuser3', 'friend_search': 'testuser2'})
        # test input
        response = self.client.post(reverse('friends'), {'current_user':'testuser3', 'major':'Computer Science', 'minor':'Data Science', 'year':'Second Year'})
        self.assertContains(response, "testuser2")
        self.assertContains(response, 'Computer Science')
        self.assertContains(response, 'Data Science')
        self.assertContains(response, 'Second Year\n')
        self.assertNotContains(response, "First Year\n")
        # tear down 
        self.client.logout()
        self.client.delete(User.objects.get(username='testuser')) 
        self.client.delete(User.objects.get(username='testuser2')) 
        self.client.delete(User.objects.get(username='testuser3')) 


    def test_no_results_text(self):
        """
        Test verifies that if there are no results, the text appears in results location saying "No results found! Add friends or change your filtering."
        """
        # create two users with different majors
        self.login('testuser', 'testuser@test.com', 3)
        firstprofile = UserProfile.objects.get(pk=3)
        firstprofile.year = 'First Year'
        firstprofile.save()
        self.client.logout()
        self.login('testuser2', 'testuser2@test.com', 4)
        secondprofile = UserProfile.objects.get(pk=4)
        secondprofile.year = 'Second Year'
        secondprofile.save()
        # create user that will be checking
        self.login('testuser3', 'testuser3@test.com', 5)
        # add friends
        self.client.post(reverse('friends'), {'current_user': 'testuser3', 'friend_search': 'testuser'})
        self.client.post(reverse('friends'), {'current_user': 'testuser3', 'friend_search': 'testuser2'})
        # test input
        response = self.client.post(reverse('friends'), {'current_user':'testuser3', 'major':'', 'minor':'', 'year':'Fourth Year'})
        self.assertContains(response, "No results found! Add friends or change your filtering.")
        # tear down 
        self.client.logout()
        self.client.delete(User.objects.get(username='testuser')) 
        self.client.delete(User.objects.get(username='testuser2')) 
        self.client.delete(User.objects.get(username='testuser3')) 
