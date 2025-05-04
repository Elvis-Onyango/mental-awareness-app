from django.urls import path
from .views import (
    SignUpView, custom_login, custom_logout, profile_view, home,
    QuizListView, quiz_detail, start_quiz, take_quiz,
    quiz_results, quiz_history, mood_dashboard, MoodEntryCreateView,
    MoodEntryUpdateView, mood_entry_delete, quick_mood_entry,
    ResourceListView, resource_detail, ForumPostListView, book_appointment,
    ForumPostCreateView, counselor_list, CounselorDetailView,
    forum_post_detail, complete_counselor_profile, add_review,
    forum_comment_delete, ForumPostUpdateView, appointment_confirmation,
    EventListView, EventDetailView, event_rsvp, counselor_profile_required,
    WellnessJourneyView, dashboard, admin_dashboard, counselor_dashboard,
    # Added these new views
    question_module_intro, mood_assessment, mood_based_quizzes,
    # Admin dashboard views
    user_management, create_user, edit_user, user_detail,
    counselor_applications, view_counselor_application,
    approve_counselor, reject_counselor, at_risk_users,
    quiz_management, create_quiz, quiz_analytics,
    resource_management, create_resource,
    send_alert, get_analytics_data
)

urlpatterns = [
    # Authentication URLs
    path('signup/', SignUpView.as_view(), name='signup'),
    path('login/', custom_login, name='login'),
    path('logout/', custom_logout, name='logout'),
    
    # Profile and Dashboard URLs
    path('profile/', profile_view, name='profile'),
    path('dashboard/user', dashboard, name='user_dashboard'),
    path('dashboard/admin', admin_dashboard, name='admin_dashboard'),
    path('counselor/dashboard/', counselor_dashboard, name='counselor_dashboard'),
    
    # New Mood-Based Quiz Flow URLs
    path('questions/', question_module_intro, name='question_module_intro'),
    path('mood-assessment/', mood_assessment, name='mood_assessment'),
    path('mood-quizzes/<int:mood_entry_id>/', mood_based_quizzes, name='mood_based_quizzes'),
    
    # Quiz URLs - organized in a logical flow
    path('quizzes/', question_module_intro, name='quiz_intro'),  # New entry point
    path('quizzes/mood-check/', mood_assessment, name='mood_assessment'),  # Mood assessment
    path('quizzes/recommended/<int:mood_entry_id>/', mood_based_quizzes, name='mood_based_quizzes'),  # Recommendations
    path('quizzes/list/', QuizListView.as_view(), name='quiz_list'),  # All quizzes list
    path('quizzes/<int:quiz_id>/', quiz_detail, name='quiz_detail'),  # Quiz details
    path('quizzes/<int:quiz_id>/start/', start_quiz, name='start_quiz'),  # Start quiz
    path('quizzes/attempt/<int:attempt_id>/', take_quiz, name='take_quiz'),  # Take quiz
    path('quizzes/attempt/<int:attempt_id>/results/', quiz_results, name='quiz_results'),  # Quiz results
    path('quizzes/history/', quiz_history, name='quiz_history'),  # Quiz history
    
    # Mood Tracking URLs
    path('mood/', mood_dashboard, name='mood_dashboard'),
    path('mood/add/', MoodEntryCreateView.as_view(), name='mood_entry_create'),
    path('mood/<int:pk>/edit/', MoodEntryUpdateView.as_view(), name='mood_entry_update'),
    path('mood/<int:pk>/delete/', mood_entry_delete, name='mood_entry_delete'),
    path('mood/quick-entry/', quick_mood_entry, name='quick_mood_entry'),
    
    # Resource URLs
    path('resource-list', ResourceListView.as_view(), name='resource_list'),
    path('resources/<int:pk>/', resource_detail, name='resource_detail'),
    path('resources/search/', ResourceListView.as_view(), name='resource_search'),
    
    # Event URLs
    path('events/', EventListView.as_view(), name='event_list'),
    path('events/<int:pk>/', EventDetailView.as_view(), name='event_detail'),
    path('events/<int:pk>/rsvp/', event_rsvp, name='event_rsvp'),
    
    # Forum URLs
    path('forum', ForumPostListView.as_view(), name='forum_list'),
    path('forum/new/', ForumPostCreateView.as_view(), name='forum_post_create'),
    path('forum/<int:pk>/', forum_post_detail, name='forum_post_detail'),
    path('forum/post/<int:pk>/edit/', ForumPostUpdateView.as_view(), name='forum_post_edit'),
    path('forum/comments/<int:pk>/delete/', forum_comment_delete, name='forum_comment_delete'),
    
    # Wellness and Counseling URLs
    path('journey/', WellnessJourneyView.as_view(), name='wellness_journey'),
    path('counselor/profile-required/', counselor_profile_required, name='counselor_profile_required'),
    path('counselor/complete-profile/', complete_counselor_profile, name='complete_counselor_profile'),
    path('counselors/', counselor_list, name='counselor_list'),
    path('counselors/book/<int:counselor_id>/', book_appointment, name='book_appointment'),
    path('counselors/<int:pk>/', CounselorDetailView.as_view(), name='counselor_detail'),
    path('counselors/<int:pk>/review/', add_review, name='add_review'),
    path('appointment/confirm/<int:appointment_id>/', appointment_confirmation, name='appointment_confirmation'),
    
    # ==============================================
    # ADMIN DASHBOARD URLs (NEWLY ADDED)
    # ==============================================
    
    # User Management
    path('admin-users/', user_management, name='admin_user_management'),
    path('admin-users/create/', create_user, name='admin_create_user'),
    path('admin-users/<int:user_id>/edit/', edit_user, name='admin_edit_user'),
    path('admin-users/<int:user_id>/', user_detail, name='admin_user_detail'),
    
    # Counselor Management
    path('admin-counselors/applications/', counselor_applications, name='admin_counselor_applications'),
    path('admin-counselors/applications/<int:application_id>/', view_counselor_application, name='admin_view_application'),
    path('admin-counselors/<int:counselor_id>/approve/', approve_counselor, name='admin_approve_counselor'),
    path('admin-counselors/<int:counselor_id>/reject/', reject_counselor, name='admin_reject_counselor'),
    
    # At Risk Users
    path('admin-at-risk-users/', at_risk_users, name='admin_at_risk_users'),
    
    # Quiz Management
    path('admin-quizzes/', quiz_management, name='admin_quiz_management'),
    path('admin-quizzes/create/', create_quiz, name='admin_create_quiz'),
    path('admin-quizzes/<int:quiz_id>/analytics/', quiz_analytics, name='admin_quiz_analytics'),
    
    # Resource Management
    path('admin-resources/', resource_management, name='admin_resource_management'),
    path('admin-resources/create/', create_resource, name='admin_create_resource'),
    
    path('admin-send-alert/', send_alert, name='admin_send_alert'),
    
    # API Endpoints
    path('admin-api/analytics/', get_analytics_data, name='admin_get_analytics_data'),
    
    # Home URL
    path('', home, name='home')
]