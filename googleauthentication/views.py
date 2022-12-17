from django.shortcuts import render, reverse
import requests
import json
from django.contrib import messages
from calendar import HTMLCalendar
from datetime import datetime
from django.urls import reverse_lazy
from django.contrib.auth.mixins import UserPassesTestMixin, LoginRequiredMixin
from django.views import View
from django.http import HttpResponseRedirect
from django.views.generic.list import ListView

from .models import TimeTable, UserProfile, Comment, Course, Friends

from collections import OrderedDict
import copy

# Create your views here.

# Landing Page
# def index(request):
#    return render(request, 'index.html')


def home(request):
   return render(request,'home.html')

def searchClasses(request):
   response_API = requests.get('http://luthers-list.herokuapp.com/api/dept/CS/')
   data = response_API.text
   classes = json.loads(data)
   return render(request, 'searchClasses.html', {'classes': classes})

def searchPage(request):
   return render(request,'searchPage.html')

def classList(request):
   try:
      department = request.POST['department']
   except:
      department = None
      messages.add_message(request, messages.ERROR, 'Please enter subject')   # adds error message banner
      return render(request, 'searchPage.html')
   try:
      catalog_num = request.POST['catalog_num']
   except:
      catalog_num = None
   try:
      days_held = request.POST.getlist('days_held')
   except:
      days_held = None
   try:
      class_type = request.POST['grad_filter']
   except:
      class_type = None
   # edit input data
   days_final = ""
   for each in days_held:
      days_final += each

   try:
      response_API = requests.get('http://luthers-list.herokuapp.com/api/dept/'+department)
      data = response_API.text
      classes = json.loads(data)
   #print(response_API.status_code)
   except:
      messages.add_message(request, messages.ERROR, 'Please enter subject')   # adds error message banner
      return render(request, 'searchPage.html')
   #print(classes[0]['description'])

   # edit meeting date/time info so it's easier to work with
   for i in range(len(classes)):



      meeting_data = ""

      if (len(classes[i]['meetings']) == 0):
         meeting_data = ""
         days = ""
         classes[i]['meetings'] = {'days': "", 'times': "", 'facility_description': ""}

      else:
         meet = classes[i]['meetings'][0]
         # filter for days here
         facility = meet['facility_description']
         if meet['start_time']:

            # reformat start/end times
            datetime_start = datetime.strptime(meet['start_time'].split('-')[0], '%H.%M.%S.%f')
            start_time = datetime_start.strftime("%I:%M%p")   # converts back to string


            datetime_end = datetime.strptime(meet['end_time'].split('-')[0], '%H.%M.%S.%f')
            end_time = datetime_end.strftime("%I:%M%p")   # converts back to string

            # add to meeting data
            meeting_data = start_time + "-" + end_time

         # update data
         classes[i]['meetings'] = {'days' : meet['days'], 'times': meeting_data,'facility_description' : facility}


   # restructure data: dictionary such that each course code is grouped together
   # also filtering data
   all_classes = {}
   for course in classes:
      if not class_type or (class_type == 'both') or (class_type == 'undergrad' and int(course['catalog_number']) < 5000) or (class_type == 'grad' and int(course['catalog_number']) >= 5000):
         if (not catalog_num or course['catalog_number'] == catalog_num) and (not days_final or course['meetings']['days'] == days_final):
            code = course['subject'] + " " + course['catalog_number'] + ": " + course['description']  # this will be the key
            if code in all_classes:
               all_classes[code].append(course)
            else:
               all_classes[code] = [course]
   # adding "no search results found" error
   """
   Found code to redirect to current page as this can happen with browser bars or the search page.
   Title: Redirect To Previous Page Django With Code Examples
   Link: https://www.folkstalk.com/tech/redirect-to-previous-page-django-with-code-examples/
   """
   if len(all_classes) == 0:
      messages.add_message(request, messages.ERROR, 'No search results found!')   # adds error message banner
      return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))
      # except:   # in case of bug
      #    messages.add_message(request, messages.ERROR, 'No search results found!')   # adds error message banner
      #    return render(request, 'searchPage.html')

   return render(request, 'classList.html', {'classes': all_classes})


