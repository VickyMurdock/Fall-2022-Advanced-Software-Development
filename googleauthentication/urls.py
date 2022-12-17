from django.urls import path
from . import views

urlpatterns = [
   #path('', views.index, name='index'),
   path('',views.home, name='home'),
   path('searchPage',views.searchPage, name='searchPage'),
   #path("searchPage", views.searchClasses),
   path("list", views.classList, name="classList"),
   path("schedule", views.TimeTableView.as_view(), name="schedule"),
   path("friendsSchedule", views.FriendsTimeTableView, name="friends_schedule"),
   path("friends", views.social, name="friends"),
   path("myInfo", views.myInfo, name="myInfo"),
]