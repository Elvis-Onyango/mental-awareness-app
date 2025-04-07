from django.urls import path
from .views import ( SignUpView, custom_login, 
       custom_logout, profile_view,home,  QuizListView,
    quiz_detail,
    start_quiz,take_quiz,
    quiz_results,quiz_history,
    mood_dashboard,MoodEntryCreateView,
    MoodEntryUpdateView,mood_entry_delete,
    quick_mood_entry,ResourceListView, resource_detail,
    ForumPostListView,book_appointment,
    ForumPostCreateView,counselor_list,CounselorDetailView,
    forum_post_detail,complete_counselor_profile,add_review,
    forum_comment_delete,ForumPostUpdateView,appointment_confirmation,
    EventListView,EventDetailView,event_rsvp,counselor_profile_required,
    WellnessJourneyView,dashboard,admin_dashboard,counselor_dashboard

       )

urlpatterns = [
    path('signup/', SignUpView.as_view(), name='signup'),
    path('login/', custom_login, name='login'),
    path('logout/', custom_logout, name='logout'),
    path('profile/', profile_view, name='profile'),
    path('quiz-list/', QuizListView.as_view(), name='quiz_list'),
    path('<int:quiz_id>/', quiz_detail, name='quiz_detail'),
    path('<int:quiz_id>/start/', start_quiz, name='start_quiz'),
    path('attempt/<int:attempt_id>/', take_quiz, name='take_quiz'),
    path('attempt/<int:attempt_id>/results/', quiz_results, name='quiz_results'),
    path('history/', quiz_history, name='quiz_history'),
    path('mood/', mood_dashboard, name='mood_dashboard'),
    path('mood/add/', MoodEntryCreateView.as_view(), name='mood_entry_create'),
    path('mood/<int:pk>/edit/', MoodEntryUpdateView.as_view(), name='mood_entry_update'),
    path('mood/<int:pk>/delete/', mood_entry_delete, name='mood_entry_delete'),
    path('mood/quick-entry/', quick_mood_entry, name='quick_mood_entry'),
    path('resource-list', ResourceListView.as_view(), name='resource_list'),
    path('resources/<int:pk>/', resource_detail, name='resource_detail'),
     path('resources/search/', ResourceListView.as_view(), name='resource_search'),
    path('events/', EventListView.as_view(), name='event_list'),
    path('events/<int:pk>/', EventDetailView.as_view(), name='event_detail'),
    path('events/<int:pk>/rsvp/', event_rsvp, name='event_rsvp'),
    path('forum', ForumPostListView.as_view(), name='forum_list'),
    path('new/', ForumPostCreateView.as_view(), name='forum_post_create'),
    path('forum/<int:pk>/', forum_post_detail, name='forum_post_detail'),
    path('forum/post/<int:pk>/edit/', ForumPostUpdateView.as_view(), name='forum_post_edit'),
    path('comments/<int:pk>/delete/', forum_comment_delete, name='forum_comment_delete'),
    path('journey/', WellnessJourneyView.as_view(), name='wellness_journey'),
    path('dashboard/user', dashboard, name='user_dashboard'),
    path('dashboard/admin', admin_dashboard, name='admin_dashboard'),
    path('counselor/dashboard/', counselor_dashboard, name='counselor_dashboard'),
    path('counselor/profile-required/', counselor_profile_required, name='counselor_profile_required'),
    path('counselor/complete-profile/', complete_counselor_profile, name='complete_counselor_profile'),
    path('counselors/', counselor_list, name='counselor_list'),
    path('counselors/book/<int:counselor_id>/', book_appointment, name='book_appointment'),
    path('counselors/<int:pk>/', CounselorDetailView.as_view(), name='counselor_detail'),
    path('counselors/<int:pk>/review/', add_review, name='add_review'),
    path('appointment/confirm/<int:appointment_id>/', appointment_confirmation, name='appointment_confirmation'),

    path('',home , name = 'home')
]