class TimeTableView(LoginRequiredMixin, View):
   def get(self, request):
      profile = UserProfile.objects.get(pk=request.user.id)
      # timetables = TimeTable.objects.get(pk=pk)
      user = profile.user
      timetable = TimeTable.objects.get(author=user)
      
      my_classes = OrderedDict()   # maintains order
      my_classes['Monday'] = []
      my_classes['Tuesday'] = []
      my_classes['Wednesday'] = []
      my_classes['Thursday'] = []
      my_classes['Friday'] = []
      for each in timetable.courses.all():
         if 'Mo' in each.days:
            my_classes['Monday'].append(each)
         if 'Tu' in each.days:
            my_classes['Tuesday'].append(each)
         if 'We' in each.days:
            my_classes['Wednesday'].append(each)
         if 'Th' in each.days:
            my_classes['Thursday'].append(each)
         if 'Fr' in each.days:
            my_classes['Friday'].append(each)
      
      # order classes in order of time
      for date in my_classes.keys():
         time_course = []
         for course in my_classes[date]:
            temp = int(course.times.split(':')[0])
            if 'PM' in course.times.split(':')[1] and temp != 12:
               temp += 12
            if len(time_course) == 0:
               time_course.append([temp, course])
            else:
               if temp < time_course[0][0]:   # this would mean it's the earliest
                  time_course.insert(0, [temp, course])
               elif temp > time_course[-1][0]:   # this would mean it's the last one
                  time_course.append([temp, course])
               else:   # means it's somewhere in the middle
                  for i in range(len(time_course)-1):
                     if temp > time_course[i][0] and temp < time_course[i+1][0]:
                        time_course.insert(i+1, [temp, course])
         final_order = []
         for each in time_course:
            final_order.append(each[1])
         my_classes[date] = final_order
         
      comments = timetable.post_comments.all()

      context = {
         'user' : user,
         'timetable': timetable,
         'courses': my_classes,
         'comments': comments,
      }

      return render(request, 'schedule.html', context)

   def post(self, request):
      """
      Method that posts course information to timetable database; upon completion, should redirect to schedule
      (TODO: later, make method stay on classList page but with some indication that the course was added to the user's schedule)
      """
      profile = UserProfile.objects.get(pk=request.user.id)
      # timetables = TimeTable.objects.get(pk=pk)
      user = profile.user
      timetable = TimeTable.objects.get(author=user)

      if request.method == 'POST':
         # for comment responses/posting
         try:
            comment_post = request.POST['posted_comment']
            if comment_post == "" or comment_post == " ":
               messages.add_message(request, messages.ERROR, 'No comment entered!')   # adds error message banner
            else:
               # create new comment
               new_comment = Comment()
               new_comment.author = user
               new_comment.associated_schedule = timetable
               new_comment.comment_text = comment_post
               # did it get saved?
               new_comment.save()

         except KeyError:   # if not adding a comment
            name = request.POST['course_name']
            section = request.POST['course_section']
         
            try:   # ----- deleting a course -----
               remove = request.POST['delete_bool']
               timetable.courses.filter(name=name, section=section).delete()
               #to_delete.delete()
               #timetable.save()
            except:   # ----- adding a course -----
               try:
                  topic = request.POST['course_topic']
               except:
                  topic = None
               days = request.POST['days']
               times = request.POST['times']

               # add functionality that checks whether course is compatible with other courses
               does_not_conflict = True
               for each in timetable.courses.all():
                  # first, check for duplicates
                  if name == each.name:
                     if each.topic == "" and topic == None:   # should allow adding when special topic!
                        does_not_conflict = False
                        break
                  
                  # next, check day/time
                  if days == each.days:   # top-down
                     # change time formatting for new class
                     new_times_list = times.split('-')   # splits from e.g. "5:00PM - 6:15PM" to ["5:00", "-", "6:00"]
                     new_times_list = [new_times_list[0], new_times_list[1]]   # keep only times
                     new_times = []
                     for i in new_times_list:
                        new_times.append(datetime.strptime(i, "%H:%S%p").time())
                     
                     # change time formatting for old class
                     other_times_list = each.times.split('-')   # splits from e.g. "5:00PM - 6:15PM" to ["5:00", "-", "6:00"]
                     other_times_list = [other_times_list[0], other_times_list[1]]   # keep only times
                     other_times = []
                     for i in other_times_list:
                        other_times.append(datetime.strptime(i, "%H:%S%p").time())

                     # --- make time comparisons ---
                     # bad case: classes at same time
                     if new_times[0] == other_times[0] and new_times[1] == other_times[1]:
                        does_not_conflict = False
                        break
                     # bad case: overlapping new end to old beginning
                     elif new_times[0] <= other_times[0] and new_times[1] >= other_times[0]:
                        does_not_conflict = False
                        break
                     # another bad case: overlapping new beginning and old end
                     elif new_times[0] <= other_times[1] and new_times[1] >= other_times[1]:
                        does_not_conflict = False
                        break


               if does_not_conflict:
                  new_class = Course(timetable=timetable)
                  new_class.name = name
                  new_class.section = section
                  if topic != None:
                     new_class.topic = topic
                  new_class.component = request.POST['course_component']
                  new_class.units = request.POST['course_units']
                  new_class.instructor = request.POST['course_instructor']
                  new_class.days = days
                  new_class.times = times
                  new_class.location = request.POST['location']

                  new_class.save()
               
               else:
                  messages.add_message(request, messages.ERROR, 'Class is a duplicate or conflicts with an existing class time.')   # adds error message banner
                  return render(request, 'searchPage.html')   # update this to actually stay on classList
      
         # create usable course data structure for visualization on page (sort by key Mo/Tu/We/Th/Fr)
         my_classes = OrderedDict()   # maintains order
         my_classes['Monday'] = []
         my_classes['Tuesday'] = []
         my_classes['Wednesday'] = []
         my_classes['Thursday'] = []
         my_classes['Friday'] = []
         for each in timetable.courses.all():
            # debugging
            if 'Mo' in each.days:
               my_classes['Monday'].append(each)
            if 'Tu' in each.days:
               my_classes['Tuesday'].append(each)
            if 'We' in each.days:
               my_classes['Wednesday'].append(each)
            if 'Th' in each.days:
               my_classes['Thursday'].append(each)
            if 'Fr' in each.days:
               my_classes['Friday'].append(each)
         
         # order classes in order of time
         for date in my_classes.keys():
            time_course = []
            for course in my_classes[date]:
               temp = int(course.times.split(':')[0])
               if 'PM' in course.times.split(':')[1] and temp != 12:
                  temp += 12
               if len(time_course) == 0:
                  time_course.append([temp, course])
               else:
                  if temp < time_course[0][0]:   # this would mean it's the earliest
                     time_course.insert(0, [temp, course])
                  elif temp > time_course[-1][0]:   # this would mean it's the last one
                     time_course.append([temp, course])
                  else:   # means it's somewhere in the middle
                     for i in range(len(time_course)-1):
                        if temp > time_course[i][0] and temp < time_course[i+1][0]:
                           time_course.insert(i+1, [temp, course])
            final_order = []
            for each in time_course:
               final_order.append(each[1])
            my_classes[date] = final_order
         
         comments = timetable.post_comments.all()
         
         context = {
            'user' : user,
            'timetable': timetable,
            'courses': my_classes,
            'comments': comments
         }

         return render(request, 'schedule.html', context)   
         

