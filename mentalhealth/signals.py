from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from .models import UserWellnessJourney

User = get_user_model()

@receiver(post_save, sender=User)
def create_user_wellness_journey(sender, instance, created, **kwargs):
    if created:
        UserWellnessJourney.objects.create(user=instance)




from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.contrib.auth.signals import user_logged_in, user_logged_out
from .models import UserActivityLog, PlatformAnalytics,QuizAttempt

@receiver(user_logged_in)
def log_user_login(sender, request, user, **kwargs):
    user.log_activity(
        'LOGIN',
        ip_address=request.META.get('REMOTE_ADDR'),
        device_info=request.META.get('HTTP_USER_AGENT', '')
    )

@receiver(user_logged_out)
def log_user_logout(sender, request, user, **kwargs):
    user.log_activity(
        'LOGOUT',
        ip_address=request.META.get('REMOTE_ADDR'),
        device_info=request.META.get('HTTP_USER_AGENT', '')
    )

@receiver(post_save, sender=QuizAttempt)
def log_quiz_attempt(sender, instance, created, **kwargs):
    if created:
        instance.user.log_activity(
            'QUIZ_START',
            data={'quiz_id': instance.quiz.id, 'quiz_title': instance.quiz.title}
        )
    elif instance.is_completed:
        instance.user.log_activity(
            'QUIZ_COMPLETE',
            data={
                'quiz_id': instance.quiz.id,
                'quiz_title': instance.quiz.title,
                'score': instance.score
            }
        )



@receiver(post_save, sender=UserActivityLog)
def update_daily_analytics(sender, instance, created, **kwargs):
    if created:
        date = instance.timestamp.date()
        analytics, created = PlatformAnalytics.objects.get_or_create(date=date)
        
        # Update relevant counters based on action
        if instance.action == 'LOGIN':
            analytics.active_users += 1
        elif instance.action == 'QUIZ_COMPLETE':
            analytics.quiz_attempts += 1
        elif instance.action == 'RESOURCE_VIEW':
            analytics.resource_views += 1
        elif instance.action == 'APPOINTMENT_BOOK':
            analytics.appointments_scheduled += 1
        elif instance.action == 'FORUM_POST':
            analytics.forum_posts += 1
        elif instance.action == 'MOOD_ENTRY':
            analytics.mood_entries += 1
            
        analytics.save()
