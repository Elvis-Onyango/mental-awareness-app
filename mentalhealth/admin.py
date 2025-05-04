# admin.py
from django.contrib import admin
from django.utils.html import format_html
from django.contrib.auth.admin import UserAdmin
from .models import (
    User, CounselorProfile, Appointment, MentalHealthCategory, 
    Quiz, Question, AnswerOption, QuizAttempt, UserResponse,
    MoodEntry, WellnessResource, ForumPost, ForumComment,
    Event, UserWellnessJourney,Announcement
)

# Custom User Admin
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'user_type', 'is_verified', 'is_staff')
    list_filter = ('user_type', 'is_verified', 'is_staff', 'is_superuser')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    ordering = ('-date_joined',)
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal Info', {
            'fields': (
                'first_name', 'last_name', 'email', 
                'date_of_birth', 'phone_number', 
                'institution', 'profile_picture', 'bio'
            )
        }),
        ('Permissions', {
            'fields': (
                'user_type', 'is_verified', 'is_active',
                'is_staff', 'is_superuser', 'groups',
                'user_permissions'
            ),
        }),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'username', 'email', 'password1', 
                'password2', 'user_type'
            ),
        }),
    )
    
    def display_profile_pic(self, obj):
        if obj.profile_picture:
            return format_html(
                '<img src="{}" width="50" height="50" style="border-radius: 50%; object-fit: cover;" />',
                obj.profile_picture.url
            )
        return "No Image"
    display_profile_pic.short_description = 'Profile Picture'

admin.site.register(User, CustomUserAdmin)

# Counselor Profile Admin
@admin.register(CounselorProfile)
class CounselorProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'specialization', 'years_of_experience', 'is_approved')
    list_filter = ('is_approved', 'specialization')
    search_fields = ('user__username', 'qualifications', 'license_number')
    list_editable = ('is_approved',)
    raw_id_fields = ('user',)
    actions = ['approve_counselors', 'disapprove_counselors']
    
    def approve_counselors(self, request, queryset):
        queryset.update(is_approved=True)
    approve_counselors.short_description = "Approve selected counselors"
    
    def disapprove_counselors(self, request, queryset):
        queryset.update(is_approved=False)
    disapprove_counselors.short_description = "Disapprove selected counselors"

# Appointment Admin
class AppointmentAdmin(admin.ModelAdmin):
    list_display = (
        'datetime', 'counselor', 'client', 
        'session_type', 'status', 'duration'
    )
    list_filter = ('status', 'session_type', 'datetime')
    search_fields = (
        'counselor__user__username', 
        'client__username', 'notes'
    )
    date_hierarchy = 'datetime'
    raw_id_fields = ('counselor', 'client')
    readonly_fields = ('created_at', 'updated_at')
    list_select_related = ('counselor__user', 'client')
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'counselor__user', 'client'
        )

admin.site.register(Appointment, AppointmentAdmin)

# Mental Health Category Admin
@admin.register(MentalHealthCategory)
class MentalHealthCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'display_icon')
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}  # Add slug field to model if needed
    
    def display_icon(self, obj):
        return format_html('<i class="{}"></i>', obj.icon)
    display_icon.short_description = 'Icon'

# Quiz Admin with Inline Questions
class AnswerOptionInline(admin.TabularInline):
    model = AnswerOption
    extra = 1
    min_num = 2

class QuestionInline(admin.TabularInline):
    model = Question
    extra = 1
    inlines = [AnswerOptionInline]
    fields = ('text', 'question_type', 'points', 'explanation')
    show_change_link = True

@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'difficulty', 'is_active', 'question_count')
    list_filter = ('category', 'difficulty', 'is_active')
    search_fields = ('title', 'description')
    inlines = [QuestionInline]
    readonly_fields = ('created_at', 'updated_at')
    
    def question_count(self, obj):
        return obj.questions.count()
    question_count.short_description = 'Questions'

# Question Admin with Answer Options
@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('text', 'quiz', 'question_type', 'points')
    list_filter = ('question_type', 'quiz__category')
    search_fields = ('text', 'explanation')
    inlines = [AnswerOptionInline]
    list_select_related = ('quiz',)
    raw_id_fields = ('quiz',)

# Quiz Attempt Admin with Responses
class UserResponseInline(admin.TabularInline):
    model = UserResponse
    extra = 0
    readonly_fields = ('responded_at', 'points_earned')
    can_delete = False
    
    def has_add_permission(self, request, obj):
        return False

@admin.register(QuizAttempt)
class QuizAttemptAdmin(admin.ModelAdmin):
    list_display = ('user', 'quiz', 'started_at', 'completed_at', 'score', 'is_completed')
    list_filter = ('quiz', 'is_completed')
    search_fields = ('user__username', 'quiz__title')
    readonly_fields = ('started_at', 'completed_at', 'score')
    inlines = [UserResponseInline]
    date_hierarchy = 'started_at'
    list_select_related = ('user', 'quiz')
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'user', 'quiz'
        )

