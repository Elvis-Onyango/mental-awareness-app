from django.db import models
from django.contrib.auth.models import AbstractUser,  Group, Permission,BaseUserManager
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from django.utils.text import slugify



class CustomUserManager(BaseUserManager):
    def create_user(self, username, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(username=username, email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('user_type', 'ADMIN')

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(username, email, password, **extra_fields)


class User(AbstractUser):
    USER_TYPES = (
        ('STUDENT', 'Student'),
        ('COUNSELOR', 'Counselor'),
        ('ADMIN', 'Admin'),
    )
    
    user_type = models.CharField(max_length=10, choices=USER_TYPES, default='STUDENT')
    date_of_birth = models.DateField(null=True, blank=True)
    phone_number = models.CharField(max_length=15, blank=True)
    institution = models.CharField(max_length=100, blank=True)
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True)
    bio = models.TextField(blank=True)
    is_verified = models.BooleanField(default=False)

    groups = models.ManyToManyField(
        Group,
        related_name="custom_user_groups",  # Adjust related_name to avoid conflicts
        blank=True
    )
    user_permissions = models.ManyToManyField(
        Permission,
        related_name="custom_user_permissions",  # Adjust related_name to avoid conflicts
        blank=True
    )

    def is_counselor_user(self):
        """Check if user is a counselor (by type or flag)"""
        return self.user_type == 'COUNSELOR' or getattr(self, 'is_counselor', False)


    @property
    def engagement_metrics(self):
        metrics, created = UserEngagementMetrics.objects.get_or_create(user=self)
        return metrics
    
    def log_activity(self, action, **kwargs):
        """Helper method to log user activities"""
        UserActivityLog.objects.create(
            user=self,
            action=action,
            ip_address=kwargs.get('ip_address'),
            device_info=kwargs.get('device_info'),
            additional_data=kwargs.get('data', {})
        )
        # Update engagement metrics
        self.engagement_metrics.last_active = timezone.now()
        
        # Increment relevant counters
        if action == 'QUIZ_COMPLETE':
            self.engagement_metrics.total_quiz_attempts += 1
        elif action == 'RESOURCE_VIEW':
            self.engagement_metrics.total_resources_viewed += 1
        elif action == 'APPOINTMENT_BOOK':
            self.engagement_metrics.total_appointments += 1
        elif action == 'FORUM_POST':
            self.engagement_metrics.total_forum_posts += 1
        elif action == 'MOOD_ENTRY':
            self.engagement_metrics.total_mood_entries += 1
        elif action == 'LOGIN':
            self.engagement_metrics.total_logins += 1
            
        self.engagement_metrics.save()
        self.engagement_metrics.update_engagement_score()    


    def __str__(self):
        return f"{self.username} ({self.get_user_type_display()})"

class CounselorProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='counselor_profile')
    specialization = models.CharField(max_length=100)
    qualifications = models.TextField()
    years_of_experience = models.PositiveIntegerField()
    license_number = models.CharField(max_length=50)
    available_hours = models.CharField(max_length=100)
    contact_email = models.EmailField()
    appointment_link = models.URLField(blank=True)
    is_approved = models.BooleanField(default=False)
    
    def is_complete(self):
        """Check if profile has all required fields filled"""
        required_fields = [
        'specialization', 'qualifications', 'years_of_experience',
        'license_number', 'contact_email', 'available_hours'
        ]
        return all(getattr(self, field) for field in required_fields)

    @property
    def performance_metrics(self):
        metrics, created = CounselorPerformance.objects.get_or_create(counselor=self)
        return metrics
    
    def update_performance_metrics(self):
        """Update all performance metrics"""
        self.performance_metrics.update_metrics()
    


    def __str__(self):
        return f"Counselor Profile for {self.user.username}"


