from django.apps import AppConfig


class TandikanWebsiteConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'tandikan_website'

    def ready(self):
        import tandikan_website.signals
