from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.views.generic import CreateView
from django.urls import reverse_lazy
from django.contrib import messages
from .forms import CustomUserCreationForm, CustomAuthenticationForm, ForumPostForm, ForumCommentForm
from django.utils import timezone
from django.http import JsonResponse
from django.views.generic import ListView
import json
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib import messages
from django.views.generic import ListView, CreateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import DetailView
from django.contrib.auth.decorators import user_passes_test
from django.db.models import Q
from django.urls import reverse 
from .models import (
    User,
    Quiz, 
    Question, 
    AnswerOption, 
    QuizAttempt, 
    UserResponse,
    MentalHealthCategory,
    MoodEntry, Event, 
    WellnessResource,
    MentalHealthCategory,
    ForumPost, ForumComment,
    MentalHealthCategory,Event, CounselorProfile
)






def home(request):
    return render(request,'index.html') 


class SignUpView(CreateView):
    form_class = CustomUserCreationForm
    template_name = 'signup.html'
    success_url = reverse_lazy('login')

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, 'Account created successfully! Please log in.')
        return response

def custom_login(request):
    if request.user.is_authenticated:
        # Redirect already authenticated users based on their type
        if request.user.is_superuser or request.user.user_type == 'ADMIN':
            return redirect('admin_dashboard')
        return redirect('user_dashboard')
    
    if request.method == 'POST':
        form = CustomAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f'Welcome back, {user.username}!')
            
            # Redirect after login based on user type
            if user.is_superuser or user.user_type == 'ADMIN':
                return redirect('admin_dashboard')
            if user.user_type == 'COUNSELOR': 
                return redirect('counselor_dashboard')
            return redirect('user_dashboard')
    else:
        form = CustomAuthenticationForm()
    
    return render(request, 'login.html', {'form': form})

@login_required
def custom_logout(request):
    logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect('home')

@login_required
def profile_view(request):
    return render(request, 'profile.html', {'user': request.user})






class QuizListView(ListView):
    model = Quiz
    template_name = 'quiz_list.html'
    context_object_name = 'quizzes'
    
    def get_queryset(self):
        return Quiz.objects.filter(is_active=True).select_related('category')

@login_required
def quiz_detail(request, quiz_id):
    quiz = get_object_or_404(Quiz, pk=quiz_id, is_active=True)
    return render(request, 'quiz_detail.html', {'quiz': quiz})

@login_required
def start_quiz(request, quiz_id):
    quiz = get_object_or_404(Quiz, pk=quiz_id, is_active=True)
    
    # Check for existing incomplete attempt
    incomplete_attempt = QuizAttempt.objects.filter(
        user=request.user,
        quiz=quiz,
        is_completed=False
    ).first()
    
    if incomplete_attempt:
        return redirect('take_quiz', attempt_id=incomplete_attempt.id)
    
    # Create new attempt
    attempt = QuizAttempt.objects.create(
        user=request.user,
        quiz=quiz
    )
    return redirect('take_quiz', attempt_id=attempt.id)

@login_required
def take_quiz(request, attempt_id):
    attempt = get_object_or_404(QuizAttempt, pk=attempt_id, user=request.user)
    
    if attempt.is_completed:
        return redirect('quiz_results', attempt_id=attempt.id)
    
    # Get answered questions
    answered_questions = UserResponse.objects.filter(
        attempt=attempt
    ).values_list('question_id', flat=True)
    
    # Get next question
    current_question = Question.objects.filter(
        quiz=attempt.quiz
    ).exclude(
        id__in=answered_questions
    ).first()
    
    if not current_question:
        # Quiz is complete
        attempt.is_completed = True
        attempt.completed_at = timezone.now()
        attempt.calculate_score()
        attempt.save()
        return redirect('quiz_results', attempt_id=attempt.id)
    
    if request.method == 'POST':
        # Process form submission
        if current_question.question_type == 'OE':
            response = UserResponse.objects.create(
                attempt=attempt,
                question=current_question,
                text_response=request.POST.get('text_response', '')
            )
        else:
            selected_option_id = request.POST.get('selected_option')
            selected_option = None
            if selected_option_id:
                selected_option = AnswerOption.objects.get(pk=selected_option_id)
            
            response = UserResponse.objects.create(
                attempt=attempt,
                question=current_question,
                selected_option=selected_option
            )
        
        # Evaluate response
        response.evaluate_response()
        return redirect('take_quiz', attempt_id=attempt.id)
    
    # Prepare options for the question
    options = current_question.options.all()
    
    context = {
        'attempt': attempt,
        'question': current_question,
        'options': options,
        'progress': (
            (answered_questions.count() / attempt.quiz.questions.count()) * 100 
            if attempt.quiz.questions.count() > 0 else 0
        ),
    }
    return render(request, 'take_quiz.html', context)

