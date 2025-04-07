import re
from django import template

register = template.Library()

@register.filter
def youtube_id(url):
    """Extract YouTube ID from various URL formats"""
    if not url:
        return None  # Prevent errors if URL is None
    
    regex = r'(?:youtube\.com\/(?:[^\/]+\/.+\/|(?:v|e(?:mbed)?)\/|watch\?v=)|youtu\.be\/)([^"&?\/\s]{11})'
    match = re.search(regex, url)
    return match.group(1) if match else None