class Appointment(models.Model):
    STATUS_CHOICES = (
        ('scheduled', 'Scheduled'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('no_show', 'No Show'),
    )
    
    SESSION_TYPES = (
        ('individual', 'Individual Therapy'),
        ('group', 'Group Therapy'),
        ('consultation', 'Consultation'),
    )
    
    counselor = models.ForeignKey(CounselorProfile, on_delete=models.CASCADE, related_name='appointments')
    client = models.ForeignKey(User, on_delete=models.CASCADE, related_name='appointments')
    datetime = models.DateTimeField()
    duration = models.PositiveIntegerField(help_text="Duration in minutes", default=50)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='scheduled')
    session_type = models.CharField(max_length=12, choices=SESSION_TYPES, default='individual')
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['datetime']
    
    def __str__(self):
        return f"Appointment with {self.client.username} on {self.datetime}"


class MentalHealthCategory(models.Model):
    name = models.CharField(max_length=50)
    slug = models.SlugField(unique=True, blank=True)  
    description = models.TextField()
    icon = models.CharField(max_length=30, help_text="Icon class from icon library")


    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    
    def __str__(self):
        return self.name


class Quiz(models.Model):
    DIFFICULTY_LEVELS = (
        ('EASY', 'Easy'),
        ('MEDIUM', 'Medium'),
        ('HARD', 'Hard'),
    )
    
    title = models.CharField(max_length=200)
    description = models.TextField()
    category = models.ForeignKey(MentalHealthCategory, on_delete=models.SET_NULL, null=True)
    difficulty = models.CharField(max_length=10, choices=DIFFICULTY_LEVELS, default='MEDIUM')
    time_limit = models.PositiveIntegerField(help_text="Time limit in minutes", null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    passing_score = models.FloatField(default=70.0, validators=[MinValueValidator(0), MaxValueValidator(100)])
    
    def __str__(self):
        return self.title
    
    @property
    def total_points(self):
        return sum(question.points for question in self.questions.all())


    @property
    def analytics(self):
        analytics, created = ContentAnalytics.objects.get_or_create(
            content_type='quiz',
            content_id=self.id
        )
        return analytics
    
    def increment_views(self):
        """Increment view count for this quiz"""
        self.analytics.views += 1
        self.analytics.save()
    

class Question(models.Model):
    QUESTION_TYPES = (
        ('MC', 'Multiple Choice'),
        ('TF', 'True/False'),
        ('OE', 'Open Ended'),
    )
    
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='questions')
    text = models.TextField()
    question_type = models.CharField(max_length=2, choices=QUESTION_TYPES)
    points = models.PositiveIntegerField(default=1)
    explanation = models.TextField(blank=True, help_text="Explanation to show after answering")
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.text[:50]}... ({self.get_question_type_display()})"

class AnswerOption(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='options')
    text = models.CharField(max_length=255)
    is_correct = models.BooleanField(default=False)
    keywords = models.TextField(blank=True, help_text="Comma-separated keywords for open-ended questions")
    
    def __str__(self):
        return f"{self.text[:30]}... ({'Correct' if self.is_correct else 'Incorrect'})"

class QuizAttempt(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='quiz_attempts')
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE)
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    score = models.FloatField(null=True, blank=True)
    is_completed = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-started_at']
    
    def __str__(self):
        return f"{self.user.username}'s attempt on {self.quiz.title}"
    
    @property
    def duration(self):
        if self.completed_at:
            return (self.completed_at - self.started_at).total_seconds() // 60
        return None
    
    def calculate_score(self):
        responses = self.responses.all()
        total_possible = self.quiz.total_points
        earned = sum(response.points_earned for response in responses if response.points_earned is not None)
        self.score = (earned / total_possible) * 100 if total_possible > 0 else 0
        self.save()
        return self.score

class UserResponse(models.Model):
    attempt = models.ForeignKey(QuizAttempt, on_delete=models.CASCADE, related_name='responses')
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    selected_option = models.ForeignKey(AnswerOption, on_delete=models.SET_NULL, null=True, blank=True)
    text_response = models.TextField(blank=True)
    points_earned = models.FloatField(null=True, blank=True)
    responded_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Response to {self.question.text[:30]}..."
    
    def evaluate_response(self):
        if self.question.question_type == 'OE':
            # Analyze open-ended response
            keywords = self.question.options.filter(is_correct=True).first().keywords.split(',')
            user_text = self.text_response.lower()
            matches = sum(1 for keyword in keywords if keyword.strip().lower() in user_text)
            total_keywords = len(keywords)
            self.points_earned = (matches / total_keywords) * self.question.points if total_keywords > 0 else 0
        else:
            # For MC/TF questions
            if self.selected_option and self.selected_option.is_correct:
                self.points_earned = self.question.points
            else:
                self.points_earned = 0
        self.save()
        return self.points_earned