@login_required
def quiz_results(request, attempt_id):
    attempt = get_object_or_404(QuizAttempt, pk=attempt_id, user=request.user)
    
    if not attempt.is_completed:
        return redirect('take_quiz', attempt_id=attempt.id)
    
    responses = UserResponse.objects.filter(
        attempt=attempt
    ).select_related('question', 'selected_option')
    
    context = {
        'attempt': attempt,
        'responses': responses,
        'score_percentage': round(attempt.score, 2) if attempt.score else 0,
        'passed': attempt.score >= attempt.quiz.passing_score if attempt.score else False,
    }
    return render(request, 'quiz_results.html', context)

@login_required
def quiz_history(request):
    attempts = QuizAttempt.objects.filter(
        user=request.user,
        is_completed=True
    ).select_related('quiz', 'quiz__category').order_by('-completed_at')
    
    context = {
        'attempts': attempts,
    }
    return render(request, 'quiz_history.html', context)



@login_required
def mood_dashboard(request):
    # Get last 30 days of mood entries
    mood_entries = MoodEntry.objects.filter(
        user=request.user,
        recorded_at__gte=timezone.now()-timezone.timedelta(days=30)
    ).order_by('recorded_at')
    
    # Prepare data for chart
    mood_data = {
        'dates': [entry.recorded_at.strftime('%Y-%m-%d') for entry in mood_entries],
        'levels': [entry.mood_level for entry in mood_entries],
        'notes': [entry.notes for entry in mood_entries],
    }
    
    # Get quiz attempts in same period
    quiz_attempts = QuizAttempt.objects.filter(
        user=request.user,
        completed_at__gte=timezone.now()-timezone.timedelta(days=30),
        is_completed=True
    ).select_related('quiz')
    
    context = {
        'mood_entries': mood_entries,
        'mood_data_json': json.dumps(mood_data),
        'quiz_attempts': quiz_attempts,
    }
    return render(request, 'mood_dashboard.html', context)

class MoodEntryCreateView(CreateView):
    model = MoodEntry
    fields = ['mood_level', 'notes', 'related_quiz']
    template_name = 'mood_entry_form.html'
    
    def form_valid(self, form):
        form.instance.user = self.request.user
        messages.success(self.request, 'Mood entry added successfully!')
        return super().form_valid(form)
    
    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        # Only show quizzes completed by this user
        form.fields['related_quiz'].queryset = QuizAttempt.objects.filter(
            user=self.request.user,
            is_completed=True
        )
        return form
    
    def get_success_url(self):
        return reverse_lazy('mood_dashboard')

class MoodEntryUpdateView(UpdateView):
    model = MoodEntry
    fields = ['mood_level', 'notes', 'related_quiz']
    template_name = 'mood_entry_form.html'
    
    def get_queryset(self):
        return super().get_queryset().filter(user=self.request.user)
    
    def form_valid(self, form):
        messages.success(self.request, 'Mood entry updated successfully!')
        return super().form_valid(form)
    
    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        # Only show quizzes completed by this user
        form.fields['related_quiz'].queryset = QuizAttempt.objects.filter(
            user=self.request.user,
            is_completed=True
        )
        return form
    
    def get_success_url(self):
        return reverse_lazy('mood_dashboard')

@login_required
def mood_entry_delete(request, pk):
    entry = get_object_or_404(MoodEntry, pk=pk, user=request.user)
    if request.method == 'POST':
        entry.delete()
        messages.success(request, 'Mood entry deleted successfully!')
        return redirect('mood_dashboard')
    return render(request, 'mood_entry_confirm_delete.html', {'entry': entry})

