# accounts/forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import User,CounselorProfile,MoodEntry, MentalHealthCategory

class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    date_of_birth = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'}),
        required=False
    )
    
    class Meta:
        model = User
        fields = (
            'username',
            'email',
            'password1',
            'password2',
            'user_type',
            'date_of_birth',
            'phone_number',
            'institution'
        )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add Tailwind classes to all fields
        for field_name, field in self.fields.items():
            field.widget.attrs.update({
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500'
            })

class CustomAuthenticationForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({
            'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500'
        })
        self.fields['password'].widget.attrs.update({
            'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500'
        })



from .models import ForumPost, ForumComment

class ForumPostForm(forms.ModelForm):
    class Meta:
        model = ForumPost
        fields = ['title', 'content', 'category', 'is_anonymous']
        widgets = {
            'content': forms.Textarea(attrs={'rows': 5}),
        }

class ForumCommentForm(forms.ModelForm):
    class Meta:
        model = ForumComment
        fields = ['content', 'is_anonymous']
        widgets = {
            'content': forms.Textarea(attrs={'rows': 3}),
        }



from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from .models import CounselorProfile

class CounselorProfileForm(forms.ModelForm):
    # Custom field configurations
    years_of_experience = forms.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(70)],
        widget=forms.NumberInput(attrs={
            'min': 0,
            'max': 70,
            'class': 'form-control'
        }),
        help_text="Total years of professional counseling experience"
    )
    
    available_hours = forms.CharField(
        widget=forms.Textarea(attrs={
            'rows': 3,
            'class': 'form-control',
            'placeholder': 'Example: Monday-Friday 9am-5pm'
        }),
        help_text="Your regular available hours for sessions"
    )
    
    class Meta:
        model = CounselorProfile
        fields = [
            'specialization',
            'years_of_experience',
            'qualifications',
            'license_number',
            'available_hours',
            'contact_email',
            'appointment_link'
        ]
        widgets = {
            'specialization': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Your areas of expertise'
            }),
            'qualifications': forms.Textarea(attrs={
                'rows': 4,
                'class': 'form-control'
            }),
            'license_number': forms.TextInput(attrs={
                'class': 'form-control'
            }),
            'contact_email': forms.EmailInput(attrs={
                'class': 'form-control'
            }),
            'appointment_link': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://'
            })
        }
        help_texts = {
            'contact_email': "Primary email for client communications",
            'appointment_link': "Your online scheduling link (if available)"
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set required attribute for required fields
        for field in self.fields:
            if self.fields[field].required:
                self.fields[field].widget.attrs['required'] = 'required'

    def clean_years_of_experience(self):
        years = self.cleaned_data.get('years_of_experience')
        if years and years > 50:
            raise ValidationError("Please verify your experience duration. Contact support if accurate.")
        return years

    def clean_license_number(self):
        license_num = self.cleaned_data.get('license_number')
        if license_num and len(license_num) < 6:
            raise ValidationError("License number appears too short. Please verify.")
        return license_num



from .models import Appointment

class AppointmentBookingForm(forms.ModelForm):
    class Meta:
        model = Appointment
        fields = ['datetime', 'duration', 'session_type', 'notes']
        widgets = {
            'datetime': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'duration': forms.NumberInput(attrs={'min': 30, 'max': 120}),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }
        help_texts = {
            'duration': "Duration in minutes (30-120)",
        }     

from .models import Review

class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['rating', 'comment']
        widgets = {
            'comment': forms.Textarea(attrs={'rows': 4}),
        }







class MoodAssessmentForm(forms.Form):
    MOOD_CHOICES = (
        (1, '😞 Very Negative'),
        (2, '😕 Negative'),
        (3, '😐 Neutral'),
        (4, '😊 Positive'),
        (5, '😁 Very Positive'),
    )
    
    mood_level = forms.ChoiceField(
        choices=MOOD_CHOICES,
        widget=forms.RadioSelect(attrs={'class': 'btn-check'}),
        label="How are you feeling today?",
        required=True
    )

class QuickMoodEntryForm(forms.ModelForm):
    class Meta:
        model = MoodEntry
        fields = ['mood_level', 'notes']
        widgets = {
            'mood_level': forms.RadioSelect(choices=MoodEntry.MOOD_CHOICES),
            'notes': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Optional notes about your mood...'}),
        }



from .models import User, CounselorProfile, Quiz, WellnessResource, Announcement



class CounselorApprovalForm(forms.ModelForm):
    APPROVAL_CHOICES = [
        ('approve', 'Approve Application'),
        ('reject', 'Reject Application'),
    ]
    
    approval_action = forms.ChoiceField(
        choices=APPROVAL_CHOICES,
        widget=forms.RadioSelect,
        required=True
    )
    notes = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 3}),
        required=False,
        help_text="Optional notes about this decision"
    )
    
    class Meta:
        model = CounselorProfile
        fields = ['specialization', 'qualifications', 'years_of_experience', 
                 'license_number', 'available_hours', 'contact_email']
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            if field != 'approval_action' and field != 'notes':
                self.fields[field].disabled = True

class QuizForm(forms.ModelForm):
    category = forms.ModelChoiceField(
        queryset=MentalHealthCategory.objects.all(),
        required=False
    )
    passing_score = forms.FloatField(
        min_value=0,
        max_value=100,
        widget=forms.NumberInput(attrs={'step': '0.1'})
    )
    
    class Meta:
        model = Quiz
        fields = ['title', 'description', 'category', 'difficulty', 
                 'time_limit', 'passing_score', 'is_active']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }

class ResourceForm(forms.ModelForm):
    category = forms.ModelChoiceField(
        queryset=MentalHealthCategory.objects.all(),
        required=False
    )
    
    class Meta:
        model = WellnessResource
        fields = ['title', 'resource_type', 'category', 'content',
                 'external_link', 'video_file', 'video_embed_code',
                 'thumbnail', 'duration', 'is_featured']
        widgets = {
            'content': forms.Textarea(attrs={'rows': 5}),
            'video_embed_code': forms.Textarea(attrs={'rows': 2}),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        resource_type = cleaned_data.get('resource_type')
        video_file = cleaned_data.get('video_file')
        video_embed_code = cleaned_data.get('video_embed_code')
        
        if resource_type == 'VIDEO':
            if not video_file and not video_embed_code:
                raise forms.ValidationError(
                    "Video resources require either a video file or embed code"
                )
            if video_file and video_embed_code:
                raise forms.ValidationError(
                    "Cannot have both video file and embed code"
                )
        return cleaned_data

class AnnouncementForm(forms.ModelForm):
    recipients = forms.ModelMultipleChoiceField(
        queryset=User.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=True
    )
    
    scheduled_at = forms.DateTimeField(
        required=False,
        widget=forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        input_formats=['%Y-%m-%dT%H:%M']
    )
    
    class Meta:
        model = Announcement
        fields = ['title', 'message', 'priority', 'recipients', 'send_email', 'scheduled_at']
        widgets = {
            'message': forms.Textarea(attrs={'rows': 5}),
        }
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user:
            self.fields['recipients'].queryset = User.objects.exclude(id=user.id)
        
        # Set current time as default for scheduled_at
        self.fields['scheduled_at'].initial = timezone.now().strftime('%Y-%m-%dT%H:%M')




        


