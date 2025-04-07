from django.apps import AppConfig


class MentalhealthConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'mentalhealth'

    def ready(self):
        import mentalhealth.signals