@login_required
def quick_mood_entry(request):
    if request.method == 'POST':
        mood_level = request.POST.get('mood_level')
        if mood_level:
            MoodEntry.objects.create(
                user=request.user,
                mood_level=mood_level,
                recorded_at=timezone.now()
            )
            messages.success(request, 'Quick mood entry recorded!')
        return redirect('mood_dashboard')
    return redirect('mood_dashboard')



class ResourceListView(ListView):
    model = WellnessResource
    template_name = 'resource_list.html'
    context_object_name = 'resources'
    paginate_by = 12
    ordering = ['-is_featured', '-created_at']
    
    def get_queryset(self):
        queryset = super().get_queryset().select_related('category')
        category_id = self.request.GET.get('category')
        resource_type = self.request.GET.get('type')
        search_query = self.request.GET.get('q')
        
        # Apply filters
        if category_id:
            queryset = queryset.filter(category__id=category_id)
        if resource_type:
            queryset = queryset.filter(resource_type=resource_type)
        
        # Apply search
        if search_query:
            queryset = queryset.filter(
                Q(title__icontains=search_query) |
                Q(content__icontains=search_query) |
                Q(category__name__icontains=search_query)
            )
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'categories': MentalHealthCategory.objects.all(),
            'resource_types': WellnessResource.RESOURCE_TYPES,
            'selected_category': self.request.GET.get('category'),
            'selected_type': self.request.GET.get('type'),
            'search_query': self.request.GET.get('q', ''),
            'featured_resources': WellnessResource.objects.filter(
                is_featured=True
            ).order_by('-created_at')[:3],
        })
        return context

def resource_detail(request, pk):
    resource = get_object_or_404(
        WellnessResource.objects.select_related('category'), 
        pk=pk
    )
    
    # Get related resources (same category, excluding current)
    related_resources = WellnessResource.objects.filter(
        category=resource.category
    ).exclude(
        id=resource.id
    ).order_by('-is_featured', '-created_at')[:4]
    
    # Get similar type resources
    similar_type_resources = WellnessResource.objects.filter(
        resource_type=resource.resource_type
    ).exclude(
        id=resource.id
    ).order_by('-created_at')[:2]
    
    # Prepare video context if resource is a video
    video_context = {}
    if resource.resource_type == 'VIDEO':
        video_context = {
            'is_video': True,
            'has_video_file': bool(resource.video_file),
            'has_embed_code': bool(resource.video_embed_code),
        }
    
    return render(request, 'resource_detail.html', {
        'resource': resource,
        'related_resources': related_resources,
        'similar_type_resources': similar_type_resources,
        **video_context,
    })



class ForumPostListView(ListView):
    model = ForumPost
    template_name = 'forum_list.html' 
    context_object_name = 'posts'
    paginate_by = 15
    
    def get_queryset(self):
        queryset = super().get_queryset()
        category_id = self.request.GET.get('category')
        
        if category_id:
            queryset = queryset.filter(category__id=category_id)
        
        return queryset.select_related('user', 'category').order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = MentalHealthCategory.objects.all()
        context['selected_category'] = self.request.GET.get('category')
        return context

class ForumPostCreateView(LoginRequiredMixin, CreateView):
    model = ForumPost
    form_class = ForumPostForm
    template_name = 'forum_post_form.html'
    
    def form_valid(self, form):
        form.instance.user = self.request.user
        messages.success(self.request, 'Your post has been created!')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('forum_post_detail', kwargs={'pk': self.object.pk})

def forum_post_detail(request, pk):
    post = get_object_or_404(ForumPost, pk=pk)
    
    if request.method == 'POST' and request.user.is_authenticated:
        form = ForumCommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.post = post
            comment.user = request.user
            comment.save()
            messages.success(request, 'Your comment has been added!')
            return redirect('forum_post_detail', pk=post.pk)
    else:
        form = ForumCommentForm()
    
    return render(request, 'forum_post_detail.html', {
        'post': post,
        'form': form,
    })

@login_required
def forum_comment_delete(request, pk):
    comment = get_object_or_404(ForumComment, pk=pk, user=request.user)
    post_pk = comment.post.pk
    comment.delete()
    messages.success(request, 'Your comment has been deleted!')
    return redirect('forum_post_detail', pk=post_pk)


class ForumPostUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = ForumPost
    form_class = ForumPostForm
    template_name = 'forum_edit_form.html'

    def test_func(self):
        post = self.get_object()
        return self.request.user == post.user

    def form_valid(self, form):
        messages.success(self.request, 'Your post has been updated!')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('forum_post_detail', kwargs={'pk': self.object.pk})




class EventListView(ListView):
    model = Event
    template_name = 'event_list.html'
    context_object_name = 'events'
    ordering = ['start_time']
    
    def get_queryset(self):
        now = timezone.now()
        return super().get_queryset().filter(start_time__gte=now)

class EventDetailView(DetailView):
    model = Event
    template_name = 'event_detail.html'
    context_object_name = 'event'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_attending'] = self.object.attendees.filter(id=self.request.user.id).exists()
        return context

@login_required
def event_rsvp(request, pk):
    event = get_object_or_404(Event, pk=pk)
    if request.user in event.attendees.all():
        event.attendees.remove(request.user)
        messages.success(request, "You're no longer attending this event.")
    else:
        event.attendees.add(request.user)
        messages.success(request, "You're now attending this event!")
    return redirect('event_detail', pk=event.pk)



from django.views.generic import DetailView
from .models import UserWellnessJourney

class WellnessJourneyView(DetailView):
    model = UserWellnessJourney
    template_name = 'wellness_journey.html'
    context_object_name = 'journey'
    
    def get_object(self):
        return self.request.user.wellness_journey
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get mood data for charts
        mood_entries = self.request.user.mood_entries.order_by('recorded_at')
        mood_data = {
            'dates': [entry.recorded_at.strftime('%Y-%m-%d') for entry in mood_entries],
            'levels': [entry.mood_level for entry in mood_entries],
        }
        context['mood_data_json'] = json.dumps(mood_data)
        
        # Get quiz attempts
        quiz_attempts = self.request.user.quiz_attempts.filter(is_completed=True).order_by('-completed_at')[:5]
        context['quiz_attempts'] = quiz_attempts
        
        # Get recent forum activity
        forum_posts = self.request.user.forumpost_set.order_by('-created_at')[:3]
        context['forum_posts'] = forum_posts
        
        # Get upcoming events
        upcoming_events = self.request.user.events_attending.filter(
            start_time__gte=timezone.now()
        ).order_by('start_time')[:3]
        context['upcoming_events'] = upcoming_events
        
        return context






@login_required
def dashboard(request):
    # Mood data for the chart
    mood_entries = MoodEntry.objects.filter(
        user=request.user,
        recorded_at__gte=timezone.now()-timezone.timedelta(days=30)
    ).order_by('recorded_at')
    
    mood_data = {
        'dates': [entry.recorded_at.strftime('%Y-%m-%d') for entry in mood_entries],
        'levels': [entry.mood_level for entry in mood_entries],
    }
    
    # Recent quiz attempts
    recent_quizzes = QuizAttempt.objects.filter(
        user=request.user,
        is_completed=True
    ).order_by('-completed_at')[:3]
    
    # Upcoming events
    upcoming_events = Event.objects.filter(
        start_time__gte=timezone.now()
    ).order_by('start_time')[:2]
    
    # Recommended resources
    recommended_resources = WellnessResource.objects.filter(
        is_featured=True
    ).order_by('-created_at')[:3]
    
    context = {
        'mood_data_json': json.dumps(mood_data),
        'recent_quizzes': recent_quizzes,
        'upcoming_events': upcoming_events,
        'recommended_resources': recommended_resources,
    }
    return render(request, 'userdashboard.html', context)






from django.db.models import Count, Avg
from datetime import timedelta
from collections import defaultdict

def admin_check(user):
    return user.is_authenticated and user.user_type == 'ADMIN'