# def scheduler(request):
#    list_of_TimeTables = TimeTable.objects.get(user_id = 1010)
#    return render(request,'schedule.html', 
#       {'user_TimeTable':list_of_TimeTables})

#####

def FriendsTimeTableView(request):
   # profile = UserProfile.objects.get(pk=request.user.id)
   # timetables = TimeTable.objects.get(pk=pk)
   # user = profile.user


   if request.method == 'POST':
      # functionality for adding a comment
      current_user = request.user
      friend = request.POST['friend_username']
      # can do this with user.id or userprofile.id
      friend_profile = UserProfile.objects.get(name=friend)
      # print(friend)
      timetable = TimeTable.objects.get(author=friend_profile.user)
      try:
         comment_post = request.POST['posted_comment']
         if comment_post == "" or comment_post == " ":
            messages.add_message(request, messages.ERROR, 'No comment entered!')   # adds error message banner
         else:
            # create new comment
            new_comment = Comment()
            new_comment.author = current_user
            new_comment.associated_schedule = timetable
            new_comment.comment_text = comment_post
            # did it get saved?
            new_comment.save()

      except KeyError:
         new_comment = None   # basically just a throwaway assignment if just getting page; no comment yet

      # timetable = TimeTable.objects.get(author = index)
      # timetable = TimeTable.objects.get(author = friend)

      # need to compare author and friend to get the correct instance of TimeTable. author requires id, but friend is the value of that id.
      # timetables = TimeTable.objects.all()
      # timetable <-- author == friend
   
      my_classes = OrderedDict()   # maintains order
      my_classes['Monday'] = []
      my_classes['Tuesday'] = []
      my_classes['Wednesday'] = []
      my_classes['Thursday'] = []
      my_classes['Friday'] = []
      for each in timetable.courses.all():
         if 'Mo' in each.days:
            my_classes['Monday'].append(each)
         if 'Tu' in each.days:
            my_classes['Tuesday'].append(each)
         if 'We' in each.days:
            my_classes['Wednesday'].append(each)
         if 'Th' in each.days:
            my_classes['Thursday'].append(each)
         if 'Fr' in each.days:
            my_classes['Friday'].append(each)
      
      # order classes in order of time
      for date in my_classes.keys():
         time_course = []
         for course in my_classes[date]:
            temp = int(course.times.split(':')[0])
            if 'PM' in course.times.split(':')[1] and temp != 12:
               temp += 12
            if len(time_course) == 0:
               time_course.append([temp, course])
            else:
               if temp < time_course[0][0]:   # this would mean it's the earliest
                  time_course.insert(0, [temp, course])
               elif temp > time_course[-1][0]:   # this would mean it's the last one
                  time_course.append([temp, course])
               else:   # means it's somewhere in the middle
                  for i in range(len(time_course)-1):
                     if temp > time_course[i][0] and temp < time_course[i+1][0]:
                        time_course.insert(i+1, [temp, course])
         final_order = []
         for each in time_course:
            final_order.append(each[1])
         my_classes[date] = final_order
      
      # get comments on post
      comments = timetable.post_comments.all()
      

   context = {
      'timetable': timetable,
      'friend': friend,
      'courses': my_classes,
      'comments': comments,
   }

   return render(request, 'friendsSchedule.html', context)