class MoodEntry(models.Model):
    MOOD_CHOICES = (
        (1, 'Very Negative'),
        (2, 'Negative'),
        (3, 'Neutral'),
        (4, 'Positive'),
        (5, 'Very Positive'),
    )
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='mood_entries')
    mood_level = models.PositiveSmallIntegerField(choices=MOOD_CHOICES)
    notes = models.TextField(blank=True)
    recorded_at = models.DateTimeField(default=timezone.now)
    related_quiz = models.ForeignKey(QuizAttempt, on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        verbose_name_plural = 'Mood entries'
        ordering = ['-recorded_at']
    
    def __str__(self):
        return f"{self.user.username}: {self.get_mood_level_display()} at {self.recorded_at}"

    def get_recommended_difficulty(self):
        if self.mood_level in [1, 5]:
            return 'HARD'
        elif self.mood_level in [2, 4]:
            return 'MEDIUM'
        else:
             return 'EASY'    

class WellnessResource(models.Model):
    RESOURCE_TYPES = (
        ('ARTICLE', 'Article'),
        ('VIDEO', 'Video'),
        ('PODCAST', 'Podcast'),
        ('TOOL', 'Interactive Tool'),
        ('BOOK', 'Book Recommendation'),
    )
    
    title = models.CharField(max_length=200)
    resource_type = models.CharField(max_length=10, choices=RESOURCE_TYPES)
    category = models.ForeignKey(MentalHealthCategory, on_delete=models.SET_NULL, null=True)
    content = models.TextField(blank=True)
    
    # For external links (articles, podcasts, etc.)
    external_link = models.URLField(blank=True)
    
    # For uploaded video files
    video_file = models.FileField(
        upload_to='resource_videos/',
        blank=True,
        null=True,
        help_text="Upload video file (for VIDEO resource type)"
    )
    
    # For embedded videos (YouTube/Vimeo)
    video_embed_code = models.CharField(
        max_length=500, 
        blank=True,
        help_text="Paste YouTube/Vimeo embed code or just the video ID"
    )
    
    thumbnail = models.ImageField(upload_to='resource_thumbnails/', blank=True)
    duration = models.CharField(max_length=20, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_featured = models.BooleanField(default=False)
    
    def __str__(self):
        return self.title
    
    def clean(self):
        """Validate video-related fields"""
        if self.resource_type == 'VIDEO':
            if not self.video_file and not self.video_embed_code:
                raise ValidationError("Video resources require either a video file or embed code")
            if self.video_file and self.video_embed_code:
                raise ValidationError("Cannot have both video file and embed code")
    
    def save(self, *args, **kwargs):
        """Handle file cleanup"""
        try:
            old = WellnessResource.objects.get(pk=self.pk)
            if old.video_file and old.video_file != self.video_file:
                old.video_file.delete(save=False)
        except WellnessResource.DoesNotExist:
            pass
        super().save(*args, **kwargs)
    
    def get_video_html(self):
        """Generate HTML for video display"""
        if self.video_embed_code:
            # If it looks like just a video ID
            if len(self.video_embed_code) in (11, 9):  # Typical YouTube/Vimeo ID lengths
                return f'<iframe width="560" height="315" src="https://www.youtube.com/embed/{self.video_embed_code}" frameborder="0" allowfullscreen></iframe>'
            # If it's full embed code
            return self.video_embed_code
        return None


    @property
    def analytics(self):
        analytics, created = ContentAnalytics.objects.get_or_create(
            content_type='resource',
            content_id=self.id
        )
        return analytics
    
    def increment_views(self):
        """Increment view count for this resource"""
        self.analytics.views += 1
        self.analytics.save()    

class ForumPost(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    content = models.TextField()
    category = models.ForeignKey(MentalHealthCategory, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_anonymous = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return self.title

class ForumComment(models.Model):
    post = models.ForeignKey(ForumPost, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_anonymous = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['created_at']
    
    def __str__(self):
        return f"Comment by {self.user.username} on {self.post.title}"

class Event(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    location = models.CharField(max_length=200)
    is_virtual = models.BooleanField(default=False)
    meeting_link = models.URLField(blank=True)
    organizer = models.ForeignKey(User, on_delete=models.CASCADE)
    attendees = models.ManyToManyField(User, related_name='events_attending', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    image = models.ImageField(upload_to='event_images/', blank=True)
    
    def __str__(self):
        return self.title

class UserWellnessJourney(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='wellness_journey')
    joined_at = models.DateTimeField(auto_now_add=True)
    last_activity = models.DateTimeField(auto_now=True)
    current_streak = models.PositiveIntegerField(default=0)
    longest_streak = models.PositiveIntegerField(default=0)
    goals = models.TextField(blank=True)
    
    def __str__(self):
        return f"Wellness Journey for {self.user.username}"
    
    def update_streak(self):
        # Logic to calculate and update streaks based on activity
        pass

class Review(models.Model):
    counselor = models.ForeignKey(CounselorProfile, on_delete=models.CASCADE, related_name='counselor_reviews')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    rating = models.PositiveSmallIntegerField(
        choices=[(1, '1 Star'), (2, '2 Stars'), (3, '3 Stars'), (4, '4 Stars'), (5, '5 Stars')]
    )
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.rating} star review by {self.user.username}"


class UserActivityLog(models.Model):
    """Tracks all user activities across the platform"""
    ACTION_CHOICES = (
        ('LOGIN', 'User Login'),
        ('LOGOUT', 'User Logout'),
        ('QUIZ_START', 'Quiz Started'),
        ('QUIZ_COMPLETE', 'Quiz Completed'),
        ('RESOURCE_VIEW', 'Resource Viewed'),
        ('APPOINTMENT_BOOK', 'Appointment Booked'),
        ('APPOINTMENT_CANCEL', 'Appointment Cancelled'),
        ('FORUM_POST', 'Forum Post Created'),
        ('FORUM_COMMENT', 'Forum Comment Added'),
        ('MOOD_ENTRY', 'Mood Recorded'),
        ('PROFILE_UPDATE', 'Profile Updated'),
    )
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='activity_logs')
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    timestamp = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    device_info = models.CharField(max_length=255, blank=True)
    additional_data = models.JSONField(default=dict, blank=True)
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['user', 'action']),
            models.Index(fields=['timestamp']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.get_action_display()} at {self.timestamp}"

class PlatformAnalytics(models.Model):
    """Aggregated platform-wide analytics data"""
    date = models.DateField(unique=True)
    active_users = models.PositiveIntegerField(default=0)
    new_registrations = models.PositiveIntegerField(default=0)
    quiz_attempts = models.PositiveIntegerField(default=0)
    resource_views = models.PositiveIntegerField(default=0)
    appointments_scheduled = models.PositiveIntegerField(default=0)
    forum_posts = models.PositiveIntegerField(default=0)
    mood_entries = models.PositiveIntegerField(default=0)
    
    class Meta:
        verbose_name_plural = 'Platform Analytics'
        ordering = ['-date']
    
    def __str__(self):
        return f"Platform Analytics for {self.date}"

class UserEngagementMetrics(models.Model):
    """Tracks individual user engagement metrics"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='engagement_metrics')
    last_active = models.DateTimeField(auto_now=True)
    total_logins = models.PositiveIntegerField(default=0)
    total_quiz_attempts = models.PositiveIntegerField(default=0)
    total_resources_viewed = models.PositiveIntegerField(default=0)
    total_appointments = models.PositiveIntegerField(default=0)
    total_forum_posts = models.PositiveIntegerField(default=0)
    total_mood_entries = models.PositiveIntegerField(default=0)
    engagement_score = models.FloatField(default=0.0)
    
    def update_engagement_score(self):
        """Calculate a composite engagement score"""
        weights = {
            'total_logins': 0.2,
            'total_quiz_attempts': 0.25,
            'total_resources_viewed': 0.2,
            'total_appointments': 0.15,
            'total_forum_posts': 0.1,
            'total_mood_entries': 0.1,
        }
        
        max_values = {
            'total_logins': 30,  # per month
            'total_quiz_attempts': 10,
            'total_resources_viewed': 20,
            'total_appointments': 4,
            'total_forum_posts': 15,
            'total_mood_entries': 30,
        }
        
        score = 0
        for metric, weight in weights.items():
            value = min(getattr(self, metric), max_values.get(metric, 100))
            normalized = value / max_values.get(metric, 1)
            score += normalized * weight
        
        self.engagement_score = min(score * 100, 100)  # Scale to 100
        self.save()
    
    def __str__(self):
        return f"Engagement Metrics for {self.user.username}"

class CounselorPerformance(models.Model):
    """Tracks performance metrics for counselors"""
    counselor = models.OneToOneField(CounselorProfile, on_delete=models.CASCADE, related_name='performance_metrics')
    total_appointments = models.PositiveIntegerField(default=0)
    completed_appointments = models.PositiveIntegerField(default=0)
    cancellation_rate = models.FloatField(default=0.0)
    average_rating = models.FloatField(default=0.0)
    response_time = models.DurationField(null=True, blank=True)  # Average response time to messages
    client_retention_rate = models.FloatField(default=0.0)
    last_updated = models.DateTimeField(auto_now=True)
    
    def update_metrics(self):
        """Calculate all performance metrics"""
        appointments = self.counselor.appointments.all()
        reviews = self.counselor.counselor_reviews.all()
        
        self.total_appointments = appointments.count()
        self.completed_appointments = appointments.filter(status='completed').count()
        
        if self.total_appointments > 0:
            cancelled = appointments.filter(status='cancelled').count()
            self.cancellation_rate = (cancelled / self.total_appointments) * 100
            
            if reviews.exists():
                self.average_rating = reviews.aggregate(models.Avg('rating'))['rating__avg']
            
            # Calculate client retention (simplified)
            unique_clients = appointments.values('client').distinct().count()
            returning_clients = appointments.values('client').annotate(
                count=models.Count('id')).filter(count__gt=1).count()
            
            if unique_clients > 0:
                self.client_retention_rate = (returning_clients / unique_clients) * 100
        
        self.save()
    
    def __str__(self):
        return f"Performance Metrics for {self.counselor.user.username}"

class ContentAnalytics(models.Model):
    """Tracks engagement with different content pieces"""
    content_type = models.CharField(max_length=50)  # e.g., 'quiz', 'resource', 'forum_post'
    content_id = models.PositiveIntegerField()
    views = models.PositiveIntegerField(default=0)
    engagements = models.PositiveIntegerField(default=0)  # Clicks, time spent, etc.
    shares = models.PositiveIntegerField(default=0)
    last_updated = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('content_type', 'content_id')
        verbose_name_plural = 'Content Analytics'
    
    def __str__(self):
        return f"Analytics for {self.content_type} #{self.content_id}"




class Announcement(models.Model):
    PRIORITY_CHOICES = [
        ('LOW', 'Low'),
        ('MEDIUM', 'Medium'),
        ('HIGH', 'High'),
        ('URGENT', 'Urgent'),
    ]
    
    title = models.CharField(max_length=200)
    message = models.TextField()
    recipients = models.ManyToManyField(User, related_name='announcements')
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='created_announcements'
    )
    priority = models.CharField(
        max_length=10,
        choices=PRIORITY_CHOICES,
        default='MEDIUM'
    )
    send_email = models.BooleanField(default=True)
    is_published = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    scheduled_at = models.DateTimeField(null=True, blank=True)
    published_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Announcement'
        verbose_name_plural = 'Announcements'

    def __str__(self):
        return f"{self.title} (Priority: {self.get_priority_display()})"

    def save(self, *args, **kwargs):
        # Set published_at if is_published is being set to True
        if self.is_published and not self.published_at:
            self.published_at = timezone.now()
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('admin_announcement_detail', args=[str(self.id)])