@user_passes_test(admin_check)
def admin_dashboard(request):
    # User statistics
    total_users = User.objects.count()
    new_users = User.objects.filter(date_joined__gte=timezone.now()-timedelta(days=7)).count()
    
    # Calculate user type percentages
    user_types = {
        'students': User.objects.filter(user_type='STUDENT').count(),
        'counselors': User.objects.filter(user_type='COUNSELOR').count(),
        'admins': User.objects.filter(user_type='ADMIN').count()
    }
    total_user_types = sum(user_types.values())
    if total_user_types > 0:
        user_types.update({
            'students_percentage': round((user_types['students'] / total_user_types) * 100),
            'counselors_percentage': round((user_types['counselors'] / total_user_types) * 100),
            'admins_percentage': round((user_types['admins'] / total_user_types) * 100)
        })

    # User growth data (last 30 days)
    thirty_days_ago = timezone.now() - timedelta(days=30)
    user_growth_data = User.objects.filter(
        date_joined__gte=thirty_days_ago
    ).extra({
        'day': "date(date_joined)"
    }).values('day').annotate(count=Count('id')).order_by('day')
    
    # Prepare labels and data for the chart
    dates = [thirty_days_ago + timedelta(days=i) for i in range(31)]
    growth_dict = {entry['day']: entry['count'] for entry in user_growth_data}
    user_growth = {
        'labels': [date.strftime('%b %d') for date in dates],
        'data': [growth_dict.get(date.strftime('%Y-%m-%d'), 0) for date in dates],
        'total': sum(growth_dict.values())
    }

    # Mood statistics (last 7 days)
    mood_entries = MoodEntry.objects.filter(
        recorded_at__gte=timezone.now()-timedelta(days=7))
    mood_counts = mood_entries.values('mood_level').annotate(count=Count('id'))
    
    mood_stats = defaultdict(int)
    for entry in mood_counts:
        mood_stats[entry['mood_level']] = entry['count']
    
    total_mood_entries = sum(mood_stats.values())
    if total_mood_entries > 0:
        mood_stats.update({
            'values': [mood_stats.get(i, 0) for i in range(1, 6)],
            '1': round((mood_stats.get(1, 0) / total_mood_entries) * 100),
            '2': round((mood_stats.get(2, 0) / total_mood_entries) * 100),
            '3': round((mood_stats.get(3, 0) / total_mood_entries) * 100),
            '4': round((mood_stats.get(4, 0) / total_mood_entries) * 100),
            '5': round((mood_stats.get(5, 0) / total_mood_entries) * 100)
        })

    # Quiz statistics
    quiz_stats = {
        'avg_score': round(QuizAttempt.objects.aggregate(avg=Avg('score'))['avg'] or 0),
        'completion_rate': 0,
        'top_quizzes': [],
        'top_scores': []
    }
    
    # Calculate completion rate (quiz attempts vs students)
    student_count = User.objects.filter(user_type='STUDENT').count()
    if student_count > 0:
        quiz_stats['completion_rate'] = round(
            (QuizAttempt.objects.count() / student_count) * 100
        )
    
    # Get top 3 quizzes by average score
    top_quizzes = Quiz.objects.annotate(
        avg_score=Avg('quizattempt__score')
    ).order_by('-avg_score')[:3]
    
    quiz_stats['top_quizzes'] = [quiz.title for quiz in top_quizzes]
    quiz_stats['top_scores'] = [round(quiz.avg_score or 0) for quiz in top_quizzes]

    # Active users (last 7 days)
    active_users_count = User.objects.filter(
        last_login__gte=timezone.now()-timedelta(days=7)
    ).count()
    active_users_percentage = round((active_users_count / total_users) * 100) if total_users > 0 else 0

    # Content statistics
    content_stats = {
        'quizzes': Quiz.objects.count(),
        'resources': WellnessResource.objects.count(),
        'forum_posts': ForumPost.objects.count(),
        'events': Event.objects.count()
    }

    # Recent activity
    recent_users = User.objects.order_by('-date_joined')[:5]
    recent_quiz_attempts = QuizAttempt.objects.select_related('user', 'quiz').order_by('-completed_at')[:5]
    recent_mood_entries = MoodEntry.objects.select_related('user').order_by('-recorded_at')[:5]

    # Pending approvals
    pending_counselors = CounselorProfile.objects.filter(is_approved=False).select_related('user')

    context = {
        # Existing context
        'total_users': total_users,
        'new_users': new_users,
        'user_types': user_types,
        'content_stats': content_stats,
        'recent_users': recent_users,
        'recent_quiz_attempts': recent_quiz_attempts,
        'recent_mood_entries': recent_mood_entries,
        'pending_counselors': pending_counselors,
        
        # New data for visualizations
        'user_growth': user_growth,
        'mood_stats': mood_stats,
        'quiz_stats': quiz_stats,
        'active_users_count': active_users_count,
        'active_users_percentage': active_users_percentage
    }
    return render(request, 'admindashboard.html', context)