#####
def social(request):
   userList = UserProfile.objects.all()
   me = UserProfile.objects.get(pk=request.user.id)
   friendslist = [profile.friend_profile for profile in me.following.all() if profile != me]
   # default filtering
   filters = {'major':'', 'minor':'', 'year':''}
   # make sure we aren't including admin in friending options; throws errors 
   real_userList = []
   for profile in userList:
      if not profile.user.is_staff and profile != me and profile not in friendslist:
         real_userList.append(profile)

   if request.method == 'POST':
      user_id = me
      # ---- FOR ADDING A NEW FRIEND -----
      try:
         friends_name = request.POST['friend_search']
         # check for blank user
         if request.POST['friend_search'] == '':
            messages.add_message(request, messages.ERROR, 'You have added all available friends!')   # adds warning banner
            return render(request,'friends.html', {'userList': real_userList, 'friendslist': friendslist, 'me': me, 'filters':filters})
         
         temp = UserProfile.objects.get(name=friends_name)
         friends_id = str(temp.user_id)
         new_follower = Friends.objects.create(user_id=user_id, friend_profile=temp, friends_id=friends_id, friend_username=friends_name)
         new_follower.save()
         friendslist.append(new_follower.friend_profile)
         real_userList.remove(new_follower.friend_profile)

      # ----- FOR FILTERING RESULTS -----
      except:
         
         # ----- FOR FILTERING RESULTS -----
         # update filters
         filters['major'] = request.POST['major']
         filters['minor'] = request.POST['minor']
         filters['year'] = request.POST['year']
         # update friendslist to display those filtered
         if filters['major'] == '' and filters['minor'] == '' and filters['year'] == '':
               messages.add_message(request, messages.INFO, 'An empty search will display all friends.')   # adds info message banner
         else:
            templist = copy.deepcopy(friendslist)
            for friend in friendslist:
               if friend.major != None:   # had to do this check to prevent errors
                  if friend.major.lower() != filters['major'].lower() and filters['major'] != '':   # used .lower() to reduce input issues (e.g. someone used lowercase or upper-case)
                     templist.remove(friend)
                     continue
               elif filters['major'] != '':
                  templist.remove(friend)
                  continue
               if friend.minor != None:   # had to do this check to prevent errors
                  if friend.minor.lower() != filters['minor'].lower() and filters['minor'] != '':   # used .lower() to reduce input issues (e.g. someone used lowercase or upper-case)
                     templist.remove(friend)
                     continue
               elif filters['minor'] != '':
                  templist.remove(friend)
                  continue
               if friend.year != filters['year'] and filters['year'] != '':
                  templist.remove(friend)
            friendslist = templist

   return render(request,'friends.html', {'userList': real_userList, 'friendslist': friendslist, 'me': me, 'filters':filters})

def myInfo(request):
   profile = UserProfile.objects.get(user=request.user.id)
   if request.method == 'POST':
      # option for empty input:
      if request.POST['year'] == '' and request.POST['major'] == '' and request.POST['minor'] == '' and request.POST['bio'] == '':
         messages.add_message(request, messages.ERROR, 'Empty input: If updating, please enter items into an input field.')   # adds error message banner
         personal_info = {'year': profile.year, 'major': profile.major, 'minor': profile.minor, 'bio': profile.bio }
         return render(request, 'my_information.html', {'personal_info': personal_info} )

      if request.POST['year'] != "":
         profile.year = request.POST['year']
      if request.POST['major'] != "":
         profile.major = request.POST['major']
      if request.POST['minor'] != "":
         profile.minor = request.POST['minor']
      if request.POST['bio'] != "":
         profile.bio = request.POST['bio']
      profile.save()

   personal_info = {'year': profile.year, 'major': profile.major, 'minor': profile.minor, 'bio': profile.bio }
   return render(request, 'my_information.html', {'personal_info': personal_info} )