# Mood Entry Admin
@admin.register(MoodEntry)
class MoodEntryAdmin(admin.ModelAdmin):
    list_display = ('user', 'mood_level_display', 'recorded_at', 'related_quiz')
    list_filter = ('mood_level', 'recorded_at')
    search_fields = ('user__username', 'notes')
    date_hierarchy = 'recorded_at'
    readonly_fields = ('recorded_at',)
    raw_id_fields = ('user', 'related_quiz')
    
    def mood_level_display(self, obj):
        return obj.get_mood_level_display()
    mood_level_display.short_description = 'Mood Level'

# Wellness Resource Admin
@admin.register(WellnessResource)
class WellnessResourceAdmin(admin.ModelAdmin):
    list_display = (
        'title', 'resource_type', 'category', 
        'is_featured', 'created_at'
    )
    list_filter = ('resource_type', 'category', 'is_featured')
    search_fields = ('title', 'content')
    readonly_fields = ('created_at', 'preview_video', 'preview_thumbnail')
    list_editable = ('is_featured',)
    date_hierarchy = 'created_at'
    
    fieldsets = (
        (None, {
            'fields': ('title', 'resource_type', 'category', 'content', 'duration')
        }),
        ('Media', {
            'fields': ('thumbnail', 'preview_thumbnail'),
        }),
        ('Video Options', {
            'fields': ('video_file', 'preview_video', 'video_embed_code'),
            'classes': ('collapse',),
        }),
        ('External Content', {
            'fields': ('external_link',),
        }),
        ('Metadata', {
            'fields': ('is_featured', 'created_at'),
        }),
    )
    
    def preview_video(self, obj):
        if obj.video_file:
            return format_html(
                '<video width="300" controls><source src="{}"></video>',
                obj.video_file.url
            )
        elif obj.video_embed_code:
            return format_html(obj.get_video_html())
        return "No video available"
    preview_video.short_description = 'Video Preview'
    
    def preview_thumbnail(self, obj):
        if obj.thumbnail:
            return format_html(
                '<img src="{}" width="150" style="max-height: 150px;" />',
                obj.thumbnail.url
            )
        return "No thumbnail"
    preview_thumbnail.short_description = 'Thumbnail Preview'

# Forum Admin
class ForumCommentInline(admin.TabularInline):
    model = ForumComment
    extra = 0
    readonly_fields = ('created_at',)
    raw_id_fields = ('user',)

@admin.register(ForumPost)
class ForumPostAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'category', 'created_at', 'comment_count')
    list_filter = ('category', 'created_at', 'is_anonymous')
    search_fields = ('title', 'content', 'user__username')
    inlines = [ForumCommentInline]
    date_hierarchy = 'created_at'
    raw_id_fields = ('user', 'category')
    
    def comment_count(self, obj):
        return obj.comments.count()
    comment_count.short_description = 'Comments'

@admin.register(ForumComment)
class ForumCommentAdmin(admin.ModelAdmin):
    list_display = ('post', 'user', 'created_at', 'is_anonymous')
    list_filter = ('created_at', 'is_anonymous')
    search_fields = ('content', 'user__username', 'post__title')
    date_hierarchy = 'created_at'
    raw_id_fields = ('post', 'user')

# Event Admin
@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = (
        'title', 'start_time', 'end_time', 
        'location', 'organizer', 'attendee_count'
    )
    list_filter = ('start_time', 'is_virtual')
    search_fields = ('title', 'description', 'organizer__username')
    date_hierarchy = 'start_time'
    filter_horizontal = ('attendees',)
    raw_id_fields = ('organizer',)
    readonly_fields = ('created_at', 'preview_image')
    
    fieldsets = (
        (None, {
            'fields': ('title', 'description', 'organizer')
        }),
        ('Time & Location', {
            'fields': ('start_time', 'end_time', 'location', 'is_virtual')
        }),
        ('Media', {
            'fields': ('image', 'preview_image', 'meeting_link')
        }),
        ('Attendees', {
            'fields': ('attendees',),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    def attendee_count(self, obj):
        return obj.attendees.count()
    attendee_count.short_description = 'Attendees'
    
    def preview_image(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" width="150" style="max-height: 150px;" />',
                obj.image.url
            )
        return "No image"
    preview_image.short_description = 'Image Preview'

# User Wellness Journey Admin
@admin.register(UserWellnessJourney)
class UserWellnessJourneyAdmin(admin.ModelAdmin):
    list_display = ('user', 'joined_at', 'current_streak', 'longest_streak')
    search_fields = ('user__username', 'goals')
    readonly_fields = ('joined_at', 'last_activity')
    raw_id_fields = ('user',)
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')


class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ('title', 'priority', 'created_by', 'created_at', 'is_published')
    list_filter = ('priority', 'is_published', 'created_at')
    search_fields = ('title', 'message', 'created_by__username')
    filter_horizontal = ('recipients',)
    readonly_fields = ('published_at',)
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'message', 'priority')
        }),
        ('Delivery Options', {
            'fields': ('recipients', 'send_email', 'scheduled_at')
        }),
        ('Publication Status', {
            'fields': ('is_published', 'published_at', 'created_by')
        }),
    )

    def save_model(self, request, obj, form, change):
        if not obj.pk:  # Only set created_by if this is a new announcement
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
admin.site.register(Announcement, AnnouncementAdmin)