from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages
from django.utils import timezone
from django.db.models import Avg, Count, Q, F, ExpressionWrapper, DurationField
from django.core.exceptions import PermissionDenied
from .models import Appointment, User, WellnessResource, CounselorProfile, QuizAttempt, MoodEntry, Event
from .forms import CounselorProfileForm
from .templatetags.youtube_filters import youtube_id
import logging

logger = logging.getLogger(__name__)

@login_required
def counselor_dashboard(request):
    """
    Counselor dashboard with analytics and resource management
    """
    try:
        if not hasattr(request.user, 'counselor_profile'):
            return redirect('counselor_profile_required')
        
        counselor = request.user.counselor_profile
        
        if not counselor.is_complete():
            messages.warning(request, "Please complete your profile to access all features.")
            return redirect('complete_counselor_profile')
        
        # Get all video resources (simplified without ownership filter)
        video_resources = WellnessResource.objects.filter(
            resource_type='VIDEO'
        ).order_by('-created_at')[:5]
        
        enhanced_videos = []
        for resource in video_resources:
            yt_id = youtube_id(resource.video_embed_code) if resource.video_embed_code else None
            enhanced_videos.append({
                'resource': resource,
                'yt_id': yt_id,
                'thumbnail_url': f"https://img.youtube.com/vi/{yt_id}/hqdefault.jpg" if yt_id else None,
            })

        context = {
            'counselor': counselor,
            'upcoming_appointments': Appointment.objects.filter(
                counselor=counselor,
                datetime__gte=timezone.now()
            ).order_by('datetime')[:5],
            'recent_clients': User.objects.filter(
                appointments__counselor=counselor
            ).distinct().order_by('-date_joined')[:5],
            'video_resources': enhanced_videos,
            'engagement_metrics': get_client_engagement_metrics(counselor),
            'appointment_analytics': get_appointment_analytics(counselor),
            'recent_feedback': Appointment.objects.filter(
                counselor=counselor,
            ).order_by('-datetime')[:3],
            'events': Event.objects.filter(
                start_time__gte=timezone.now()
            ).order_by('start_time')[:5],
            'now': timezone.now(),
        }
        return render(request, 'counselor_dashboard.html', context)
    
    except Exception as e:
        logger.error(f"Dashboard error for counselor {request.user.id}: {str(e)}", exc_info=True)
        return render(request, 'errors/dashboard_error.html', {
            'error_message': "We encountered an issue loading your dashboard."
        }, status=500)

def get_client_engagement_metrics(counselor):
    """Calculate client engagement metrics"""
    try:
        # Calculate average session duration
        duration_expr = ExpressionWrapper(F('end_time') - F('start_time'), output_field=DurationField())
        avg_duration = Appointment.objects.filter(
            counselor=counselor,
            status='completed'
        ).annotate(duration=duration_expr).aggregate(
            avg_duration=Avg('duration')
        )['avg_duration']
        
        # Calculate client metrics
        total_clients = User.objects.filter(
            appointments__counselor=counselor
        ).distinct().count()
        
        active_clients = User.objects.filter(
            appointments__counselor=counselor,
            appointments__datetime__gte=timezone.now() - timezone.timedelta(days=30)
        ).distinct().count()
        
        return {
            'avg_session_minutes': round(avg_duration.total_seconds() / 60) if avg_duration else 0,
            'engagement_rate': round((active_clients / total_clients * 100) if total_clients > 0 else 0),
            'active_clients': active_clients,
        }
    except Exception as e:
        logger.error(f"Error calculating engagement metrics: {str(e)}")
        return {
            'avg_session_minutes': 0,
            'engagement_rate': 0,
            'active_clients': 0
        }

