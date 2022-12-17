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
from .models import TimeTable, UserProfile, Course

# Create your tests here.
# received guidance from https://stackoverflow.com/questions/46449463/django-test-client-submitting-a-form-with-a-post-request
# for figuring out how to submit a form in testing suite and verify it works 

# Placeholder
class TestPlaceholder(TestCase):
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
    
    def test_remove_button(self):
        """
        Test checks that when user clicks "remove from schedule" from the schedule page, the course is removed from that page and the associated TimeTable
        """
        self.login('testuser', 'testuser@test.com')
        profile = UserProfile.objects.get(user=5)
        timetable = TimeTable.objects.get(author=5)
        # create course to add to database
        Course.objects.create(timetable=timetable, name="CS 1110: Intro to Programming", section="001", topic="", component="LEC", units=3, instructor="Raymond Pettit", days="MoWeFr", times="02:00-02:50PM", location="Gilmer Hall 301")
        # checking that the course shows up initially
        response = self.client.get(reverse('schedule'))
        self.assertContains(response, 'CS 1110: Intro to Programming')
        self.assertEqual(True, timetable.courses.filter(name="CS 1110: Intro to Programming").exists())    # check if class exists in the database
        # check that course no longer shows up
        response = self.client.post(reverse('schedule'), {'course_name':'CS 1110: Intro to Programming', 'course_section': '001', 'delete_bool':'True'})
        self.assertNotContains(response, 'CS 1110: Intro to Programming')
        self.assertEqual(False, timetable.courses.filter(name="CS 1110: Intro to Programming").exists())    # check that class no longer exists in the database
        # tear down variables
        self.client.logout()
        self.client.delete(User.objects.get(username='testuser'))

    def test_schedule_contains_all_courses(self):
        """
        Test checks that when user adds mulitple courses from the schedule page, all of the courses are included on the page and the associated TimeTable
        """
        self.login('testuser', 'testuser@test.com')
        profile = UserProfile.objects.get(user=5)
        timetable = TimeTable.objects.get(author=5)
        # create course to add to database
        Course.objects.create(timetable=timetable, name="CS 1110: Intro to Programming", section="001", topic="", component="LEC", units=3, instructor="Raymond Pettit", days="MoWeFr", times="02:00-02:50PM", location="Gilmer Hall 301")
        Course.objects.create(timetable=timetable, name="ECON 2010: Principles of Economics: Microeconomics", section="090", topic="", component="LEC", units=3, instructor="Kenneth Elzinga", days="TuTh", times="12:30-01:45PM", location="Chemistry Bldg 402")
        # checking that the course shows up initially
        response = self.client.get(reverse('schedule'))
        self.assertContains(response, 'CS 1110: Intro to Programming')
        self.assertEqual(True, timetable.courses.filter(name="CS 1110: Intro to Programming").exists())    # check if class exists in the database
        self.assertContains(response, 'ECON 2010: Principles of Economics: Microeconomics')
        self.assertEqual(True, timetable.courses.filter(name="ECON 2010: Principles of Economics: Microeconomics").exists())  # check if class exists in the database
        # tear down variables
        self.client.logout()
        self.client.delete(User.objects.get(username='testuser'))

    def test_schedule_wont_add_duplicate_course(self):
        """
        Test should validate appropriate behavior when adding a duplicate course (not a special topic). In this case, the user should be redirected
        to the search page, see a message saying "Class is a duplicate or conflicts with an existing class time.", and the system should not add the 
        course to the user's schedule.
        """
        self.login('testuser', 'testuser@test.com')
        profile = UserProfile.objects.get(user=5)
        timetable = TimeTable.objects.get(author=5)
        # create course to add to database
        Course.objects.create(timetable=timetable, name="CS 1110: Intro to Programming", section="001", topic="", component="LEC", units=3, instructor="Raymond Pettit", 
            days="MoWeFr", times="02:00PM-02:50PM", location="Gilmer Hall 301")
        # attempt to add this course
        response = self.client.post(reverse('schedule'), {'course_name':"CS 1110: Intro to Programming", "course_section":"002", 
                "days":"MoWeFr", "times":"12:00PM-12:50PM", "course_component":"LEC", "course_units":3, "course_instructor":"Briana Morrison", 
                "location":"Rice Hall 130"}) 
        # checking that the we redirect and get duplicate error
        self.assertContains(response, 'Class is a duplicate or conflicts with an existing class time.')
        self.assertEqual(1, len(timetable.courses.filter(name="CS 1110: Intro to Programming")))    # check if only one instance of CS 1110
        # tear down variables
        self.client.logout()
        self.client.delete(User.objects.get(username='testuser'))


    def test_schedule_wont_add_conflicting_time(self):
        """
        Test should validate appropriate behavior when adding a time-conflicting course. In this case, the user should be redirected
        to the search page, see a message saying "Class is a duplicate or conflicts with an existing class time.", and the system should not add the 
        course to the user's schedule.
        """
        self.login('testuser', 'testuser@test.com')
        profile = UserProfile.objects.get(user=5)
        timetable = TimeTable.objects.get(author=5)
        # create course to add to database
        Course.objects.create(timetable=timetable, name="CS 1110: Intro to Programming", section="001", topic="", component="LEC", units=3, 
            instructor="Raymond Pettit", days="MoWeFr", times="02:00PM-02:50PM", location="Gilmer Hall 301")
        # attempt to add this course
        response = self.client.post(reverse('schedule'), {'course_name':"CS 2120: Discrete Mathematics and Theory 1", "course_section":"001", 
                "days":"MoWeFr", "times":"02:00PM-02:50PM", "course_component":"LEC", "course_units":3, "course_instructor":"Elizabeth Orrico", 
                "location":"Mechanical Engr Bldg 205"}) 
        # checking that the we redirect and get duplicate error
        self.assertContains(response, 'Class is a duplicate or conflicts with an existing class time.')
        self.assertEqual(True, timetable.courses.filter(name="CS 1110: Intro to Programming").exists())    # check that CS 1110 exists
        self.assertFalse(timetable.courses.filter(name="CS 2120: Discrete Mathematics and Theory 1").exists())
        # tear down variables
        self.client.logout()
        self.client.delete(User.objects.get(username='testuser'))

    def test_schedule_allows_adding_special_topic(self):
        """
        Test should validate appropriate behavior when adding a special topic course (same course code). In this case, the user should be redirected
        to their schedule with the selected course added
        """
        self.login('testuser', 'testuser@test.com')
        profile = UserProfile.objects.get(user=5)
        timetable = TimeTable.objects.get(author=5)
        # create course to add to database
        Course.objects.create(timetable=timetable, name="CS 4501: Special Topics in Computer Science", section="001", topic="Privacy in the Internet Age", 
            component="LEC", units=3, instructor="Yixin Sun", days="MoWe", times="02:00PM-03:15PM", location="Thornton Hall E316")
        # attempt to add this course
        response = self.client.post(reverse('schedule'), {'course_name':"CS 4501: Special Topics in Computer Science", "course_section":"002", "course_topic":"Biocomputing",
                "days":"TuTh", "times":"12:30PM-01:45PM", "course_component":"LEC", "course_units":3, "course_instructor":"David Evans", 
                "location":"Olsson Hall 120"}) 
        # checking that the we go to schedule and both courses are added
        self.assertContains(response, "Privacy in the Internet Age")
        self.assertContains(response, "Biocomputing")
        self.assertEqual(2, len(timetable.courses.filter(name="CS 4501: Special Topics in Computer Science")))    # check that both special topics are added
        # tear down variables
        self.client.logout()
        self.client.delete(User.objects.get(username='testuser'))
    