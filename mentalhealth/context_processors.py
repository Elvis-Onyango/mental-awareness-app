from .models import MoodEntry

def mood_choices(request):
    return {
        'MOOD_CHOICES': MoodEntry.MOOD_CHOICES
    }