def get_appointment_analytics(counselor):
    """Get appointment analytics"""
    try:
        appointments = Appointment.objects.filter(counselor=counselor)
        total = appointments.count()
        cancelled = appointments.filter(status='cancelled').count()
        
        # Get busiest days (1=Sunday, 7=Saturday)
        busiest_days = appointments.annotate(
            day_of_week=ExtractWeekDay('datetime')
        ).values('day_of_week').annotate(
            count=Count('id')
        ).order_by('-count')[:3]
        
        return {
            'total_appointments': total,
            'cancellation_rate': round((cancelled / total * 100) if total > 0 else 0),
            'busiest_days': [{'day': day['day_of_week'], 'count': day['count']} for day in busiest_days],
        }
    except Exception as e:
        logger.error(f"Error getting appointment analytics: {str(e)}")
        return {
            'total_appointments': 0,
            'cancellation_rate': 0,
            'busiest_days': []
        }

@login_required
def counselor_profile_required(request):
    """View for counselors who need to complete their profile"""
    if request.user.user_type != 'COUNSELOR':
        messages.error(request, "This section is only available for counselors.")
        return redirect('home')
    
    if hasattr(request.user, 'counselor_profile'):
        if request.user.counselor_profile.is_complete():
            return redirect('counselor_dashboard')
        return redirect('complete_counselor_profile')
    
    return render(request, 'counselor/profile_required.html')

@login_required
def complete_counselor_profile(request):
    """Profile completion view"""
    if request.user.user_type != 'COUNSELOR':
        messages.error(request, "This section is only available for counselors.")
        return redirect('home')
    
    profile, created = CounselorProfile.objects.get_or_create(user=request.user)
    
    if profile.is_complete():
        messages.info(request, "Your profile is already complete.")
        return redirect('counselor_dashboard')
    
    if request.method == 'POST':
        form = CounselorProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile submitted for approval.")
            return redirect('counselor_dashboard')
        messages.error(request, "Please correct the errors below.")
    else:
        form = CounselorProfileForm(instance=profile, initial={
            'contact_email': request.user.email
        })
    
    return render(request, 'counselor/complete_profile.html', {
        'form': form,
        'progress': calculate_profile_completion(profile),
    })

def calculate_profile_completion(profile):
    """Calculate completion percentage (0-100)"""
    required_fields = [
        'specialization', 'qualifications', 'years_of_experience',
        'license_number', 'contact_email', 'available_hours'
    ]
    completed = sum(1 for field in required_fields if getattr(profile, field))
    return int((completed / len(required_fields)) * 100)


from django.utils import timezone
from .models import CounselorProfile, Appointment
from .forms import AppointmentBookingForm
from django.db.models import Case, When, Value, BooleanField



def counselor_list(request):
    counselors = CounselorProfile.objects.annotate(
        is_complete_flag=Case(
            When(
                specialization__isnull=False,
                qualifications__isnull=False,
                years_of_experience__isnull=False,
                license_number__isnull=False,
                contact_email__isnull=False,
                available_hours__isnull=False,
                then=Value(True)
            ),
            default=Value(False),
            output_field=BooleanField()
        )
    ).filter(
        is_approved=True,
        is_complete_flag=True
    ).select_related('user')
    
    context = {
        'counselors': counselors,
    }
    return render(request, 'counselor/list.html', context)




@login_required
def book_appointment(request, counselor_id):
    """Handle appointment booking with a specific counselor"""
    
    # Annotating is_complete_flag in the query based on whether required fields are filled
    try:
        counselor = CounselorProfile.objects.annotate(
            is_complete_flag=Case(
                When(
                    specialization__isnull=False,
                    qualifications__isnull=False,
                    years_of_experience__isnull=False,
                    license_number__isnull=False,
                    contact_email__isnull=False,
                    available_hours__isnull=False,
                    then=Value(True)
                ),
                default=Value(False),
                output_field=BooleanField()
            )
        ).get(
            id=counselor_id,
            is_approved=True,
            is_complete_flag=True  # Check if profile is complete
        )
    except CounselorProfile.DoesNotExist:
        messages.error(request, "Counselor not found or not available")
        return redirect('counselor_list')

    if request.method == 'POST':
        form = AppointmentBookingForm(request.POST)
        if form.is_valid():
            appointment = form.save(commit=False)
            appointment.counselor = counselor
            appointment.client = request.user
            appointment.status = 'scheduled'
            appointment.save()

            messages.success(request, "Appointment booked successfully!")
            return redirect('appointment_confirmation', appointment.id)
    else:
        form = AppointmentBookingForm(initial={
            'duration': 50,  # Default duration
            'session_type': 'individual'
        })

    context = {
        'counselor': counselor,
        'form': form,
        'available_slots': get_available_slots(counselor),
    }
    return render(request, 'counselor/book.html', context)


def get_available_slots(counselor):
    """Get available time slots for a counselor"""
    # This is a simplified version - you'd want to implement actual availability logic
    # based on the counselor's available_hours and existing appointments
    booked_appointments = Appointment.objects.filter(
        counselor=counselor,
        datetime__gte=timezone.now(),
        status__in=['scheduled', 'completed']
    ).values_list('datetime', flat=True)
    
    # Generate some sample slots (in a real app, use counselor's actual availability)
    from datetime import datetime, timedelta
    base_date = timezone.now().replace(hour=9, minute=0, second=0, microsecond=0)
    return [
        base_date + timedelta(days=i, hours=j) 
        for i in range(0, 14) 
        for j in [9, 11, 14, 16]  # 9am, 11am, 2pm, 4pm
        if (base_date + timedelta(days=i, hours=j)) > timezone.now()
        and (base_date + timedelta(days=i, hours=j)) not in booked_appointments
    ]


from django.shortcuts import render, get_object_or_404
from .models import Appointment

@login_required
def appointment_confirmation(request, appointment_id):
    """Handle appointment confirmation with a simple confirmation message"""
    appointment = get_object_or_404(Appointment, id=appointment_id, client=request.user)

    if appointment.status == 'scheduled':
        messages.success(request, "Your appointment has been successfully booked!")
        context = {
            'appointment': appointment,
        }
        return render(request, 'counselor/appointment_confirmation.html', context)
    else:
        messages.error(request, "Appointment not found or already confirmed")
        return redirect('counselor_list')




from django.views.generic import DetailView
from .models import CounselorProfile, Review
from .forms import ReviewForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.urls import reverse
from django.http import HttpResponseRedirect

class CounselorDetailView(DetailView):
    model = CounselorProfile
    template_name = 'counselors/counselor_detail.html'
    context_object_name = 'counselor'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        counselor = self.object
        
        # Calculate average rating
        reviews = Review.objects.filter(counselor=counselor)
        review_count = reviews.count()
        average_rating = reviews.aggregate(Avg('rating'))['rating__avg'] or 0
        
        # Get next available slots (simplified example - you'd implement your actual availability logic)
        from datetime import datetime, timedelta
        import random
        next_available_slots = []
        now = datetime.now()
        for i in range(1, 6):
            next_date = now + timedelta(days=i)
            if next_date.weekday() < 5:  # Weekdays only
                for hour in [9, 11, 14, 16]:  # Sample hours
                    next_available_slots.append(
                        datetime(next_date.year, next_date.month, next_date.day, hour, 0))
        
        # Split specialization string into list
        specialization_list = counselor.specialization.split(',') if counselor.specialization else []
        
        context.update({
            'reviews': reviews[:5],  # Show only 5 most recent reviews
            'average_rating': round(average_rating, 1),
            'review_count': review_count,
            'next_available_slots': next_available_slots[:5],  # Show next 5 slots
            'specialization_list': [s.strip() for s in specialization_list],
            'languages': ['English', 'Spanish']  # Example - replace with actual languages from your model
        })
        return context

def add_review(request, pk):
    counselor = get_object_or_404(CounselorProfile, pk=pk)
    
    if request.method == 'POST':
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.counselor = counselor
            review.user = request.user
            review.save()
            messages.success(request, 'Thank you for your review!')
            return HttpResponseRedirect(reverse('counselor_detail', kwargs={'pk': pk}))
    else:
        form = ReviewForm()
    
    return render(request, 'counselors/add_review.html', {
        'form': form,
        'counselor': counselor
    })
